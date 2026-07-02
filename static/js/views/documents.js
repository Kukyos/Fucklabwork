// Documents view — block-level editor + right-panel inspector.

import { api, downloadResponse } from "../api.js";

let state = null;
let toast = () => {};

let currentFile = null;
let currentFilePath = null;  // set when opened from organizer; null for uploads
let currentBlocks = [];
let edits = {};
const busyIds = new Set();
let focusedBlockId = null;
let viewMode = "edit";  // "edit" | "preview"

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

export function initDocuments(ctx) {
  state = ctx.state;
  toast = ctx.toast;

  $("#docs-pick").addEventListener("click", () => $("#docs-file").click());
  $("#docs-file").addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (f) openFile(f);
  });

  document.addEventListener("autolab:open-file", (e) => openFile(e.detail.file));

  const empty = $("#docs-empty");
  ["dragenter", "dragover"].forEach((ev) => empty.addEventListener(ev, (e) => {
    e.preventDefault();
    empty.classList.add("is-dragging");
  }));
  empty.addEventListener("dragleave", () => empty.classList.remove("is-dragging"));
  empty.addEventListener("drop", (e) => {
    e.preventDefault();
    empty.classList.remove("is-dragging");
    const f = e.dataTransfer?.files?.[0];
    if (f) openFile(f);
  });

  // Right panel — global actions
  $("#rp-save").addEventListener("click", saveDoc);
  $("#rp-close").addEventListener("click", closeDoc);
  $("#rp-ai-all").addEventListener("click", bulkAi);

  // Right panel — add question
  $("#addq-form").addEventListener("submit", onAddQuestion);

  // Right panel — solve question (run + screenshots + insert)
  $("#solve-form").addEventListener("submit", onSolveQuestion);
  $("#sq-generate").addEventListener("click", onGenerateCode);
  $("#sq-mode").addEventListener("change", syncSolveMode);

  // Right panel — save to disk (desktop)
  const saveasForm = $("#saveas-form");
  if (saveasForm) saveasForm.addEventListener("submit", onSaveAs);

  // Right panel — selected block actions (operate on focusedBlockId)
  $("#rp-block-ai").addEventListener("click", () => focusedBlockId && rewriteById(focusedBlockId));
  $("#rp-block-reset").addEventListener("click", () => focusedBlockId && resetById(focusedBlockId));

  // Right panel — mode switch
  $$("#doc-mode-switch .mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => setViewMode(btn.dataset.mode));
  });

  // External "open" hook — used by templates view after generating a doc
  document.addEventListener("autolab:open-doc", (e) => {
    const { file, path } = e.detail || {};
    if (file) openFile(file, path || null);
  });
}

function setViewMode(mode) {
  if (mode !== "edit" && mode !== "preview") return;
  viewMode = mode;
  const page = $("#doc-blocks");
  page.classList.toggle("is-preview", mode === "preview");
  // Disable contenteditable in preview so accidental clicks don't focus.
  $$(".blk-text", page).forEach((el) => {
    el.contentEditable = mode === "edit" ? "true" : "false";
  });
  $$("#doc-mode-switch .mode-btn").forEach((btn) => {
    const on = btn.dataset.mode === mode;
    btn.classList.toggle("is-active", on);
    btn.setAttribute("aria-selected", on ? "true" : "false");
  });
}

async function openFile(file, path = null) {
  if (!file.name.toLowerCase().endsWith(".docx")) {
    toast("Pick a .docx file.", "err");
    return;
  }
  let parsed;
  try {
    parsed = await api.parseDoc(file);
  } catch (e) {
    toast(e.message, "err");
    return;
  }
  currentFile = file;
  currentFilePath = path;
  currentBlocks = parsed.blocks;
  edits = {};
  focusedBlockId = null;
  viewMode = "edit";          // freshly opened docs always start in edit mode
  renderEditor(parsed);       // re-applies the active view mode internally
  setInspector("active");
}

function setInspector(stateName) {
  // stateName: "empty" | "active"
  $("#rp-docs-empty").hidden = stateName !== "empty";
  $("#rp-docs-active").hidden = stateName !== "active";
  $("#rp-docs-addq").hidden = stateName !== "active";
  $("#rp-docs-solve").hidden = stateName !== "active" || !state?.capabilities?.solve;
  if (stateName === "active" && !$("#sq-urk").value) {
    $("#sq-urk").value = state?.profile?.default_urk || "";
  }
  const saveasSec = $("#rp-docs-saveas");
  if (saveasSec) saveasSec.hidden = stateName !== "active" || !state?.capabilities?.desktop;
  if (stateName !== "active") $("#rp-docs-block").hidden = true;
}

