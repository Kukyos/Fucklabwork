"""Billing: Supabase auth + credit wallet + Razorpay checkout. Stdlib HTTP only.

Off by default — turns on when these env vars are set (Vercel project settings,
or your shell when testing locally):

  SUPABASE_URL            https://xxxx.supabase.co
  SUPABASE_ANON_KEY       public anon key (safe to hand to browsers)
  SUPABASE_SERVICE_KEY    service_role key (server only — NEVER to browsers)
  RAZORPAY_KEY_ID         rzp_test_... / rzp_live_...
  RAZORPAY_KEY_SECRET
  RAZORPAY_WEBHOOK_SECRET optional; only the webhook route needs it
  GEMINI_API_KEY          server-side key that paid operations run on

1 credit = ₹1. Credits pay only for AI ops that run on the server's Gemini
key. Plain text find & replace is always free, and bringing your own key
makes every AI op free too.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import urllib.error
import urllib.request

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
SERVER_GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

PRICES = {
    "rewrite": 1,         # one AI paragraph rewrite
    "patch_screens": 10,  # screenshot patching, whole document
    "gen_question": 5,    # one generated question: code + output + screenshots
}
PACKS = [50, 100, 200]
MIN_TOPUP, MAX_TOPUP = 20, 2000


def enabled() -> bool:
    return bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_SERVICE_KEY
                and RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET)


def _http(url: str, *, data: dict | None = None, headers: dict | None = None,
          method: str | None = None, timeout: int = 20):
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def _service_headers() -> dict:
    return {"apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}


# --- auth ---------------------------------------------------------------

def auth_user(authorization: str) -> dict:
    """Validate a Supabase access token from an Authorization header.

    Returns {"id": ..., "email": ...}; raises ValueError when missing/invalid.
    """
    if not authorization.lower().startswith("bearer "):
        raise ValueError("Sign in first (Account tab).")
    token = authorization[7:].strip()
    try:
        u = _http(f"{SUPABASE_URL}/auth/v1/user",
                  headers={"apikey": SUPABASE_ANON_KEY,
                           "Authorization": f"Bearer {token}"})
    except urllib.error.HTTPError as e:
        raise ValueError("Session expired — sign in again.") from e
    if not u or not u.get("id"):
        raise ValueError("Session expired — sign in again.")
    return {"id": u["id"], "email": u.get("email", "")}


# --- wallet (Supabase Postgres via PostgREST) ----------------------------

def balance(user_id: str) -> int:
    rows = _http(
        f"{SUPABASE_URL}/rest/v1/wallets?user_id=eq.{user_id}&select=balance",
        headers=_service_headers(),
    )
    return rows[0]["balance"] if rows else 0


def spend(user_id: str, cost: int, reason: str) -> int:
    """Atomic decrement. Returns the new balance, or -1 if insufficient."""
    return _http(f"{SUPABASE_URL}/rest/v1/rpc/spend_credits",
                 data={"uid": user_id, "cost": cost, "why": reason},
                 headers=_service_headers())


def credit(user_id: str, amount: int, reason: str, ref: str | None = None) -> int:
    """Add credits. Passing a payment id as `ref` makes the call idempotent."""
    return _http(f"{SUPABASE_URL}/rest/v1/rpc/add_credits",
                 data={"uid": user_id, "amount": amount, "why": reason,
                       "pay_ref": ref},
                 headers=_service_headers())


# --- Razorpay -------------------------------------------------------------

def _rzp_auth() -> str:
    tok = base64.b64encode(
        f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode()).decode()
    return f"Basic {tok}"


def rzp_create_order(amount_rupees: int, user_id: str) -> dict:
    return _http("https://api.razorpay.com/v1/orders",
                 data={"amount": amount_rupees * 100, "currency": "INR",
                       "notes": {"user_id": user_id}},
                 headers={"Authorization": _rzp_auth()})


def rzp_get_order(order_id: str) -> dict:
    return _http(f"https://api.razorpay.com/v1/orders/{order_id}",
                 headers={"Authorization": _rzp_auth()})


def verify_payment_sig(order_id: str, payment_id: str, signature: str) -> bool:
    mac = hmac.new(RAZORPAY_KEY_SECRET.encode(),
                   f"{order_id}|{payment_id}".encode(), hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)


def verify_webhook_sig(body: bytes, signature: str) -> bool:
    if not RAZORPAY_WEBHOOK_SECRET:
        return False
    mac = hmac.new(RAZORPAY_WEBHOOK_SECRET.encode(), body, hashlib.sha256)
    return hmac.compare_digest(mac.hexdigest(), signature)
