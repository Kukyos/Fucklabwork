// Templates view — gallery in canvas, fill/questionnaire forms in the right panel.

import { api } from "../api.js";
import { billing } from "../billing.js";

let toast = () => {};
let state = null;
let templates = [];
let activeTpl = null;

const DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
const $ = (s, r = document) => r.querySelector(s);

export function initTemplates(ctx) {
  state = ctx.state;
  toast = ctx.toast;

  loadTemplates();
  $("#tpl-form").addEventListener("submit", onSubmit);
  initAiRecord();
}

async function loadTemplates() {
  try {
    const r = await api.listTemplates();
    templates = r.templates;
  } catch {
    templates = [];
  }
  renderGrid();
}

function renderGrid() {
  const grid = $("#tpl-grid");
  grid.innerHTML = "";
  grid.appendChild(aiCard());
  for (const t of templates) {
    const card = document.createElement("article");
    card.className = "tpl-card";
    card.innerHTML = `
      <div class="tpl-preview">
        <div class="tpl-page">
          <div class="row"><div class="box"></div><div class="box"></div></div>
          <div class="row"><div class="box"></div><div class="box"></div></div>
          <div class="h"></div><div class="line mid"></div><div class="line"></div>
          <div class="h"></div><div class="line"></div><div class="line short"></div>
          <div class="h"></div><div class="line mid"></div>
        </div>
      </div>
      <div class="tpl-meta">
        <h3>${escapeHTML(t.name)}</h3>
        <p>${escapeHTML(t.summary)}</p>
      </div>
    `;
    card.addEventListener("click", () => openFill(t, card));
    grid.appendChild(card);
  }
}

function aiCard() {
  const card = document.createElement("article");
  card.className = "tpl-card tpl-card-ai";
  card.innerHTML = `
    <div class="tpl-preview">
      <div class="tpl-page">
        <div class="row"><div class="box"></div><div class="box"></div></div>
        <div class="h"></div><div class="line mid"></div><div class="line"></div>
        <div class="shot"></div>
        <div class="h"></div><div class="line short"></div>
        <div class="shot"></div>
      </div>
    </div>
    <div class="tpl-meta">
      <h3>✦ Full record (AI)</h3>
      <p>Answer a few questions — AI writes the code, renders the terminal screenshots, and builds the whole record for you.</p>
    </div>
  `;
  card.addEventListener("click", () => openAi(card));
  return card;
}

function selectCard(card) {
  document.querySelectorAll(".tpl-card").forEach((c) => c.classList.toggle("is-active", c === card));
  $("#rp-tpl-empty").hidden = true;
}

function openFill(t, card) {
  activeTpl = t;
  selectCard(card);
  $("#rp-tpl-ai").hidden = true;
  $("#rp-tpl-fill").hidden = false;
  $("#rp-tpl-title").textContent = `Fill — ${t.name}`;
  $("#tpl-status").textContent = "";
  $("#tpl-status").className = "hint";
  if (state.profile) {
    if (!$("#tpl-reg").value) $("#tpl-reg").value = state.profile.default_urk || "";
    if (!$("#tpl-course").value) $("#tpl-course").value = state.profile.preferences?.default_course_title || "";
  }
}

function openAi(card) {
  activeTpl = null;
  selectCard(card);
  $("#rp-tpl-fill").hidden = true;
  $("#rp-tpl-ai").hidden = false;
  if (state.profile) {
    if (!$("#air-reg").value) $("#air-reg").value = state.profile.default_urk || "";
    if (!$("#air-course").value) $("#air-course").value = state.profile.preferences?.default_course_title || "";
  }
  updateCost();
}