function renderEditor(parsed) {
  $("#docs-empty").hidden = true;
  const org = $("#organizer");
  if (org) org.hidden = true;
  $("#docs-editor").hidden = false;
  $("#rp-doc-head-name").textContent = parsed.name;
  // Prefill the save-as filename + "current location" option visibility
  const sn = $("#saveas-name");
  if (sn) sn.value = parsed.name;
  const curOpt = $("#saveas-current-opt");
  if (curOpt) curOpt.hidden = !currentFilePath;
  const sf = $("#saveas-folder");
  if (sf) sf.value = currentFilePath ? "current" : "generated";
  refreshStats();
  const page = $("#doc-blocks");
  page.innerHTML = "";

  const sectionLabels = { paragraph: "Body", cell: "Table cells", header: "Header", footer: "Footer" };
  let lastKind = null;
  for (const b of parsed.blocks) {
    if (b.kind !== lastKind) {
      const sep = document.createElement("div");
      sep.className = "blk-section";
      sep.textContent = sectionLabels[b.kind] || b.kind;
      page.appendChild(sep);
      lastKind = b.kind;
    }
    page.appendChild(renderBlock(b));
  }

  // Blank/new documents have no editable text blocks (empty paragraphs are
  // skipped on parse). Show a gentle hint instead of a confusing empty page.
  if (!parsed.blocks.length) {
    const hint = document.createElement("div");
    hint.className = "doc-empty-hint";
    hint.textContent = "This document has no text yet. Use “Add a question” in the panel to insert content.";
    page.appendChild(hint);
  }

  // Keep contentEditable + preview styling consistent with the active mode.
  setViewMode(viewMode);
}

function renderBlock(b) {
  const el = document.createElement("div");
  el.className = "blk";
  el.dataset.id = b.id;
  el.dataset.kind = b.kind;
  el.dataset.style = b.style;
  el.dataset.originalText = b.text;
  el.dataset.words = String(b.words);
  el.dataset.chars = String(b.chars);

  const text = document.createElement("div");
  text.className = "blk-text";
  text.textContent = b.text;
  text.contentEditable = "true";
  text.spellcheck = false;

  text.addEventListener("focus", () => {
    el.classList.add("is-editing");
    focusedBlockId = b.id;
    updateBlockInspector(b, text);
  });
  text.addEventListener("input", () => updateBlockInspector(b, text));
  text.addEventListener("blur", () => {
    el.classList.remove("is-editing");
    const newText = text.textContent;
    if (newText !== el.dataset.originalText) {
      edits[b.id] = newText;
      el.classList.add("is-dirty");
    } else {
      delete edits[b.id];
      el.classList.remove("is-dirty");
    }
    refreshStats();
  });
  text.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      text.blur();
    }
    if (e.key === "Escape") {
      text.textContent = el.dataset.originalText;
      delete edits[b.id];
      el.classList.remove("is-dirty");
      text.blur();
    }
  });
  el.appendChild(text);

  const loc = document.createElement("span");
  loc.className = "blk-loc";
  loc.textContent = b.loc;
  el.appendChild(loc);

  const actions = document.createElement("div");
  actions.className = "blk-actions";

  const aiBtn = document.createElement("button");
  aiBtn.className = "blk-act is-ai";
  aiBtn.textContent = "Rewrite";
  aiBtn.title = "Rewrite with AI · keeps word count";
  aiBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    rewriteBlock(el, b, text);
  });

  const resetBtn = document.createElement("button");
  resetBtn.className = "blk-act";
  resetBtn.textContent = "Reset";
  resetBtn.title = "Restore original";
  resetBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    text.textContent = el.dataset.originalText;
    delete edits[b.id];
    el.classList.remove("is-dirty");
    refreshStats();
    if (focusedBlockId === b.id) updateBlockInspector(b, text);
  });

  actions.appendChild(aiBtn);
  actions.appendChild(resetBtn);
  el.appendChild(actions);
  return el;
}

