// Profile view — saved URKs + defaults + API key (desktop only).

import { api } from "../api.js";

let toast = () => {};
let state = null;
let profile = null;

const $ = (s, r = document) => r.querySelector(s);

export function initProfile(ctx) {
  state = ctx.state;
  toast = ctx.toast;

  $("#urk-add").addEventListener("submit", async (e) => {
    e.preventDefault();
    const v = $("#urk-add-input").value.trim();
    if (!v) return;
    try {
      profile = await api.addUrk(v);
      state.profile = profile;
      $("#urk-add-input").value = "";
      renderProfile();
      toast(`Saved ${v}`);
    } catch (err) { toast(err.message, "err"); }
  });

  $("#pref-save").addEventListener("click", async () => {
    const course = $("#pref-course").value;
    try {
      profile = await api.patchProfile({ default_course_title: course });
      state.profile = profile;
      const s = $("#pref-status");
      s.textContent = "Saved.";
      s.className = "hint is-ok";
    } catch (err) { toast(err.message, "err"); }
  });

  $("#api-key-save").addEventListener("click", async () => {
    const k = $("#api-key").value.trim();
    if (!k) {
      const s = $("#api-key-status");
      s.textContent = "Paste your key first.";
      s.className = "hint is-err";
      return;
    }
    try {
      profile = await api.patchProfile({ ai_api_key: k });
      state.profile = profile;
      $("#api-key").value = "";
      const s = $("#api-key-status");
      s.textContent = "Saved.";
      s.className = "hint is-ok";
      renderProfile();
    } catch (err) { toast(err.message, "err"); }
  });

  $("#api-key-clear").addEventListener("click", async () => {
    try {
      profile = await api.patchProfile({ ai_api_key: "" });
      state.profile = profile;
      const s = $("#api-key-status");
      s.textContent = "Cleared.";
      s.className = "hint";
      renderProfile();
    } catch (err) { toast(err.message, "err"); }
  });

  document.addEventListener("autolab:desktop-ready", loadProfile);
}

async function loadProfile() {
  try {
    profile = await api.getProfile();
    state.profile = profile;
  } catch {
    profile = null;
    return;
  }
  renderProfile();
}

function renderProfile() {
  if (!profile) return;

  const wrap = $("#urks-chips");
  wrap.innerHTML = "";
  if (!profile.saved_urks?.length) {
    const e = document.createElement("span");
    e.className = "urks-empty";
    e.textContent = "No register numbers saved yet.";
    wrap.appendChild(e);
  } else {
    for (const urk of profile.saved_urks) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "urk-chip" + (urk === profile.default_urk ? " is-default" : "");
      chip.title = urk === profile.default_urk ? "Default" : "Click to make default";

      const label = document.createElement("span");
      label.textContent = urk;
      chip.appendChild(label);

      const x = document.createElement("button");
      x.type = "button";
      x.className = "x";
      x.textContent = "×";
      x.setAttribute("aria-label", `Remove ${urk}`);
      x.addEventListener("click", async (e) => {
        e.stopPropagation();
        try {
          profile = await api.removeUrk(urk);
          state.profile = profile;
          renderProfile();
        } catch (err) { toast(err.message, "err"); }
      });
      chip.appendChild(x);

      chip.addEventListener("click", async () => {
        if (urk === profile.default_urk) return;
        try {
          profile = await api.patchProfile({ default_urk: urk });
          state.profile = profile;
          renderProfile();
        } catch (err) { toast(err.message, "err"); }
      });
      wrap.appendChild(chip);
    }
  }

  $("#pref-course").value = profile.preferences?.default_course_title || "";
  $("#ai-key-state").textContent = profile.ai_key_set
    ? `Key set · ${profile.ai_key_preview}`
    : "No key set";

  // Mirror summary into the right panel
  if ($("#rp-pf-urks")) $("#rp-pf-urks").textContent = String(profile.saved_urks?.length || 0);
  if ($("#rp-pf-ai")) $("#rp-pf-ai").textContent = profile.ai_key_set ? `Yes · ${profile.ai_key_preview}` : "No";
  if ($("#rp-pf-mode")) $("#rp-pf-mode").textContent = state.capabilities.desktop ? "Desktop" : "Web";
  if ($("#rp-pf-path") && state.capabilities.data_dir) $("#rp-pf-path").textContent = state.capabilities.data_dir;
}
