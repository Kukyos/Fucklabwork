// Document organizer (desktop-only) — Generated folder + user-picked folders.
// Renders inside the Documents view when no file is open.

let state = null;
let toast = () => {};
let currentSource = "generated";
let currentFolder = null; // user-picked folder
let folderFiles = [];
let generatedFiles = [];

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

const DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";

export function initOrganizer(ctx) {
  state = ctx.state;
  toast = ctx.toast;

  $("#org-new").addEventListener("click", onNewBlank);
  $("#org-upload").addEventListener("click", () => $("#org-upload-input").click());
  $("#org-upload-input").addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (f) {
      document.dispatchEvent(new CustomEvent("autolab:open-doc", { detail: { file: f, path: null } }));
    }
    e.target.value = "";
  });
  $("#org-pick-folder").addEventListener("click", pickFolder);
  $$(".org-tab").forEach((tab) => {
    tab.addEventListener("click", () => setSource(tab.dataset.source));
  });

  document.addEventListener("autolab:desktop-ready", () => {
    // initial fetch once we know we're desktop
    refreshGenerated();
  });
  document.addEventListener("autolab:refresh-organizer", refreshAll);

  // Initialize folder tab label
  $("#org-folder-label").textContent = "Folder";
}

export function showOrganizer() {
  if (!state?.capabilities?.desktop) {
    $("#organizer").hidden = true;
    return false;
  }
  $("#docs-empty").hidden = true;
  $("#organizer").hidden = false;
  refreshGenerated();
  if (currentSource === "folder" && currentFolder) refreshFolder();
  return true;
}

export function hideOrganizer() {
  $("#organizer").hidden = true;
}

async function refreshGenerated() {
  if (!state?.capabilities?.desktop) return;
  try {
    const r = await fetchJson("/api/organizer/generated");
    generatedFiles = r.files || [];
  } catch {
    generatedFiles = [];
  }
  $("#org-gen-count").textContent = String(generatedFiles.length);
  if (currentSource === "generated") render();
}

async function refreshAll() {
  await refreshGenerated();
  if (currentFolder) await refreshFolder();
}

async function refreshFolder() {
  if (!currentFolder) return;
  try {
    const r = await fetchJson("/api/organizer/scan", { method: "POST", json: { folder: currentFolder } });
    folderFiles = r.files || [];
  } catch (e) {
    folderFiles = [];
    toast(e.message, "err");
  }
  $("#org-folder-count").hidden = false;
  $("#org-folder-count").textContent = String(folderFiles.length);
  if (currentSource === "folder") render();
}

async function pickFolder() {
  let folder = null;
  if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.pick_folder === "function") {
    try {
      folder = await window.pywebview.api.pick_folder();
    } catch {
      folder = null;
    }
  } else {
    folder = prompt("Folder path:");
  }
  if (!folder) return;
  currentFolder = folder;
  $("#org-folder-label").textContent = shortName(folder);
  setSource("folder");
  await refreshFolder();
}

function shortName(p) {
  if (!p) return "Folder";
  const parts = p.split(/[\\/]/).filter(Boolean);
  if (!parts.length) return p;
  return parts[parts.length - 1];
}

function setSource(src) {
  currentSource = src;
  $$(".org-tab").forEach((t) => t.classList.toggle("is-active", t.dataset.source === src));
  if (src === "folder" && currentFolder) {
    $("#org-current-folder").hidden = false;
    $("#org-current-folder").textContent = currentFolder;
  } else {
    $("#org-current-folder").hidden = true;
  }
  render();
}

function render() {
  const files = currentSource === "generated" ? generatedFiles : folderFiles;
  const list = $("#org-list");
  list.innerHTML = "";
  if (!files.length) {
    const msg = document.createElement("p");
    msg.className = "org-empty";
    if (currentSource === "folder" && !currentFolder) {
      msg.textContent = 'Click "Browse…" to pick a folder.';
    } else if (currentSource === "generated") {
      msg.textContent = "Nothing here yet. Generate a record from a template, or save one with the Save button.";
    } else {
      msg.textContent = "No .docx files in this folder.";
    }
    list.appendChild(msg);
    return;
  }
  for (const f of files) {
    list.appendChild(makeItem(f));
  }
}

function makeItem(f) {
  const el = document.createElement("div");
  el.className = "org-item";
  el.title = f.path;
  el.dataset.path = f.path;
  el.innerHTML = `
    <div class="org-item-icon"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h9l5 5v12.5a1.5 1.5 0 0 1-1.5 1.5h-12A1.5 1.5 0 0 1 5 20.5V4.5A1.5 1.5 0 0 1 6.5 3H6Zm9 1v4a1 1 0 0 0 1 1h4" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round"/></svg></div>
    <div class="org-item-meta">
      <div class="org-item-name"></div>
      <div class="org-item-sub"></div>
    </div>
    <div class="org-item-open">Open</div>
  `;
  el.querySelector(".org-item-name").textContent = f.name;
  el.querySelector(".org-item-sub").textContent = `${fmtSize(f.size)} · ${fmtTime(f.modified)}`;
  const open = () => openPath(f.path, f.name);
  el.addEventListener("dblclick", open);
  el.querySelector(".org-item-open").addEventListener("click", (e) => {
    e.stopPropagation();
    open();
  });
  return el;
}

function fmtSize(n) {
  if (typeof n !== "number") return "—";
  if (n < 1024) return `${n} B`;
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 / 1024).toFixed(2)} MB`;
}
function fmtTime(epochSec) {
  if (!epochSec) return "—";
  const ms = epochSec * 1000;
  const d = new Date(ms);
  const now = Date.now();
  const ago = (now - ms) / 1000;
  if (ago < 60) return "just now";
  if (ago < 3600) return `${Math.floor(ago / 60)}m ago`;
  if (ago < 86400) return `${Math.floor(ago / 3600)}h ago`;
  if (ago < 86400 * 7) return `${Math.floor(ago / 86400)}d ago`;
  return d.toLocaleDateString();
}

async function openPath(path, name) {
  try {
    const res = await fetch("/api/organizer/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path }),
    });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { detail = (await res.json()).detail || detail; } catch {}
      throw new Error(detail);
    }
    const blob = await res.blob();
    const file = new File([blob], name, { type: DOCX_MIME });
    document.dispatchEvent(new CustomEvent("autolab:open-doc", { detail: { file, path } }));
  } catch (e) {
    toast(e.message, "err");
  }
}

async function onNewBlank() {
  try {
    const res = await fetch("/api/organizer/new-blank", { method: "POST" });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { detail = (await res.json()).detail || detail; } catch {}
      throw new Error(detail);
    }
    const blob = await res.blob();
    const file = new File([blob], "untitled.docx", { type: DOCX_MIME });
    document.dispatchEvent(new CustomEvent("autolab:open-doc", { detail: { file, path: null } }));
  } catch (e) {
    toast(e.message, "err");
  }
}

async function fetchJson(url, opts = {}) {
  const init = { method: opts.method || "GET" };
  if (opts.json !== undefined) {
    init.headers = { "Content-Type": "application/json" };
    init.body = JSON.stringify(opts.json);
  }
  const res = await fetch(url, init);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}
