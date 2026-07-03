// Account view (web + billing only) — sign-in, balance, top-ups, pricing.

import { billing, sendOtp, verifyOtp, signOut, refreshMe, topUp } from "../billing.js";

let toast = () => {};
const $ = (s, r = document) => r.querySelector(s);

const PRICE_LABELS = {
  rewrite: "AI rewrite (per paragraph)",
  patch_screens: "Screenshot patching (per document)",
  gen_question: "Generated question (code + output + shots)",
};

export function initAccount(ctx) {
  toast = ctx.toast;
  $("#no-billing-callout").hidden = true;
  $("#account-wrap").hidden = false;
  $("#pricing-card").hidden = false;

  let email = "";
  $("#acct-email-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    email = $("#acct-email").value.trim();
    const st = $("#acct-status");
    st.textContent = "Sending code…";
    try {
      await sendOtp(email);
      $("#acct-code-form").hidden = false;
      st.textContent = `Code sent to ${email} — check spam too.`;
      $("#acct-code").focus();
    } catch (err) { st.textContent = err.message; }
  });

  $("#acct-code-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const st = $("#acct-status");
    st.textContent = "Verifying…";
    try {
      await verifyOtp(email, $("#acct-code").value.trim());
      st.textContent = "";
      $("#acct-code-form").hidden = true;
      await renderAccount();
      toast("Signed in.");
    } catch (err) { st.textContent = err.message; }
  });

  $("#acct-signout").addEventListener("click", () => {
    signOut();
    renderAccount();
  });

  $("#credits-pill").addEventListener("click", () => { location.hash = "#profile"; });

  const wrap = $("#topup-buttons");
  for (const amt of billing.config.packs) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "btn-ghost";
    b.textContent = `₹${amt}`;
    b.addEventListener("click", () => doTopUp(amt));
    wrap.appendChild(b);
  }

  const list = $("#price-list");
  for (const [op, price] of Object.entries(billing.config.prices)) {
    const row = document.createElement("div");
    row.className = "rp-info-row";
    row.innerHTML = `<span class="k">${PRICE_LABELS[op] || op}</span><span class="v">₹${price}</span>`;
    list.appendChild(row);
  }
  const free = document.createElement("div");
  free.className = "rp-info-row";
  free.innerHTML = '<span class="k">Text find &amp; replace</span><span class="v">Free</span>';
  list.appendChild(free);

  document.addEventListener("autolab:refresh-account", renderAccount);
  renderAccount();
}

function doTopUp(amount) {
  const st = $("#topup-status");
  st.textContent = "Opening checkout…";
  topUp(amount, async (err, v) => {
    if (err) { st.textContent = err.message; return; }
    st.textContent = `Added ₹${v.added}. Balance: ₹${v.balance}.`;
    toast(`Topped up ₹${v.added}`);
    await renderAccount();
  }).catch((e) => { st.textContent = e.message; });
}

export async function renderAccount() {
  const signedIn = !!billing.session;
  $("#acct-signedout").hidden = signedIn;
  $("#acct-signedin").hidden = !signedIn;
  $("#topup-card").hidden = !signedIn;
  $("#acct-state").textContent = signedIn ? "Signed in" : "Signed out";
  const pill = $("#credits-pill");
  const repHint = $("#rep-key-hint");
  if (!signedIn) {
    pill.hidden = true;
    if (repHint) {
      repHint.innerHTML =
        'Free at <strong>aistudio.google.com</strong> — or sign in (Profile tab) and pay ₹10 from credits.';
    }
    return;
  }
  $("#acct-email-v").textContent = billing.session.email;
  if (repHint) {
    repHint.innerHTML =
      `Leave blank to use ₹${billing.config.prices.patch_screens} of credits, or paste your own key (free).`;
  }
  try {
    const me = await refreshMe();
    $("#acct-balance").textContent = `₹${me.balance}`;
    pill.textContent = `₹${me.balance}`;
    pill.hidden = false;
  } catch {
    $("#acct-balance").textContent = "—";
  }
}
