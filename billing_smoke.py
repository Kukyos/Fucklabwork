"""Offline check for billing.py — signatures, auth parsing, wallet calls (mocked)."""

import hashlib
import hmac
import json

import billing


def main() -> None:
    # --- Razorpay payment signature (the checkout handler path) ---
    billing.RAZORPAY_KEY_SECRET = "test_secret"
    good = hmac.new(b"test_secret", b"order_1|pay_1", hashlib.sha256).hexdigest()
    assert billing.verify_payment_sig("order_1", "pay_1", good)
    assert not billing.verify_payment_sig("order_1", "pay_1", "0" * 64)
    assert not billing.verify_payment_sig("order_2", "pay_1", good)

    # --- webhook signature ---
    billing.RAZORPAY_WEBHOOK_SECRET = "hook_secret"
    body = json.dumps({"event": "payment.captured"}).encode()
    sig = hmac.new(b"hook_secret", body, hashlib.sha256).hexdigest()
    assert billing.verify_webhook_sig(body, sig)
    assert not billing.verify_webhook_sig(body + b" ", sig)
    billing.RAZORPAY_WEBHOOK_SECRET = ""
    assert not billing.verify_webhook_sig(body, sig)  # unset secret rejects all

    # --- auth header parsing ---
    for bad in ("", "Basic abc", "token-without-scheme"):
        try:
            billing.auth_user(bad)
            raise AssertionError(f"accepted bad header: {bad!r}")
        except ValueError:
            pass

    # --- wallet RPC payloads (HTTP mocked) ---
    calls = []

    def fake_http(url, *, data=None, headers=None, method=None, timeout=20):
        calls.append((url, data))
        if "spend_credits" in url:
            return 40
        if "add_credits" in url:
            return 90
        if "wallets" in url:
            return [{"balance": 50}]
        return None

    real = billing._http
    billing._http = fake_http
    billing.SUPABASE_URL = "https://x.supabase.co"
    billing.SUPABASE_SERVICE_KEY = "svc"
    try:
        assert billing.balance("u1") == 50
        assert billing.spend("u1", 10, "patch_screens") == 40
        assert billing.credit("u1", 50, "topup", ref="pay_1") == 90
    finally:
        billing._http = real

    assert calls[1][1] == {"uid": "u1", "cost": 10, "why": "patch_screens"}
    assert calls[2][1] == {"uid": "u1", "amount": 50, "why": "topup", "pay_ref": "pay_1"}

    print("PASS")


if __name__ == "__main__":
    main()
