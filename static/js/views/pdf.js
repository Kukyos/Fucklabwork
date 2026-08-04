// PDF view — page previews with the real text spans laid over them, editable
// in place. Each span keeps the font, size and colour the PDF actually uses,
// so what you type lands back on the page looking like what was already there.

import { api, downloadResponse } from "../api.js";

let toast = () => {};
let doc = null;          // { name, size, page_count, pages[], spans[] }
let file = null;         // the original File — re-sent on save, nothing is stored server-side
const edits = new Map(); // span id -> new text

const $ = (s, r = document) => r.querySelector(s);
const BASE_WIDTH = 860;  // page width in CSS px at 100% zoom
let zoom = 1;

export function initPdf(ctx) {
  toast = ctx.toast;

  $("#pdf-file").addEventListener("change", (e) => {
    const f = e.target.files[0];
    if (f) openFile(f);
    e.target.value = "";       // re-picking the same file must still fire change
  });

  $("#pdf-save").addEventListener("click", save);
  $("#pdf-reset").addEventListener("click", () => {
    if (!edits.size) return;
    edits.clear();
    render();
    syncPanel();
    toast("Edits discarded.");
  });
  $("#pdf-close").addEventListener("click", closeFile);

  $("#pdf-zoom-in").addEventListener("click", () => setZoom(zoom + 0.15));
  $("#pdf-zoom-out").addEventListener("click", () => setZoom(zoom - 0.15));

  document.addEventListener("autolab:open-pdf", (e) => openFile(e.detail.file));
}

function setZoom(z) {
  zoom = Math.min(2.5, Math.max(0.5, Math.round(z * 100) / 100));
  $("#pdf-zoom-label").textContent = `${Math.round(zoom * 100)}%`;
  render();
}

export async function openFile(f) {
  if (!f.name.toLowerCase().endsWith(".pdf")) {
    toast("That's not a PDF.", "err");
    return;
  }
  file = f;
  edits.clear();
  $("#pdf-empty").hidden = true;
  $("#pdf-loading").hidden = false;
  $("#pdf-pages").innerHTML = "";
  try {
    doc = await api.parsePdf(f);
  } catch (err) {
    $("#pdf-loading").hidden = true;
    $("#pdf-empty").hidden = false;
    toast(err.message, "err");
    return;
  }
  $("#pdf-loading").hidden = true;
  if (!doc.spans.length) {
    // A scanned PDF is pixels, not text — say so rather than showing an
    // empty page the user can click at forever.
    toast("No editable text found — this looks like a scan.", "err");
  }
  render();
  syncPanel();
}

function closeFile() {
  doc = null;
  file = null;
  edits.clear();
  $("#pdf-pages").innerHTML = "";
  $("#pdf-empty").hidden = false;
  $("#pdf-stage").hidden = true;
  syncPanel();
}

function fontStack(s) {
  if (s.mono) return "ui-monospace, SFMono-Regular, Menlo, monospace";
  return /times|serif|georgia|book/i.test(s.font) ? "Georgia, 'Times New Roman', serif"
                                                  : "Arial, Helvetica, sans-serif";
}

function render() {
  if (!doc) return;
  const host = $("#pdf-pages");
  host.innerHTML = "";
  $("#pdf-stage").hidden = false;

  const byPage = new Map();
  doc.spans.forEach((s) => {
    if (!byPage.has(s.page)) byPage.set(s.page, []);
    byPage.get(s.page).push(s);
  });

  doc.pages.forEach((page, i) => {
    const scale = (BASE_WIDTH * zoom) / page.width;
    const wrap = document.createElement("div");
    wrap.className = "pdf-page";
    wrap.style.width = `${page.width * scale}px`;
    wrap.style.height = `${page.height * scale}px`;
    wrap.innerHTML = `<img class="pdf-page-img" src="data:image/png;base64,${page.png}" alt="Page ${i + 1}" draggable="false">`;

    (byPage.get(i) || []).forEach((s) => wrap.appendChild(spanEl(s, scale)));

    const label = document.createElement("div");
    label.className = "pdf-page-no";
    label.textContent = `Page ${i + 1} of ${doc.page_count}`;

    const holder = document.createElement("div");
    holder.className = "pdf-page-holder";
    holder.append(wrap, label);
    host.appendChild(holder);
  });
}

function spanEl(s, scale) {
  const el = document.createElement("div");
  el.className = "pdf-span";
  el.dataset.id = s.id;
  el.style.left = `${s.bbox[0] * scale}px`;
  el.style.top = `${s.bbox[1] * scale}px`;
  el.style.width = `${(s.bbox[2] - s.bbox[0]) * scale}px`;
  el.style.height = `${(s.bbox[3] - s.bbox[1]) * scale}px`;
  el.style.fontSize = `${s.size * scale}px`;
  el.style.fontFamily = fontStack(s);
  el.style.fontWeight = s.bold ? "700" : "400";
  el.style.fontStyle = s.italic ? "italic" : "normal";
  el.title = `${s.font} · ${s.size}pt`;

  if (edits.has(s.id)) {
    // ponytail: the edited preview paints an opaque box over the old glyphs,
    // which assumes a light page. The download is rendered server-side and is
    // always correct; swap to a re-render round trip if dark pages show up.
    el.classList.add("is-edited");
    el.textContent = edits.get(s.id);
    el.style.color = s.color;
  }

  el.addEventListener("click", () => beginEdit(el, s));
  return el;
}

