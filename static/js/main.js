// AutoLAB front-end shell — router, command palette, drag overlay, toast.

import { api } from "./api.js";
import { initDocuments } from "./views/documents.js";
import { initTemplates } from "./views/templates.js";
import { initTools } from "./views/tools.js";
import { initProfile } from "./views/profile.js";
import { initOrganizer, showOrganizer } from "./views/organizer.js";

const VIEWS = ["documents", "templates", "tools", "profile"];

export const state = {
  capabilities: { desktop: false, version: "?" },
  profile: null,
};

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

// ---------- theme ----------------------------------------------------
// Apply saved theme synchronously so we don't flash light on a dark-set machine.
try {
  if (localStorage.getItem("autolab-theme") === "dark") {
    document.body.classList.add("is-dark");
    const meta = document.querySelector('meta[name="color-scheme"]');
    if (meta) meta.setAttribute("content", "dark");
  }
} catch {}

function setTheme(dark) {
  const body = document.body;
  // Swap the theme atomically in a single task with transitions disabled, so
  // NO transition is ever started on the var()-based colour tokens. If a
  // transition were allowed to run on a theme flip it would briefly show the
  // wrong colour mid-fade (and in a backgrounded tab, where the frame clock is
  // paused, it would freeze at the wrong colour indefinitely). Disabling
  // transitions for the flip, then re-enabling after a forced style flush in
  // the SAME task, commits the new colours as the baseline with nothing
  // pending — verified via getAnimations() returning empty. Normal hover/focus
  // transitions are unaffected because the class is gone by the time we return.
  body.classList.add("theme-switching");
  body.classList.toggle("is-dark", dark);
  // color-scheme affects rendering, so it must change inside the same
  // transitions-disabled flush rather than dirtying styles afterwards.
  const meta = document.querySelector('meta[name="color-scheme"]');
  if (meta) meta.setAttribute("content", dark ? "dark" : "light");
  void body.offsetWidth;            // flush: commit new colours, no transition
  body.classList.remove("theme-switching");
  void body.offsetWidth;            // flush: baseline == current, nothing pending
  try { localStorage.setItem("autolab-theme", dark ? "dark" : "light"); } catch {}
  const tm = document.querySelector('meta[name="theme-color"]');
  if (tm) tm.setAttribute("content", dark ? "#0b0b0d" : "#ffffff");
}
$("#theme-toggle").addEventListener("click", () => {
  setTheme(!document.body.classList.contains("is-dark"));
});

// ---------- router ---------------------------------------------------
function showView(view) {
  if (!VIEWS.includes(view)) view = "documents";
  $$(".view").forEach((el) => {
    const on = el.dataset.view === view;
    el.classList.toggle("is-active", on);
    el.hidden = !on;
  });
  $$(".rp-view").forEach((el) => {
    const on = el.dataset.view === view;
    el.classList.toggle("is-active", on);
    el.hidden = !on;
  });
  $$(".nav-item").forEach((el) => {
    const on = el.dataset.view === view;
    el.classList.toggle("is-active", on);
    el.setAttribute("aria-selected", on ? "true" : "false");
  });
  $("#crumbs").innerHTML = `<span class="crumb">${cap(view)}</span>`;
  if (location.hash !== `#${view}`) history.replaceState(null, "", `#${view}`);
  document.body.dataset.view = view;
  closeDrawer();
  closeRightDrawer();
  closePalette();
}
const cap = (s) => s[0].toUpperCase() + s.slice(1);

$$(".nav-item").forEach((btn) => btn.addEventListener("click", () => showView(btn.dataset.view)));
window.addEventListener("hashchange", () => {
  const h = location.hash.replace("#", "");
  if (VIEWS.includes(h)) showView(h);
});

// ---------- keyboard -------------------------------------------------
document.addEventListener("keydown", (e) => {
  const t = e.target;
  const inField = t instanceof HTMLElement && (
    t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable
  );

  if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
    e.preventDefault();
    openPalette();
    return;
  }
  if (e.key === "Escape") {
    closePalette();
    closeDrawer();
    return;
  }
  if (!inField && (e.metaKey || e.ctrlKey)) {
    const n = parseInt(e.key, 10);
    if (n >= 1 && n <= 4) {
      e.preventDefault();
      showView(VIEWS[n - 1]);
    }
  }
});

// ---------- drawer ---------------------------------------------------
let drawerBackdrop = null;
function openDrawer() {
  $(".sidebar").classList.add("is-open");
  if (!drawerBackdrop) {
    drawerBackdrop = document.createElement("div");
    drawerBackdrop.className = "drawer-backdrop";
    drawerBackdrop.addEventListener("click", closeDrawer);
    document.body.appendChild(drawerBackdrop);
  }
  drawerBackdrop.classList.add("is-open");
}
function closeDrawer() {
  $(".sidebar").classList.remove("is-open");
  if (drawerBackdrop) drawerBackdrop.classList.remove("is-open");
}
$("#menu-btn").addEventListener("click", openDrawer);

let rightDrawerBackdrop = null;
function openRightDrawer() {
  $(".right-panel").classList.add("is-open");
  if (!rightDrawerBackdrop) {
    rightDrawerBackdrop = document.createElement("div");
    rightDrawerBackdrop.className = "drawer-backdrop";
    rightDrawerBackdrop.addEventListener("click", closeRightDrawer);
    document.body.appendChild(rightDrawerBackdrop);
  }
  rightDrawerBackdrop.classList.add("is-open");
}
function closeRightDrawer() {
  $(".right-panel").classList.remove("is-open");
  if (rightDrawerBackdrop) rightDrawerBackdrop.classList.remove("is-open");
}
$("#panel-btn").addEventListener("click", openRightDrawer);
export const openInspector = openRightDrawer;

