#!/usr/bin/env python3
"""
Thin client to fetch short-lived, scoped secrets from StegVerse/TV via OIDC.

- CI: use GitHub OIDC (requires workflow permissions: id-token: write)
- Local: use --profile to read a short-lived token from ~/.config/stegverse-tv/<profile>.json

Security goals:
- Never print secret values
- Avoid predictable default output paths
- Write output with restrictive file permissions
- Ensure only requested keys are returned/serialized
"""

from __future__ import annotations
import argparse, json, os, sys, time, tempfile
from pathlib import Path

try:
    import requests
except Exception:
    requests = None


def log(msg: str) -> None:
    print(f"[tv_fetch] {msg}", flush=True)


def _require_requests() -> None:
    if requests is None:
        raise RuntimeError("requests is required. Add 'pip install requests' in your workflow.")


def get_github_oidc_jwt(audience: str) -> str:
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    tok = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not url or not tok:
        raise RuntimeError("Missing GitHub OIDC request env vars. Ensure permissions: id-token: write.")
    url = f"{url}{'&' if '?' in url else '?'}audience={audience}"

    import urllib.request
    import json as _json

    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = _json.load(resp)

    val = data.get("value")
    if not val:
        raise RuntimeError("Failed to obtain OIDC ID token from GitHub (no 'value' in response).")
    return val


def exchange_oidc_for_tv_token(tv_base_url: str, id_token: str, role: str) -> str:
    _require_requests()
    url = tv_base_url.rstrip("/") + "/oidc/exchange"
    r = requests.post(
        url,
        json={"id_token": id_token, "role": role},
        headers={"Accept": "application/json"},
        timeout=20,
    )
    if r.status_code != 200:
        raise RuntimeError(f"TV OIDC exchange failed: {r.status_code} {r.text}")
    try:
        data = r.json()
    except Exception:
        raise RuntimeError("TV OIDC exchange returned non-JSON response.")
    tok = data.get("access_token")
    if not tok:
        raise RuntimeError("TV did not return access_token.")
    return tok


def get_tv_token_from_profile(profile: str) -> str:
    cfg = Path.home() / ".config" / "stegverse-tv" / f"{profile}.json"
    if not cfg.exists():
        raise RuntimeError(f"TV profile not found: {cfg}")
    data = json.loads(cfg.read_text(encoding="utf-8"))
    tok = data.get("access_token")
    if not tok:
        raise RuntimeError("TV dev token missing in profile file.")
    exp = data.get("exp")
    if exp and int(exp) < int(time.time()):
        raise RuntimeError("TV dev token expired. Renew via TV CLI.")
    return tok


def fetch_keys(tv_base_url: str, tv_token: str, keys: list[str]) -> dict:
    _require_requests()
    url = tv_base_url.rstrip("/") + "/kv/get"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {tv_token}", "Accept": "application/json"},
        json={"keys": keys},
        timeout=20,
    )
    if r.status_code != 200:
        raise RuntimeError(f"TV KV get failed: {r.status_code} {r.text}")
    try:
        data = r.json()
    except Exception:
        raise RuntimeError("TV KV get returned non-JSON response.")
    if not isinstance(data, dict):
        raise RuntimeError("TV KV get returned unexpected JSON type (expected object).")
    return data


def write_secrets_json(path: Path, payload: dict) -> None:
    # Write with restrictive permissions. Use atomic write to avoid partial files.
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", dir=str(path.parent))
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False))
        os.replace(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except Exception:
            pass
        raise


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tv-url", required=True)
    ap.add_argument("--role", required=True)
    ap.add_argument("--aud", default="stegverse-tv")
    ap.add_argument("--keys", required=True, help="Comma-separated list of keys to fetch")
    ap.add_argument("--out", default="", help="Output path for secrets JSON (recommended: under $RUNNER_TEMP)")
    ap.add_argument("--profile")
    args = ap.parse_args()

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    if not keys:
        print("No keys requested. Use --keys key1,key2", file=sys.stderr)
        sys.exit(2)

    # Default output: runner temp if available, else ./tv.json (still safe perms)
    if args.out.strip():
        out_path = Path(args.out)
    else:
        base = os.environ.get("RUNNER_TEMP") or "."
        out_path = Path(base) / "tv.json"

    if args.profile:
        log(f"Using TV dev profile '{args.profile}'")
        tv_token = get_tv_token_from_profile(args.profile)
    else:
        log("Acquiring GitHub OIDC ID token…")
        id_token = get_github_oidc_jwt(audience=args.aud)
        log("Exchanging OIDC for short-lived TV token…")
        tv_token = exchange_oidc_for_tv_token(args.tv_url, id_token, role=args.role)

    log("Fetching requested keys (values will not be printed)…")
    values = fetch_keys(args.tv_url, tv_token, keys)

    # Guardrail: only write requested keys (ignore accidental extras)
    filtered = {k: values.get(k) for k in keys if k in values}

    write_secrets_json(out_path, filtered)
    log(f"Wrote secrets JSON to {out_path} (permissions: 600)")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[tv_fetch] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
