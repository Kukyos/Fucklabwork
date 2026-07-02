// Templates view — gallery in canvas, fill form in the right panel.

import { api } from "../api.js";

let toast = () => {};
let state = null;
let templates = [];
let activeTpl = null;

const $ = (s, r = document) => r.querySelector(s);

export function initTemplates(ctx) {
  state = ctx.state;
  toast = ctx.toast;

  loadTemplates();
  $("#tpl-form").addEventListener("submit", onSubmit);
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

function openFill(t, card) {
  activeTpl = t;
  document.querySelectorAll(".tpl-card").forEach((c) => c.classList.toggle("is-active", c === card));
  $("#rp-tpl-empty").hidden = true;
  $("#rp-tpl-fill").hidden = false;
  $("#rp-tpl-title").textContent = `Fill — ${t.name}`;
  $("#tpl-status").textContent = "";
  $("#tpl-status").className = "hint";
  if (state.profile) {
    if (!$("#tpl-reg").value) $("#tpl-reg").value = state.profile.default_urk || "";
    if (!$("#tpl-course").value) $("#tpl-course").value = state.profile.preferences?.default_course_title || "";
  }
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
    const file = new File([blob], finalName, {
      type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });

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

function escapeHTML(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c]);
}