async function onSubmit(e) {
  e.preventDefault();
  if (!activeTpl) return;
  const fd = new FormData(e.target);
  const payload = {
    template: activeTpl.id,
    course_title: fd.get("course_title") || "",
    register_number: fd.get("register_number") || "",
    ex_no: fd.get("ex_no") || "",
    title: fd.get("title") || "",
    date: fd.get("date") || "",
  };
  const status = $("#tpl-status");
  status.textContent = "Generating…";
  status.className = "hint";
  try {
    const res = await api.fillTemplate(payload);
    const cd = res.headers.get("Content-Disposition") || "";
    const m = cd.match(/filename="([^"]+)"/);
    const name = (m ? m[1] : (payload.title || "record")).replace(/[/\\:*?"<>|]/g, "_") || "record.docx";
    const finalName = name.toLowerCase().endsWith(".docx") ? name : `${name}.docx`;
    // Desktop builds persist the record to the Generated folder and return its
    // on-disk path; web builds return no path (open-in-editor only).
    const savedPath = res.headers.get("X-File-Path") || null;
    const blob = await res.blob();
    const file = new File([blob], finalName, { type: DOCX_MIME });

    // Hand the freshly-generated doc to the Documents view and switch.
    document.dispatchEvent(new CustomEvent("autolab:open-doc", { detail: { file, path: savedPath } }));
    if (location.hash !== "#documents") location.hash = "#documents";
    if (savedPath) document.dispatchEvent(new Event("autolab:refresh-organizer"));

    status.textContent = savedPath ? "Saved to Generated · opened in editor." : "Opened in editor.";
    status.className = "hint is-ok";
    toast(savedPath ? "Generated · saved to Generated" : "Generated · opened in editor");
  } catch (err) {
    status.textContent = err.message;
    status.className = "hint is-err";
  }
}

// --- AI full record ---------------------------------------------------

function initAiRecord() {
  for (const id of ["air-font", "air-size", "air-margin", "air-pagenums", "air-header"]) {
    $("#" + id).addEventListener("change", updatePreview);
  }
  $("#air-questions").addEventListener("input", updateCost);
  $("#air-key").addEventListener("input", updateCost);
  $("#ai-record-form").addEventListener("submit", onAiSubmit);
  updatePreview();
}

function questionLines() {
  return $("#air-questions").value.split("\n").map((s) => s.trim()).filter(Boolean);
}

function updateCost() {
  const n = questionLines().length;
  const cost = $("#air-cost");
  const price = billing.config?.prices?.gen_question || 5;
  $("#ai-price-tag").textContent = `₹${price} / question`;
  if (!n) { cost.textContent = ""; return; }
  if ($("#air-key").value.trim()) {
    cost.textContent = `${n} question${n === 1 ? "" : "s"} — free with your own key.`;
  } else if (billing.config?.enabled && !state.capabilities.desktop) {
    cost.textContent = `${n} question${n === 1 ? "" : "s"} × ₹${price} = ₹${n * price} from credits.`;
  } else {
    cost.textContent = `${n} question${n === 1 ? "" : "s"}.`;
  }
}

function updatePreview() {
  const pv = $("#ai-preview");
  pv.classList.toggle("is-serif", $("#air-font").value === "Times New Roman");
  pv.classList.toggle("is-large", $("#air-size").value === "12");
  pv.classList.toggle("is-narrow", $("#air-margin").value === "narrow");
  pv.classList.toggle("no-pagenums", !$("#air-pagenums").checked);
  pv.classList.toggle("no-header", !$("#air-header").checked);
}

async function onAiSubmit(e) {
  e.preventDefault();
  const status = $("#air-status");
  const btn = $("#air-run");
  status.className = "hint";
  const questions = questionLines();
  if (!questions.length) {
    status.textContent = "Add at least one question.";
    status.className = "hint is-err";
    return;
  }
  if (questions.length > 15) {
    status.textContent = "Max 15 questions per record.";
    status.className = "hint is-err";
    return;
  }

  btn.disabled = true;
  try {
    status.textContent = "Building the template…";
    const res = await api.fillTemplate({
      template: "neutral",
      course_title: $("#air-course").value,
      register_number: $("#air-reg").value,
      ex_no: $("#air-exno").value,
      title: $("#air-title").value,
      date: $("#air-date").value,
      font: $("#air-font").value,
      body_pt: parseInt($("#air-size").value, 10),
      margin: $("#air-margin").value,
      page_numbers: $("#air-pagenums").checked,
      header_line: $("#air-header").checked,
    });
    let blob = await res.blob();

    for (let i = 0; i < questions.length; i++) {
      status.textContent = `Question ${i + 1} of ${questions.length}… (AI writes and renders, ~20s each)`;
      const file = new File([blob], "record.docx", { type: DOCX_MIME });
      const qres = await api.generateQuestion(file, {
        number: String(i + 1),
        title: questions[i],
        question: questions[i],
        language: $("#air-lang").value,
        urk: $("#air-reg").value,
        urk_mode: $("#air-urkmode").value,
        include_code_shot: $("#air-codeshot").checked ? "1" : "0",
        api_key: $("#air-key").value.trim(),
      });
      blob = await qres.blob();
    }

    const safe = ($("#air-title").value || "record").replace(/[/\\:*?"<>|]/g, "_").trim() || "record";
    const file = new File([blob], `${safe}.docx`, { type: DOCX_MIME });
    document.dispatchEvent(new CustomEvent("autolab:open-doc", { detail: { file, path: null } }));
    if (location.hash !== "#documents") location.hash = "#documents";
    status.textContent = "Done — opened in the editor. Save & download from the panel.";
    status.className = "hint is-ok";
    toast("Record generated");
  } catch (err) {
    status.textContent = err.message;
    status.className = "hint is-err";
  } finally {
    btn.disabled = false;
    document.dispatchEvent(new Event("autolab:refresh-account"));
  }
}

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c]);
}
