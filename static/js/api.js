// Tiny fetch wrappers around the AutoLAB backend.

let authToken = null;
export function setAuthToken(t) { authToken = t; }
function authHeaders(extra = {}) {
  return authToken ? { Authorization: `Bearer ${authToken}`, ...extra } : extra;
}

async function jsonOrThrow(res) {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const j = await res.json();
      if (j && j.detail) detail = j.detail;
    } catch {}
    throw new Error(detail);
  }
  return res.json();
}

async function fileOrThrow(res) {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { detail = (await res.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return res;
}

export const api = {
  async capabilities() {
    return jsonOrThrow(await fetch("/api/capabilities"));
  },

  async parseDoc(file) {
    const fd = new FormData();
    fd.append("file", file);
    return jsonOrThrow(await fetch("/api/document/parse", { method: "POST", body: fd }));
  },

  async saveDoc(file, edits) {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("edits", JSON.stringify(edits));
    return fileOrThrow(await fetch("/api/document/save", { method: "POST", body: fd }));
  },

  async replace(file, find, replace, patchImages = false, apiKey = "") {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("find", find);
    fd.append("replace", replace);
    if (patchImages) {
      fd.append("patch_images", "true");
      fd.append("api_key", apiKey);
    }
    return fileOrThrow(await fetch("/api/replace", {
      method: "POST", headers: authHeaders(), body: fd,
    }));
  },

  async generateQuestion(file, fields) {
    const fd = new FormData();
    fd.append("file", file);
    for (const [k, v] of Object.entries(fields)) fd.append(k, v);
    return fileOrThrow(await fetch("/api/generate/question", {
      method: "POST", headers: authHeaders(), body: fd,
    }));
  },

  async billingConfig() {
    return jsonOrThrow(await fetch("/api/billing/config"));
  },
  async me() {
    return jsonOrThrow(await fetch("/api/me", { headers: authHeaders() }));
  },
  async payOrder(amount) {
    return jsonOrThrow(await fetch("/api/pay/order", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ amount }),
    }));
  },
  async payVerify(order_id, payment_id, signature) {
    return jsonOrThrow(await fetch("/api/pay/verify", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ order_id, payment_id, signature }),
    }));
  },

  async listTemplates() {
    return jsonOrThrow(await fetch("/api/templates"));
  },

  async fillTemplate(payload) {
    return fileOrThrow(await fetch("/api/template/fill", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }));
  },

  async generateCode(payload) {
    return jsonOrThrow(await fetch("/api/ai/generate-code", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }));
  },

  async aiRewrite(text, instruction = "", target_words = null) {
    return jsonOrThrow(await fetch("/api/ai/rewrite", {
      method: "POST",
      headers: authHeaders({ "Content-Type": "application/json" }),
      body: JSON.stringify({ text, instruction, target_words }),
    }));
  },

  async getProfile() {
    return jsonOrThrow(await fetch("/api/profile"));
  },
  async addUrk(urk) {
    return jsonOrThrow(await fetch("/api/profile/urks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ urk }),
    }));
  },
  async removeUrk(urk) {
    return jsonOrThrow(await fetch(`/api/profile/urks/${encodeURIComponent(urk)}`, { method: "DELETE" }));
  },
  async patchProfile(patch) {
    return jsonOrThrow(await fetch("/api/profile", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }));
  },
};

export async function downloadResponse(res, fallbackName) {
  const cd = res.headers.get("Content-Disposition") || "";
  const m = cd.match(/filename="([^"]+)"/);
  const name = m ? m[1] : fallbackName;
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
