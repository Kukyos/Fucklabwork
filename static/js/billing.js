// Account: Supabase email-OTP auth + credits + Razorpay top-up. No SDKs —
// raw fetch against Supabase auth REST, Razorpay's checkout.js loaded on demand.

import { api, setAuthToken } from "./api.js";

export const billing = { config: { enabled: false }, session: null, me: null };

const LS = "autolab-session";

function saveSession(s) {
  billing.session = s;
  try {
    if (s) localStorage.setItem(LS, JSON.stringify(s));
    else localStorage.removeItem(LS);
  } catch {}
  setAuthToken(s ? s.access_token : null);
}

async function supa(path, body) {
  const r = await fetch(`${billing.config.supabase_url}/auth/v1/${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      apikey: billing.config.supabase_anon_key,
    },
    body: JSON.stringify(body),
  });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) {
    throw new Error(j.msg || j.error_description || j.message || `HTTP ${r.status}`);
  }
  return j;
}

function sessionFrom(j, email) {
  return {
    access_token: j.access_token,
    refresh_token: j.refresh_token,
    expires_at: j.expires_at || Math.floor(Date.now() / 1000) + (j.expires_in || 3600),
    email: j.user?.email || email,
  };
}

export async function initBilling() {
  try { billing.config = await api.billingConfig(); }
  catch { billing.config = { enabled: false }; }
  if (!billing.config.enabled) return billing;
  try { billing.session = JSON.parse(localStorage.getItem(LS) || "null"); } catch {}
  if (billing.session) {
    if (Date.now() > (billing.session.expires_at - 60) * 1000) await refreshSession();
    else setAuthToken(billing.session.access_token);
  }
  return billing;
}

export async function sendOtp(email) {
  await supa("otp", { email, create_user: true });
}

export async function verifyOtp(email, code) {
  const j = await supa("verify", { type: "email", email, token: code });
  saveSession(sessionFrom(j, email));
}

export async function refreshSession() {
  if (!billing.session) return;
  try {
    const j = await supa("token?grant_type=refresh_token", {
      refresh_token: billing.session.refresh_token,
    });
    saveSession(sessionFrom(j, billing.session.email));
  } catch {
    saveSession(null);
  }
}

export function signOut() {
  saveSession(null);
  billing.me = null;
}

export async function refreshMe() {
  billing.me = await api.me();
  return billing.me;
}

// --- Razorpay checkout -------------------------------------------------

let rzpScript = null;
function loadRzp() {
  if (!rzpScript) {
    rzpScript = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "https://checkout.razorpay.com/v1/checkout.js";
      s.onload = resolve;
      s.onerror = () => reject(new Error("Couldn't load Razorpay checkout."));
      document.head.appendChild(s);
    });
  }
  return rzpScript;
}

export async function topUp(amount, onDone) {
  await loadRzp();
  const o = await api.payOrder(amount);
  const rzp = new window.Razorpay({
    key: o.key_id,
    order_id: o.order_id,
    amount: o.amount,
    currency: o.currency,
    name: "AutoLAB",
    description: `₹${amount} credit top-up`,
    prefill: { email: o.email },
    theme: { color: "#0a0a0a" },
    handler: async (resp) => {
      try {
        const v = await api.payVerify(
          resp.razorpay_order_id, resp.razorpay_payment_id, resp.razorpay_signature,
        );
        onDone(null, v);
      } catch (e) { onDone(e); }
    },
  });
  rzp.open();
}