// contenteditable hands back U+00A0 wherever the user typed a space, and a
// pasted line can carry newlines a single-line span cannot draw. Both would
// end up baked into the PDF, so normalise before the text ever leaves here.
const clean = (t) =>
  t.replace(/\u00a0/g, " ").replace(/[\r\n\t]+/g, " ").replace(/\s+$/, "");

function beginEdit(el, s) {
  // Re-focus rather than bail out: if a span ever ends up editable without the
  // focus that goes with it, bailing would leave that line permanently dead.
  if (el.classList.contains("is-editing")) {
    el.focus({ preventScroll: true });
    return;
  }
  const before = edits.has(s.id) ? edits.get(s.id) : s.text;
  el.classList.add("is-editing", "is-edited");
  el.style.color = s.color;
  el.textContent = before;
  el.contentEditable = "plaintext-only";
  // preventScroll matters: focusing a span the user just clicked would
  // otherwise scroll the page under their cursor before they type a character.
  el.focus({ preventScroll: true });
  document.getSelection().selectAllChildren(el);

  // Only this span is touched on commit — a full re-render would rebuild every
  // page image and throw away the reader's scroll position on each edit.
  const finish = (commit) => {
    el.removeEventListener("keydown", onKey);
    el.contentEditable = "false";
    el.classList.remove("is-editing");
    const next = commit ? clean(el.textContent) : before;
    if (next === s.text) {
      edits.delete(s.id);
      el.classList.remove("is-edited");
      el.textContent = "";
      el.style.color = "";
    } else {
      edits.set(s.id, next);
      el.textContent = next;
    }
    syncPanel();
  };

  const onKey = (e) => {
    if (e.key === "Enter") { e.preventDefault(); el.blur(); }
    if (e.key === "Escape") { e.preventDefault(); el.textContent = before; el.blur(); }
  };
  el.addEventListener("blur", () => finish(true), { once: true });
  el.addEventListener("keydown", onKey);
}

function syncPanel() {
  const has = !!doc;
  $("#rp-pdf-empty").hidden = has;
  $("#rp-pdf-active").hidden = !has;
  if (!has) return;

  $("#pdf-name").textContent = doc.name;
  $("#pdf-meta").textContent =
    `${doc.page_count} page${doc.page_count === 1 ? "" : "s"} · ` +
    `${doc.spans.length} text span${doc.spans.length === 1 ? "" : "s"} · ` +
    `${(doc.size / 1024).toFixed(0)} KB`;

  const n = edits.size;
  $("#pdf-edit-count").textContent = n ? `${n} pending edit${n === 1 ? "" : "s"}` : "No edits yet";
  $("#pdf-save").disabled = !n;
  $("#pdf-reset").disabled = !n;

  const list = $("#pdf-edit-list");
  list.innerHTML = "";
  for (const [id, text] of edits) {
    const src = doc.spans.find((s) => s.id === id);
    const li = document.createElement("li");
    li.className = "pdf-edit-row";
    li.innerHTML = `<span class="pe-old"></span><span class="pe-arrow">→</span><span class="pe-new"></span>`;
    li.querySelector(".pe-old").textContent = src ? src.text.trim() : id;
    li.querySelector(".pe-new").textContent = text;
    list.appendChild(li);
  }
}

async function save() {
  if (!doc || !edits.size) return;
  const btn = $("#pdf-save");
  const status = $("#pdf-status");
  btn.disabled = true;
  status.textContent = "Applying…";
  status.className = "hint";
  try {
    const res = await api.savePdf(file, Object.fromEntries(edits));
    let report = [];
    try { report = JSON.parse(res.headers.get("X-Edit-Report") || "[]"); } catch {}
    await downloadResponse(res, file.name.replace(/\.pdf$/i, "_edited.pdf"));

    // Anything lossy gets said out loud — a swapped font or shrunk line is
    // exactly what someone would otherwise only notice after handing it in.
    // "original" reuses the page's own font resource, "embedded" a copy of it —
    // both keep the typeface. Only the fallback rungs are a real substitution.
    const faithful = new Set(["original", "embedded"]);
    const swapped = report.filter((r) => !faithful.has(r.font_source)).length;
    const shrunk = report.filter((r) => r.shrunk).length;
    const dropped = report.filter((r) => r.dropped);
    const notes = [`Applied ${report.length} edit${report.length === 1 ? "" : "s"}`];
    if (swapped) notes.push(`${swapped} used a substitute font`);
    if (shrunk) notes.push(`${shrunk} shrunk to fit`);
    status.textContent = notes.join(" · ") + ".";
    status.className = dropped.length ? "hint is-err" : "hint is-ok";
    if (dropped.length) {
      status.textContent += ` ${dropped.length} had characters no available font could draw.`;
    }
  } catch (err) {
    status.textContent = err.message;
    status.className = "hint is-err";
  } finally {
    btn.disabled = !edits.size;
  }
}