// ---------- command palette -----------------------------------------
const palette = $("#palette");
const paletteInput = $("#palette-input");
const paletteList = $("#palette-list");
let paletteItems = [];
let paletteCursor = 0;

function commands() {
  const cmds = [
    { label: "Go to Documents", meta: "1", run: () => showView("documents") },
    { label: "Go to Templates", meta: "2", run: () => showView("templates") },
    { label: "Go to Tools",     meta: "3", run: () => showView("tools") },
    { label: "Go to Profile",   meta: "4", run: () => showView("profile") },
    { label: "Find & replace",  meta: "tool", run: () => showView("tools") },
    { label: "Generate a record from a template", meta: "tool", run: () => showView("templates") },
  ];
  if (state.capabilities.desktop) {
    cmds.push({ label: "Add a register number", meta: "profile", run: () => { showView("profile"); setTimeout(() => $("#urk-add-input").focus(), 50); }});
    cmds.push({ label: "Set Anthropic API key", meta: "profile", run: () => { showView("profile"); setTimeout(() => $("#api-key").focus(), 50); }});
  }
  return cmds;
}

function renderPalette() {
  const q = paletteInput.value.trim().toLowerCase();
  const all = commands();
  paletteItems = q ? all.filter((c) => c.label.toLowerCase().includes(q)) : all;
  paletteCursor = 0;
  if (!paletteItems.length) {
    paletteList.innerHTML = '<li class="palette-empty">No matches</li>';
    return;
  }
  paletteList.innerHTML = "";
  paletteItems.forEach((c, i) => {
    const li = document.createElement("li");
    li.className = "palette-item" + (i === paletteCursor ? " is-cursor" : "");
    li.innerHTML = `<span>${c.label}</span><span class="pl-meta">${c.meta}</span>`;
    li.addEventListener("click", () => { c.run(); });
    paletteList.appendChild(li);
  });
}
function refreshCursor() {
  $$(".palette-item", paletteList).forEach((el, i) => el.classList.toggle("is-cursor", i === paletteCursor));
}
function openPalette() {
  palette.hidden = false;
  paletteInput.value = "";
  paletteInput.focus();
  renderPalette();
}
function closePalette() {
  palette.hidden = true;
}

$$(".palette [data-palette-close]").forEach((el) => el.addEventListener("click", closePalette));
$("#cmd-trigger").addEventListener("click", openPalette);
paletteInput.addEventListener("input", renderPalette);
paletteInput.addEventListener("keydown", (e) => {
  if (e.key === "ArrowDown") {
    e.preventDefault();
    paletteCursor = Math.min(paletteCursor + 1, paletteItems.length - 1);
    refreshCursor();
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    paletteCursor = Math.max(paletteCursor - 1, 0);
    refreshCursor();
  } else if (e.key === "Enter") {
    e.preventDefault();
    const c = paletteItems[paletteCursor];
    if (c) c.run();
  }
});

// ---------- toast ----------------------------------------------------
let toastTimer = 0;
export function toast(msg, kind = "ok") {
  const el = $("#toast");
  el.textContent = msg;
  el.className = "toast" + (kind === "err" ? " is-err" : "");
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 3200);
}

// ---------- global file drop ---------------------------------------
const dropOverlay = $("#global-drop");
let dragDepth = 0;
const isFileDrag = (e) =>
  e.dataTransfer && Array.from(e.dataTransfer.types || []).includes("Files");

window.addEventListener("dragenter", (e) => {
  if (!isFileDrag(e)) return;
  dragDepth++;
  dropOverlay.hidden = false;
});
window.addEventListener("dragover", (e) => {
  if (!isFileDrag(e)) return;
  e.preventDefault();
});
window.addEventListener("dragleave", () => {
  dragDepth = Math.max(0, dragDepth - 1);
  if (dragDepth === 0) dropOverlay.hidden = true;
});
window.addEventListener("drop", (e) => {
  if (!isFileDrag(e)) return;
  e.preventDefault();
  dragDepth = 0;
  dropOverlay.hidden = true;
  const f = e.dataTransfer.files[0];
  if (!f) return;
  if (!f.name.toLowerCase().endsWith(".docx")) {
    toast("Only .docx files for now.", "err");
    return;
  }
  showView("documents");
  document.dispatchEvent(new CustomEvent("autolab:open-file", { detail: { file: f } }));
});

// ---------- init views ----------------------------------------------
initDocuments({ state, toast });
initTemplates({ state, toast });
initTools({ state, toast });
initProfile({ state, toast });
initOrganizer({ state, toast });
// expose for documents.js to call on close
window.__autolab_show_organizer = showOrganizer;

// ---------- boot -----------------------------------------------------
(async () => {
  try { state.capabilities = await api.capabilities(); } catch {}

  if (state.capabilities.desktop) {
    document.body.classList.add("is-desktop");
    const pill = $("#mode-pill");
    pill.textContent = "Desktop";
    pill.classList.add("is-desktop");
    if (state.capabilities.data_dir) {
      $("#profile-path").textContent = `${state.capabilities.data_dir}\\profile.json`;
    }
    document.dispatchEvent(new Event("autolab:desktop-ready"));
    // Show organizer in place of the docs-empty card when on desktop.
    showOrganizer();
  }

  const h = location.hash.replace("#", "");
  if (VIEWS.includes(h)) showView(h);
  else showView("documents");
})();