function updateBlockInspector(b, textEl) {
  $("#rp-docs-block").hidden = false;
  $("#rp-block-id").textContent = b.id;
  $("#rp-bi-loc").textContent = b.loc;
  $("#rp-bi-kind").textContent = b.kind;
  $("#rp-bi-style").textContent = b.style;
  const live = textEl.textContent;
  $("#rp-bi-words").textContent = live.split(/\s+/).filter(Boolean).length;
  $("#rp-bi-chars").textContent = live.length;
}

function blockEl(id) {
  return $(`.blk[data-id="${cssEscape(id)}"]`);
}
function cssEscape(s) {
  return s.replace(/([!"#$%&'()*+,./:;<=>?@[\]^`{|}~])/g, "\\$1");
}

async function rewriteById(id) {
  const el = blockEl(id);
  if (!el) return;
  const b = currentBlocks.find((x) => x.id === id);
  const textEl = el.querySelector(".blk-text");
  await rewriteBlock(el, b, textEl);
}
function resetById(id) {
  const el = blockEl(id);
  if (!el) return;
  const t = el.querySelector(".blk-text");
  t.textContent = el.dataset.originalText;
  delete edits[id];
  el.classList.remove("is-dirty");
  refreshStats();
  const b = currentBlocks.find((x) => x.id === id);
  if (b) updateBlockInspector(b, t);
}

async function rewriteBlock(el, b, textEl) {
  if (busyIds.has(b.id)) return;
  if (!state.capabilities.desktop) {
    toast("AI rewrite needs the desktop app.", "err");
    return;
  }
  const aiBtns = [el.querySelector(".blk-act.is-ai"), $("#rp-block-ai")].filter(Boolean);
  busyIds.add(b.id);
  aiBtns.forEach((btn) => { btn.disabled = true; btn.dataset.orig = btn.textContent; btn.textContent = "…"; });
  try {
    const t = textEl.textContent;
    const r = await api.aiRewrite(t, "", b.words);
    textEl.textContent = r.text;
    edits[b.id] = r.text;
    el.classList.add("is-dirty");
    if (focusedBlockId === b.id) updateBlockInspector(b, textEl);
    toast(`Rewrote · ${r.words_in} → ${r.words_out} words`);
  } catch (e) {
    toast(e.message, "err");
  } finally {
    busyIds.delete(b.id);
    aiBtns.forEach((btn) => { btn.disabled = false; btn.textContent = btn.dataset.orig || "Rewrite"; });
    refreshStats();
  }
}

async function bulkAi() {
  if (!state.capabilities.desktop) {
    toast("AI rewrite needs the desktop app.", "err");
    return;
  }
  if (!confirm(`Rewrite every block with AI? (${currentBlocks.length} blocks. Will hit the API once per block.)`)) return;
  const blocks = $$(".blk", $("#doc-blocks"));
  for (const el of blocks) {
    const b = currentBlocks.find((x) => x.id === el.dataset.id);
    if (!b) continue;
    const t = el.querySelector(".blk-text");
    await rewriteBlock(el, b, t);
  }
  toast("Bulk rewrite complete");
}

async function onAddQuestion(e) {
  e.preventDefault();
  if (!currentFile) {
    toast("Open a document first.", "err");
    return;
  }
  const num = $("#aq-num").value.trim();
  const title = $("#aq-title").value.trim();
  const desc = $("#aq-desc").value.trim();
  if (!title) {
    setAddqStatus("Title is required.", "err");
    return;
  }
  if (Object.keys(edits).length > 0) {
    const cont = confirm("You have unsaved edits. Adding a question will reload the document and discard them. Continue?");
    if (!cont) return;
  }

  setAddqStatus("Appending…", "");
  const fd = new FormData();
  fd.append("file", currentFile);
  fd.append("number", num);
  fd.append("title", title);
  fd.append("description", desc);

  let blob;
  try {
    const res = await fetch("/api/document/add-question", { method: "POST", body: fd });
    if (!res.ok) {
      let d = `HTTP ${res.status}`;
      try { d = (await res.json()).detail || d; } catch {}
      throw new Error(d);
    }
    blob = await res.blob();
  } catch (err) {
    setAddqStatus(err.message, "err");
    return;
  }

  const newFile = new File([blob], currentFile.name, {
    type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  });

  let parsed;
  try { parsed = await api.parseDoc(newFile); }
  catch (err) { setAddqStatus(err.message, "err"); return; }

  currentFile = newFile;
  currentBlocks = parsed.blocks;
  edits = {};
  focusedBlockId = null;
  renderEditor(parsed);
  setInspector("active");

  // Reset the form
  $("#aq-num").value = "";
  $("#aq-title").value = "";
  $("#aq-desc").value = "";
  setAddqStatus(`Appended. ${parsed.block_count} blocks now.`, "ok");
  toast("Question added");

  // Scroll to the bottom of the doc so the new question is visible
  const page = $("#doc-blocks");
  page.scrollIntoView({ block: "end" });
  const blocks = $$(".blk", page);
  if (blocks.length) blocks[blocks.length - 1].scrollIntoView({ behavior: "smooth", block: "center" });
}

function setAddqStatus(msg, kind) {
  const s = $("#aq-status");
  s.textContent = msg;
  s.className = "hint" + (kind ? ` is-${kind}` : "");
}

// --- Solve question: AI codegen + run + screenshots + insert ---------------

function syncSolveMode() {
  const pair = $("#sq-mode").value === "pair";
  $("#sq-code-wrap").hidden = pair;
  $$(".sq-pair").forEach((el) => { el.hidden = !pair; });
}

function setSolveStatus(msg, kind) {
  const s = $("#sq-status");
  s.textContent = msg;
  s.className = "hint" + (kind ? ` is-${kind}` : "");
}

async function onGenerateCode() {
  if (!state.capabilities.desktop) {
    toast("AI generation needs the desktop app.", "err");
    return;
  }
  const question = $("#sq-question").value.trim();
  if (!question) {
    setSolveStatus("Write the question first.", "err");
    return;
  }
  const btn = $("#sq-generate");
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = "Generating…";
  setSolveStatus("Asking Gemini…", "");
  try {
    const r = await api.generateCode({
      project_title: $("#sq-title").value.trim()
        || state.profile?.preferences?.default_course_title || "",
      question,
      language: $("#sq-lang").value,
      mode: $("#sq-mode").value === "pair" ? "pair" : "auto",
    });
    if (r.mode === "pair") {
      $("#sq-mode").value = "pair";
      $("#sq-server").value = r.server_code || "";
      $("#sq-client").value = r.client_code || "";
    } else {
      $("#sq-mode").value = "single";
      $("#sq-code").value = r.code || "";
    }
    syncSolveMode();
    setSolveStatus("Code generated — review it, then Run & insert.", "ok");
  } catch (e) {
    setSolveStatus(e.message, "err");
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

async function onSolveQuestion(e) {
  e.preventDefault();
  if (!currentFile) {
    toast("Open a document first.", "err");
    return;
  }
  const title = $("#sq-title").value.trim();
  if (!title) {
    setSolveStatus("Title is required.", "err");
    return;
  }
  const mode = $("#sq-mode").value;
  if (mode === "single" && !$("#sq-code").value.trim()) {
    setSolveStatus("Paste or generate code first.", "err");
    return;
  }
  if (mode === "pair" && (!$("#sq-server").value.trim() || !$("#sq-client").value.trim())) {
    setSolveStatus("Pair mode needs both server and client code.", "err");
    return;
  }
  if (Object.keys(edits).length > 0) {
    const cont = confirm("You have unsaved edits. Solving will reload the document and discard them. Continue?");
    if (!cont) return;
  }

  const btn = $("#sq-run");
  btn.disabled = true;
  setSolveStatus("Running the program…", "");
  const fd = new FormData();
  fd.append("file", currentFile);
  fd.append("number", $("#sq-num").value.trim());
  fd.append("title", title);
  fd.append("description", $("#sq-question").value.trim());
  fd.append("language", $("#sq-lang").value);
  fd.append("mode", mode);
  fd.append("code", mode === "single" ? $("#sq-code").value : "");
  fd.append("server_code", mode === "pair" ? $("#sq-server").value : "");
  fd.append("client_code", mode === "pair" ? $("#sq-client").value : "");
  fd.append("urk", $("#sq-urk").value.trim());
  fd.append("urk_mode", $("#sq-urkmode").value);
  fd.append("include_code_shot", $("#sq-codeshot").checked ? "1" : "0");

  try {
    const res = await fetch("/api/document/add-solved-question", { method: "POST", body: fd });
    if (!res.ok) {
      let d = `HTTP ${res.status}`;
      try { d = (await res.json()).detail || d; } catch {}
      throw new Error(d);
    }
    if (res.headers.get("X-Run-Ok") === "0") {
      // ponytail: discard the returned docx — never paste a failed run into the record
      throw new Error("The program failed to run — document untouched. Fix the code (or regenerate) and retry.");
    }
    const blob = await res.blob();
    const newFile = new File([blob], currentFile.name, {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const parsed = await api.parseDoc(newFile);
    currentFile = newFile;
    currentBlocks = parsed.blocks;
    edits = {};
    focusedBlockId = null;
    renderEditor(parsed);
    setInspector("active");
    const shots = res.headers.get("X-Images-Added") || "?";
    setSolveStatus(`Inserted with ${shots} screenshot${shots === "1" ? "" : "s"}.`, "ok");
    toast("Question solved & inserted");
    const blocks = $$(".blk", $("#doc-blocks"));
    if (blocks.length) blocks[blocks.length - 1].scrollIntoView({ behavior: "smooth", block: "center" });
  } catch (err) {
    setSolveStatus(err.message, "err");
  } finally {
    btn.disabled = false;
  }
}

function closeDoc() {
  if (Object.keys(edits).length && !confirm("Discard unsaved edits?")) return;
  currentFile = null;
  currentFilePath = null;
  currentBlocks = [];
  edits = {};
  focusedBlockId = null;
  $("#docs-editor").hidden = true;
  $("#doc-blocks").innerHTML = "";
  $("#docs-file").value = "";
  setInspector("empty");
  // Show organizer if available, else empty state
  if (state?.capabilities?.desktop && typeof window.__autolab_show_organizer === "function") {
    window.__autolab_show_organizer();
  } else {
    $("#docs-empty").hidden = false;
  }
}

async function saveDoc() {
  if (!currentFile) {
    toast("Open a document first.", "err");
    return;
  }
  const btn = $("#rp-save");
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = "Saving…";
  try {
    const res = await api.saveDoc(currentFile, edits);
    await downloadResponse(res, currentFile.name.replace(/\.docx$/i, "_edited.docx"));
    const applied = res.headers.get("X-Edits-Applied") || "0";
    toast(`Saved · ${applied} edit${applied === "1" ? "" : "s"} applied`);
  } catch (e) {
    toast(e.message, "err");
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

function refreshStats() {
  const dirty = Object.keys(edits).length;
  const total = currentBlocks.length;
  $("#rp-doc-stats").textContent = `${total} blocks · ${dirty} changed`;
}

async function onSaveAs(e) {
  e.preventDefault();
  if (!currentFile) {
    toast("Open a document first.", "err");
    return;
  }
  const name = $("#saveas-name").value.trim();
  const folder = $("#saveas-folder").value;
  const status = $("#saveas-status");
  status.textContent = "";
  status.className = "hint";
  if (!name) {
    status.textContent = "Filename required.";
    status.className = "hint is-err";
    return;
  }
  status.textContent = "Saving…";
  const fd = new FormData();
  fd.append("file", currentFile);
  fd.append("edits", JSON.stringify(edits));
  fd.append("name", name);
  fd.append("folder", folder);
  if (currentFilePath) fd.append("current_path", currentFilePath);
  try {
    const res = await fetch("/api/organizer/save", { method: "POST", body: fd });
    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try { detail = (await res.json()).detail || detail; } catch {}
      throw new Error(detail);
    }
    const r = await res.json();
    currentFilePath = r.path;
    // After save, the on-disk file matches what we just sent (with edits baked in).
    // Update currentFile to the post-edits bytes so subsequent edits diff from saved.
    if (Object.keys(edits).length) {
      // Re-fetch to keep currentFile consistent with disk
      try {
        const re = await fetch("/api/organizer/open", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ path: r.path }),
        });
        if (re.ok) {
          const blob = await re.blob();
          currentFile = new File([blob], r.name, {
            type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
          });
          edits = {};
          // Re-parse so block originalText reflects the saved state
          const parsed = await api.parseDoc(currentFile);
          currentBlocks = parsed.blocks;
          renderEditor(parsed);
        }
      } catch {}
    }
    const parts = (r.path || "").split(/[\\/]/).filter(Boolean);
    const parentName = parts.length >= 2 ? parts[parts.length - 2] : "folder";
    const destLabel = folder === "generated" ? "Generated" : parentName;
    status.textContent = `Saved to ${destLabel}`;
    status.title = r.path || "";
    status.className = "hint is-ok";
    toast(`Saved · ${r.name}`);
    document.dispatchEvent(new Event("autolab:refresh-organizer"));
    refreshStats();
  } catch (err) {
    status.textContent = err.message;
    status.className = "hint is-err";
  }
}
