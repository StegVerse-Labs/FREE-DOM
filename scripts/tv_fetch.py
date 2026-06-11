#!/usr/bin/env python3
"""
Fetch short-lived, scoped secrets for FREE-DOM CI under StegVerse governance.

Two paths, selected automatically:

  1. GOVERNED ENV PATH (default, server-free)
     - Validates the request against TVC governance (roles.yml + issuers.yml)
       via tvc_secret_governance.evaluate().
     - Reads secret VALUES from the execution environment (GitHub Actions
       encrypted secrets exported as env vars). Values never live in TV/TVC.
     - Emits a USAGE RECEIPT (no values) to TV's chainlog, proving how the
       secret read was governed.

  2. SERVER/API PATH (optional)
     - Used only when --tv-url points at a live TV deployment.
     - Performs the original OIDC exchange + KV get over HTTPS.

Security goals (unchanged):
  - Never print secret values
  - Restrictive (0600) output file permissions, atomic writes
  - Only requested + permitted keys are serialized
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import time
from pathlib import Path

try:
    import requests
except Exception:
    requests = None


def log(msg: str) -> None:
    print(f"[tv_fetch] {msg}", flush=True)


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def write_secrets_json(path: Path, payload: dict) -> None:
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


def env_key_to_var(key: str) -> str:
    """
    Map a governance key to its environment variable name.
    'secure_submission_url' -> 'TV_SECURE_SUBMISSION_URL'
    'osint/newsapi'         -> 'TV_OSINT_NEWSAPI'
    Overridable via TV_ENV_PREFIX (default 'TV_').
    """
    prefix = os.environ.get("TV_ENV_PREFIX", "TV_")
    norm = key.upper().replace("/", "_").replace("-", "_").replace(".", "_")
    return f"{prefix}{norm}"


# --------------------------------------------------------------------------- #
# Path 1: governed env (server-free)
# --------------------------------------------------------------------------- #
def run_governed_env(args, keys: list[str], out_path: Path) -> None:
    # Import the portable governance core (kept alongside this script or on PYTHONPATH).
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import tvc_secret_governance as gov
    except Exception as e:
        raise RuntimeError(
            "tvc_secret_governance module not found. Place tvc_secret_governance.py "
            f"alongside tv_fetch.py or on PYTHONPATH. ({e})"
        )

    policy_dir = Path(args.policy_dir)

    # OIDC context (used by issuers.yml binding). In Actions these are provided.
    repo_full = os.environ.get("GITHUB_REPOSITORY", "")  # "StegVerse/FREE-DOM"
    org, _, repo = repo_full.partition("/")
    workflow_ref = os.environ.get("GITHUB_WORKFLOW_REF", "")  # contains workflow file
    workflow_file = ""
    if workflow_ref:
        # .../.github/workflows/auto_update_tv_patch.yml@refs/heads/main
        wf = workflow_ref.split("@")[0]
        workflow_file = wf.split("/")[-1]
    branch = os.environ.get("GITHUB_REF_NAME", "")

    oidc_ctx = {"org": org, "repo": repo, "workflow": workflow_file, "branch": branch}
    has_ctx = any(oidc_ctx.values())

    decision = gov.evaluate(
        role=args.role,
        requested_keys=keys,
        policy_dir=policy_dir,
        oidc_ctx=oidc_ctx if has_ctx else None,
        # Local runs (no OIDC ctx) may relax binding with --allow-unbound.
        require_binding=not args.allow_unbound,
    )

    # Always emit a usage receipt to TV (governs success AND denial).
    receipt = decision.to_receipt(policy_dir=policy_dir, source="execution_env")
    if args.receipt_out:
        rp = Path(args.receipt_out)
        rp.parent.mkdir(parents=True, exist_ok=True)
        with rp.open("a", encoding="utf-8") as f:
            f.write(json.dumps(receipt) + "\n")
        log(f"Wrote usage receipt to {rp} (receipt_hash={receipt['receipt_hash'][:23]}…)")

    if not decision.admissible:
        raise RuntimeError(f"governance_denied: {', '.join(decision.reasons)}")

    # Read VALUES from the environment for permitted keys only.
    payload, missing = {}, []
    for k in decision.allowed_keys:
        var = env_key_to_var(k)
        val = os.environ.get(var)
        if val is None:
            missing.append((k, var))
        else:
            payload[k] = val

    if missing:
        names = ", ".join(f"{k} (expected env {v})" for k, v in missing)
        raise RuntimeError(f"missing_secret_values_in_env: {names}")

    write_secrets_json(out_path, payload)
    log(f"Wrote {len(payload)} governed value(s) to {out_path} (permissions: 600)")


# --------------------------------------------------------------------------- #
# Path 2: server/API (optional) — original OIDC + KV flow
# --------------------------------------------------------------------------- #
def _require_requests() -> None:
    if requests is None:
        raise RuntimeError("requests is required for the server path. pip install requests.")


def get_github_oidc_jwt(audience: str) -> str:
    url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    tok = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    if not url or not tok:
        raise RuntimeError("Missing GitHub OIDC env vars. Ensure permissions: id-token: write.")
    url = f"{url}{'&' if '?' in url else '?'}audience={audience}"
    import urllib.request
    import json as _json
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = _json.load(resp)
    val = data.get("value")
    if not val:
        raise RuntimeError("No 'value' in GitHub OIDC response.")
    return val


def exchange_oidc_for_tv_token(tv_base_url: str, id_token: str, role: str) -> str:
    _require_requests()
    url = tv_base_url.rstrip("/") + "/oidc/exchange"
    r = requests.post(url, json={"id_token": id_token, "role": role},
                      headers={"Accept": "application/json"}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"TV OIDC exchange failed: {r.status_code} {r.text}")
    tok = r.json().get("access_token")
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
        raise RuntimeError("TV dev token expired.")
    return tok


def fetch_keys(tv_base_url: str, tv_token: str, keys: list[str]) -> dict:
    _require_requests()
    url = tv_base_url.rstrip("/") + "/kv/get"
    r = requests.post(url, headers={"Authorization": f"Bearer {tv_token}", "Accept": "application/json"},
                      json={"keys": keys}, timeout=20)
    if r.status_code != 200:
        raise RuntimeError(f"TV KV get failed: {r.status_code} {r.text}")
    data = r.json()
    if not isinstance(data, dict):
        raise RuntimeError("TV KV get returned unexpected JSON type.")
    return data


def run_server(args, keys: list[str], out_path: Path) -> None:
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
    filtered = {k: values.get(k) for k in keys if k in values}
    write_secrets_json(out_path, filtered)
    log(f"Wrote secrets JSON to {out_path} (permissions: 600)")


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True)
    ap.add_argument("--keys", required=True, help="Comma-separated list of keys to fetch")
    ap.add_argument("--out", default="", help="Output path for secrets JSON (recommend under $RUNNER_TEMP)")
    # Governed env path
    ap.add_argument("--policy-dir", default="stegverse_tv_policy",
                    help="Path to TV policy dir (roles.yml + issuers.yml)")
    ap.add_argument("--receipt-out", default="",
                    help="Append a usage receipt (no values) to this chainlog path")
    ap.add_argument("--allow-unbound", action="store_true",
                    help="Local/offline: skip OIDC binding requirement (scope still enforced)")
    # Server path (optional)
    ap.add_argument("--tv-url", default="", help="If set, use the HTTPS TV deployment instead of env path")
    ap.add_argument("--aud", default="stegverse-tv")
    ap.add_argument("--profile")
    args = ap.parse_args()

    keys = [k.strip() for k in args.keys.split(",") if k.strip()]
    if not keys:
        print("No keys requested. Use --keys key1,key2", file=sys.stderr)
        sys.exit(2)

    if args.out.strip():
        out_path = Path(args.out)
    else:
        base = os.environ.get("RUNNER_TEMP") or "."
        out_path = Path(base) / "tv.json"

    use_server = bool(args.tv_url.strip()) or bool(args.profile)
    if use_server:
        log("Using server/API path.")
        run_server(args, keys, out_path)
    else:
        log("Using governed env path (server-free).")
        run_governed_env(args, keys, out_path)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[tv_fetch] ERROR: {e}", file=sys.stderr)
        sys.exit(1)
