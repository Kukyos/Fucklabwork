// Tools view — list in canvas, controls in the right panel.

import { api, downloadResponse } from "../api.js";

let toast = () => {};
let state = null;
let activeTool = null;

const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));

export function initTools(ctx) {
  state = ctx.state;
  toast = ctx.toast;

  // Card clicks
  $$(".tool-card").forEach((card) => {
    card.addEventListener("click", () => {
      if (card.classList.contains("is-soon")) return;
      const id = card.dataset.tool;
      if (!id) return;
      selectTool(id, card);
    });
  });

  // Replace tool wiring (in the right panel)
  const fileInput = $("#rep-file");
  const fileLabel = $("#rep-file-label");
  const dropMini = fileInput.closest(".drop-mini");

  fileInput.addEventListener("change", () => {
    const f = fileInput.files[0];
    if (f) {
      fileLabel.textContent = f.name;
      dropMini.classList.add("has-file");
    } else {
      fileLabel.textContent = "Choose a .docx…";
      dropMini.classList.remove("has-file");
    }
  });

  $("#replace-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = $("#rep-status");
    status.textContent = "";
    status.className = "hint";

    const f = fileInput.files[0];
    const find = $("#rep-find").value;
    const replace = $("#rep-replace").value;

    if (!f) { status.textContent = "Pick a .docx first."; status.className = "hint is-err"; return; }
    if (!find) { status.textContent = "Find can't be empty."; status.className = "hint is-err"; return; }

    status.textContent = "Working…";
    try {
      const res = await api.replace(f, find, replace);
      const count = parseInt(res.headers.get("X-Replace-Count") || "0", 10);
      await downloadResponse(res, f.name.replace(/\.docx$/i, "_modified.docx"));
      status.textContent = count === 0
        ? "No matches found (file saved anyway)."
        : `Replaced ${count} occurrence${count === 1 ? "" : "s"}.`;
      status.className = "hint is-ok";
    } catch (err) {
      status.textContent = err.message;
      status.className = "hint is-err";
    }
  });
}

function selectTool(id, card) {
  activeTool = id;
  $$(".tool-card").forEach((c) => c.classList.toggle("is-active", c === card));
  $("#rp-tool-empty").hidden = true;
  $("#rp-tool-replace").hidden = id !== "replace";
}
