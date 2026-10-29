#!/usr/bin/env python3
"""Stable validator dispatcher: run the checks declared in tools/tasks/task_catalog.json.

The catalog is the manifest. Each group is one job of a workflow that was folded
into the stable dispatcher; its steps are the verbatim run bodies of that job,
stored under tools/tasks/steps/ and pinned by sha256. The dispatcher workflow
runs one matrix job per group, so every group keeps a fresh runner, exactly as
its original job had. Every group run ends ALLOW, DENY or FAIL_CLOSED, and every
non-ALLOW result carries the six fields.

stdlib only. Commands:
  matrix --event pull_request|push   print the matrix for this event (each cell marked selected true|false
                                     by the folded workflow's original path filter)
  run --group ID                     run one group's steps in order
  verify                             check the catalog against its pinned bodies
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "tools/tasks/task_catalog.json"
EXPR = re.compile(r"\$\{\{\s*(.*?)\s*\}\}")
OWNING_GOAL = "G17-WORKFLOW-SURFACE-MINIMIZATION (StegVerse-Labs/.github#167/#168)"

# Expression -> environment variable the dispatcher job sets. Anything else is
# refused by `verify`, so a folded check can never silently lose its input.
CONTEXT = {
    "runner.temp": "RUNNER_TEMP",
    "github.workspace": "GITHUB_WORKSPACE",
    "github.sha": "GITHUB_SHA",
    "github.ref": "GITHUB_REF",
    "github.ref_name": "GITHUB_REF_NAME",
    "github.repository": "GITHUB_REPOSITORY",
    "github.repository_owner": "GITHUB_REPOSITORY_OWNER",
    "github.run_id": "GITHUB_RUN_ID",
    "github.run_number": "GITHUB_RUN_NUMBER",
    "github.run_attempt": "GITHUB_RUN_ATTEMPT",
    "github.event_name": "GITHUB_EVENT_NAME",
    "github.actor": "GITHUB_ACTOR",
    "github.server_url": "GITHUB_SERVER_URL",
    "github.head_ref": "GITHUB_HEAD_REF",
    "github.base_ref": "GITHUB_BASE_REF",
    "github.job": "GITHUB_JOB",
    "github.event.before": "CATALOG_EVENT_BEFORE",
    "github.event.after": "CATALOG_EVENT_AFTER",
    "github.event.pull_request.base.sha": "CATALOG_PR_BASE_SHA",
    "github.event.pull_request.head.sha": "CATALOG_PR_HEAD_SHA",
    "github.event.pull_request.number": "CATALOG_PR_NUMBER",
    "github.event.pull_request.base.ref": "CATALOG_PR_BASE_REF",
    "github.event.pull_request.head.ref": "CATALOG_PR_HEAD_REF",
    "github.event.number": "CATALOG_PR_NUMBER",
    "github.event.pull_request.title": "CATALOG_PR_TITLE",
    "github.event.pull_request.body": "CATALOG_PR_BODY",
    "github.event.pull_request.html_url": "CATALOG_PR_HTML_URL",
    "github.event.pull_request.merge_commit_sha": "CATALOG_PR_MERGE_COMMIT_SHA",
    "github.event.release.tag_name": "CATALOG_RELEASE_TAG",
    # A folded workflow_run chain stage: the upstream stage is a job of the same
    # dispatcher run, so its head is this run's commit and its id this run's id.
    "github.event.workflow_run.conclusion": "CATALOG_UPSTREAM_CONCLUSION",
    "github.event.workflow_run.head_sha": "GITHUB_SHA",
    "github.event.workflow_run.id": "GITHUB_RUN_ID",
}


def six(code, predicate, repair, goal=OWNING_GOAL, nxt="repair the named entry, then rerun the retry_entrypoint", retry=None):
    return {
        "failure_code": code,
        "failed_predicate": predicate,
        "required_evidence_or_repair": repair,
        "retry_entrypoint": retry or "python3 tools/tasks/run_catalog.py verify",
        "owning_existing_goal": goal,
        "next_attempt": nxt,
    }


def load():
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def body(step):
    return (ROOT / step["run_file"]).read_bytes()


def expressions(value):
    found = set()
    if isinstance(value, str):
        found.update(EXPR.findall(value))
    elif isinstance(value, dict):
        for item in value.values():
            found |= expressions(item)
    elif isinstance(value, list):
        for item in value:
            found |= expressions(item)
    return found


def env_expressions(group):
    found = expressions(group.get("env") or {})
    for step in group["steps"]:
        found |= expressions(step.get("env") or {})
        found |= expressions(step.get("working_directory") or "")
    found |= expressions(group.get("artifacts") or [])
    return found


def verify(catalog=None):
    """Return a list of six-field refusals; empty means the catalog is consistent."""
    catalog = catalog or load()
    refusals = []
    seen = set()
    for group in catalog["groups"]:
        gid = group["id"]
        if gid in seen:
            refusals.append(six("CATALOG_GROUP_DUPLICATE", f"group id {gid} is unique", "rename one group"))
        seen.add(gid)
        writer = group.get("writer_surface")
        if not group.get("events") and not writer:
            refusals.append(six("CATALOG_GROUP_NO_EVENT", f"group {gid} declares at least one event", "declare pull_request and/or push"))
        if writer and (group.get("events") or not (ROOT / writer).is_file()
                       or f"run --group {gid}" not in (ROOT / writer).read_text(encoding="utf-8")):
            # A writer group runs only from its own registered writer surface, never the validator matrix.
            refusals.append(six("CATALOG_WRITER_GROUP_SURFACE", f"group {gid} declares no events and {writer} runs it", "restore the writer surface or the group"))
        for step in group["steps"]:
            path = ROOT / step["run_file"]
            if not path.is_file():
                refusals.append(six("CATALOG_STEP_BODY_ABSENT", f"{step['run_file']} exists", "restore the step body"))
                continue
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != step["run_sha256"]:
                refusals.append(six("CATALOG_STEP_BODY_DRIFT", f"sha256({step['run_file']}) == {step['run_sha256']}", f"restore the body or re-pin it (actual {digest})"))
            for expr in EXPR.findall(path.read_text(encoding="utf-8")):
                if not supported(expr):
                    refusals.append(six("CATALOG_STEP_BODY_EXPRESSION", f"{step['run_file']} expression '{expr}' is one the runner renders", "supply it through CONTEXT and the dispatcher env"))
        for expr in sorted(env_expressions(group)):
            if not supported(expr):
                refusals.append(six("CATALOG_EXPRESSION_UNSUPPORTED", f"group {gid} expression '{expr}' is one the dispatcher supplies", "supply it through CONTEXT and the dispatcher env"))
        for step in group["steps"]:
            cond = step.get("if")
            if cond is not None:
                try:
                    evaluate(cond, {}, True)
                except ValueError as exc:
                    refusals.append(six("CATALOG_CONDITION_UNSUPPORTED", f"group {gid} step condition '{cond}' is evaluable", str(exc)))
    return refusals


def resolve_ref(ref, env, ctx=None):
    """Value of one context reference, the way GitHub would render it on these events."""
    ref = ref.strip()
    ctx = ctx if ctx is not None else {}
    if ref.startswith("'") and ref.endswith("'"):
        return ref[1:-1].replace("''", "'")
    if ref in CONTEXT:
        return env.get(CONTEXT[ref], "")
    if ref.startswith("env."):
        return env.get(ref[4:], "")
    if ref.startswith("inputs.") or ref.startswith("github.event.inputs."):
        # workflow_dispatch inputs do not exist on pull_request/push: empty, as on GitHub.
        return ""
    if ref.startswith("matrix."):
        return str((ctx.get("matrix") or {}).get(ref[7:], ""))
    parts = ref.split(".")
    if len(parts) == 4 and parts[0] == "steps" and parts[2] == "outputs":
        return (ctx.get("steps") or {}).get(parts[1], {}).get(parts[3], "")
    if len(parts) == 3 and parts[0] == "steps" and parts[2] in ("outcome", "conclusion"):
        return (ctx.get("steps") or {}).get(parts[1], {}).get("__" + parts[2], "")
    if ref == "job.status":
        return "success" if ctx.get("success", True) else "failure"
    raise ValueError(f"unsupported expression {ref}")


def resolve(expr, env, ctx=None):
    for alternative in [a for a in expr.split("||")]:
        value = resolve_ref(alternative, env, ctx)
        if value:
            return value
    return ""


def supported(expr):
    try:
        resolve(expr, {}, {"steps": {}})
        return True
    except ValueError:
        return False


def substitute(value, env, ctx=None):
    def repl(match):
        return resolve(match.group(1), env, ctx)
    return EXPR.sub(repl, str(value))


# A deliberately small evaluator for the step conditions the folded jobs use:
# env.X, string literals, ==, !=, &&, ||, !, parentheses and the status functions.
TOKEN = re.compile(r"\s*(\$\{\{|\}\}|&&|\|\||==|!=|!|\(|\)|'(?:[^']|'')*'|[A-Za-z_][A-Za-z0-9_.-]*\(\)|[A-Za-z_][A-Za-z0-9_.-]*|\d+)")


def evaluate(cond, env, success, ctx=None):
    text = cond.strip()
    if text.startswith("${{") and text.endswith("}}"):
        text = text[3:-2]
    tokens, pos = [], 0
    while pos < len(text):
        match = TOKEN.match(text, pos)
        if not match:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"cannot parse condition at: {text[pos:]!r}")
        tokens.append(match.group(1))
        pos = match.end()
    status_used = any(t in ("always()", "success()", "failure()", "cancelled()") for t in tokens)
    index = 0

    def peek():
        return tokens[index] if index < len(tokens) else None

    def take():
        nonlocal index
        index += 1
        return tokens[index - 1]

    def atom():
        tok = take()
        if tok == "(":
            value = orexpr()
            if take() != ")":
                raise ValueError("unbalanced parentheses")
            return value
        if tok == "!":
            return not truthy(atom())
        if tok == "always()":
            return True
        if tok == "success()":
            return success
        if tok == "failure()":
            return not success
        if tok == "cancelled()":
            return False
        if tok.startswith("'"):
            return tok[1:-1].replace("''", "'")
        if tok in ("true", "false"):
            return tok == "true"
        if tok.isdigit():
            return tok
        return resolve_ref(tok, env, ctx)

    def truthy(v):
        return bool(v) and v != "false"

    def cmp():
        left = atom()
        while peek() in ("==", "!="):
            op = take()
            right = atom()
            left = (str(left).lower() == str(right).lower()) if op == "==" else (str(left).lower() != str(right).lower())
        return left

    def andexpr():
        left = cmp()
        while peek() == "&&":
            take()
            right = cmp()
            left = truthy(left) and truthy(right)
        return left

    def orexpr():
        left = andexpr()
        while peek() == "||":
            take()
            right = andexpr()
            left = truthy(left) or truthy(right)
        return left

    value = orexpr()
    if index != len(tokens):
        raise ValueError(f"trailing tokens in condition {cond!r}")
    result = truthy(value)
    return result if status_used else (success and result)


def shell_command(shell, script):
    # The defaults GitHub-hosted Linux runners apply to `run:`.
    if shell in (None, ""):
        return ["bash", "-e", script]
    if shell == "bash":
        return ["bash", "--noprofile", "--norc", "-eo", "pipefail", script]
    if shell == "sh":
        return ["sh", "-e", script]
    if shell == "python":
        return ["python", script]
    if "{0}" in shell:
        return [part.replace("{0}", script) for part in shlex.split(shell)]
    return shlex.split(shell) + [script]


def read_env_file(path):
    values = {}
    if not path.is_file():
        return values
    lines = path.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if "<<" in line and ("=" not in line or line.index("<<") < line.index("=")):
            name, delim = line.split("<<", 1)
            collected = []
            i += 1
            while i < len(lines) and lines[i] != delim:
                collected.append(lines[i])
                i += 1
            values[name] = "\n".join(collected)
        elif "=" in line:
            name, value = line.split("=", 1)
            values[name] = value
        i += 1
    return values


def run_group(gid):
    catalog = load()
    groups = {g["id"]: g for g in catalog["groups"]}
    temp = Path(os.environ.get("RUNNER_TEMP") or tempfile.mkdtemp())
    receipts = temp / "catalog-receipts"
    receipts.mkdir(parents=True, exist_ok=True)
    receipt = {"schema": "stegverse.task-catalog-run-receipt/v1", "group": gid, "steps": []}
    refusals = [r for r in verify(catalog) if gid in r["failed_predicate"] or "CATALOG_GROUP_DUPLICATE" == r["failure_code"]]
    group = groups.get(gid)
    if group is None:
        refusals.append(six("CATALOG_GROUP_UNKNOWN", f"group {gid} is declared in the catalog", "name a declared group"))
    if refusals:
        receipt.update(disposition="FAIL_CLOSED", refusal=refusals[0], refusals=refusals)
        (receipts / f"{gid}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2))
        return 1

    if os.environ.get("CATALOG_SELECTED") == "false":
        # The folded workflow's original path filter did not match this event's changed files.
        event = os.environ.get("GITHUB_EVENT_NAME", "")
        receipt.update(disposition="NOT_SELECTED", reason={"original_path_filter_not_matched": True, "event": event},
                       path_filters=(group.get("path_filters") or {}).get(event))
        (receipts / f"{gid}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2))
        return 0
    selected, why = selection(group)
    if not selected:
        # Selected by manifest state, not skipped: the receipt names why and what selects it.
        receipt.update(disposition="NOT_SELECTED", reason=why, select_when=group.get("select_when"))
        (receipts / f"{gid}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2))
        return 0

    env = dict(os.environ)
    env["GITHUB_WORKSPACE"] = env.get("GITHUB_WORKSPACE") or str(ROOT)
    ctx = {"steps": {}, "success": True, "matrix": group.get("matrix_values") or {}}
    for key, value in (group.get("env") or {}).items():
        env[key] = substitute(value, env, ctx)
    success = True
    for n, step in enumerate(group["steps"], 1):
        name = step.get("name") or step["run_file"]
        cond = step.get("if")
        ctx["success"] = success
        run = evaluate(cond, env, success, ctx) if cond is not None else success
        if not run:
            if step.get("id"):
                ctx["steps"][step["id"]] = {"__outcome": "skipped", "__conclusion": "skipped"}
            receipt["steps"].append({"n": n, "name": name, "result": "SKIPPED_BY_CONDITION" if success else "NOT_RUN_AFTER_FAILURE"})
            continue
        step_env = dict(env)
        for key, value in (step.get("env") or {}).items():
            step_env[key] = substitute(value, env, ctx)
        with tempfile.TemporaryDirectory() as scratch:
            scratch = Path(scratch)
            files = {k: scratch / k.lower() for k in ("GITHUB_ENV", "GITHUB_OUTPUT", "GITHUB_PATH", "GITHUB_STEP_SUMMARY")}
            for key, path in files.items():
                path.write_text("", encoding="utf-8")
                step_env[key] = str(path)
            script = scratch / "step.sh"
            raw = body(step)
            text = raw.decode("utf-8")
            # GitHub renders ${{ }} in a run block before the shell sees it; so does this.
            script.write_bytes(substitute(text, env, ctx).encode("utf-8") if EXPR.search(text) else raw)
            cwd = ROOT / substitute(step.get("working_directory") or ".", env, ctx)
            print(f"::group::[{gid}] {n}. {name}", flush=True)
            timeout = step.get("timeout_minutes") or group.get("timeout_minutes")
            try:
                code = subprocess.run(shell_command(step.get("shell"), str(script)), cwd=cwd, env=step_env,
                                      timeout=(timeout * 60 if timeout else None)).returncode
            except subprocess.TimeoutExpired:
                code = 124
            print("::endgroup::", flush=True)
            env.update(read_env_file(files["GITHUB_ENV"]))
            if step.get("id"):
                outputs = read_env_file(files["GITHUB_OUTPUT"])
                outcome = "success" if code == 0 else "failure"
                tolerated_now = str(step.get("continue_on_error", "false")).lower() == "true"
                outputs.update(__outcome=outcome, __conclusion="success" if tolerated_now else outcome)
                ctx["steps"][step["id"]] = outputs
            summary = files["GITHUB_STEP_SUMMARY"].read_text(encoding="utf-8")
            if summary and os.environ.get("GITHUB_STEP_SUMMARY"):
                with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
                    handle.write(summary)
            added = [p for p in files["GITHUB_PATH"].read_text(encoding="utf-8").splitlines() if p.strip()]
            if added:
                env["PATH"] = os.pathsep.join(list(reversed(added)) + [env.get("PATH", "")])
        tolerated = str(step.get("continue_on_error", "false")).lower() == "true"
        receipt["steps"].append({"n": n, "name": name, "exit_code": code, "continue_on_error": tolerated})
        if code != 0 and not tolerated:
            print(f"::error::[{gid}] step {n} '{name}' exited {code}")
            success = False
    collect_artifacts(group, env, temp)
    if success:
        receipt["disposition"] = "ALLOW"
    else:
        failed = [s for s in receipt["steps"] if s.get("exit_code") not in (None, 0) and not s.get("continue_on_error")]
        receipt["disposition"] = "DENY"
        # catalog_additions groups carry no source workflow/job; a missing key must not turn a DENY into a crash
        source = group.get("source") or {}
        origin = (f"folded from {source.get('workflow')} job {source.get('job')}" if source.get("workflow")
                  else "catalog addition, no folded source workflow")
        receipt["refusal"] = six(
            "CATALOG_CHECK_FAILED",
            f"every step of group {gid} ({origin}) exits 0; failed: "
            + "; ".join(f"{s['n']}. {s['name']} -> {s['exit_code']}" for s in failed),
            "fix the code or data the failed step checks; the step body itself is pinned",
            nxt="push the repair; the dispatcher reruns this group on the next pull_request or push",
            retry=f"python3 tools/tasks/run_catalog.py run --group {gid}",
        )
    (receipts / f"{gid}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"[{gid}] {receipt['disposition']}")
    return 0 if success else 1


def collect_artifacts(group, env, temp):
    """Copy each declared artifact path under RUNNER_TEMP/catalog-artifacts/<name>/ for upload."""
    import glob
    import shutil
    for artifact in group.get("artifacts") or []:
        dest = temp / "catalog-artifacts"
        for line in str(artifact.get("path") or "").splitlines():
            line = substitute(line.strip(), env)
            if not line or line.startswith("!"):
                continue
            pattern = line if os.path.isabs(line) else str(ROOT / line)
            for match in glob.glob(pattern, recursive=True):
                source = Path(match)
                target = dest / source.name
                target.parent.mkdir(parents=True, exist_ok=True)
                if source.is_dir():
                    shutil.copytree(source, target, dirs_exist_ok=True)
                elif source.is_file():
                    shutil.copy2(source, target)


def selection(group):
    """select_when: {"paths_present": [...], "paths_absent": [...]} over this checkout."""
    when = group.get("select_when") or {}
    missing = [p for p in when.get("paths_present", []) if not (ROOT / p).exists()]
    present = [p for p in when.get("paths_absent", []) if (ROOT / p).exists()]
    if missing or present:
        return False, {"paths_missing": missing, "paths_present": present, "selects_when": when.get("reason", "")}
    return True, None


def glob_regex(pattern):
    """GitHub Actions path-filter glob: * (no /), ** (any), ? and + (apply to the previous char), [set]."""
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
            continue
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
            continue
        if c == "*":
            out.append("[^/]*")
        elif c in "?+":
            out.append(c)
        elif c == "[":
            j = pattern.find("]", i + 1)
            if j == -1:
                out.append(re.escape(c))
            else:
                out.append(pattern[i:j + 1])
                i = j
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def path_matches(patterns, path):
    """Ordered include/exclude semantics of `paths`: a later `!` pattern removes an earlier match."""
    hit = False
    for pattern in patterns:
        if pattern.startswith("!"):
            if glob_regex(pattern[1:]).match(path):
                hit = False
        elif glob_regex(pattern).match(path):
            hit = True
    return hit


def filter_selects(filt, files):
    """True when the original workflow's own paths / paths-ignore filter would have started it."""
    if files is None or not filt:
        return True
    if "paths" in filt:
        return any(path_matches(filt["paths"], f) for f in files)
    if "paths_ignore" in filt:
        return any(not any(glob_regex(pat).match(f) for pat in filt["paths_ignore"]) for f in files)
    return True


def changed_files(event, env=None):
    """Files this event changed, or None when it cannot be determined (then every group is selected)."""
    env = os.environ if env is None else env
    if event == "push":
        before, after = env.get("CATALOG_EVENT_BEFORE", ""), env.get("CATALOG_EVENT_AFTER", "")
        if not before or set(before) == {"0"} or not after:
            return None
        spec = [before, after]
    elif event == "pull_request":
        base, head = env.get("CATALOG_PR_BASE_SHA", ""), env.get("CATALOG_PR_HEAD_SHA", "")
        if not base or not head:
            return None
        spec = [base + "..." + head]
    else:
        return None
    try:
        out = subprocess.run(["git", "diff", "--name-only", *spec], cwd=ROOT, check=True,
                             capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return [line for line in out.splitlines() if line]


def matrix(event, files=None):
    catalog = load()
    include = []
    for group in catalog["groups"]:
        if event not in group["events"] or group.get("dispatcher_job"):
            # A folded workflow_run chain stage runs as its own dispatcher job, keyed on
            # its upstream stage's result, not as a matrix cell.
            continue
        row = {"group": group["id"]}
        row.update(group.get("runner") or {})
        # The folded workflow's own push/pull_request path filter decides whether this cell
        # runs its steps or records NOT_SELECTED (a run, never a skipped job).
        row["selected"] = "true" if filter_selects((group.get("path_filters") or {}).get(event), files) else "false"
        include.append(row)
    return {"include": include}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("matrix")
    m.add_argument("--event", required=True)
    r = sub.add_parser("run")
    r.add_argument("--group", required=True)
    sub.add_parser("verify")
    args = parser.parse_args(argv)
    if args.cmd == "matrix":
        print(json.dumps(matrix(args.event, changed_files(args.event)), separators=(",", ":")))
        return 0
    if args.cmd == "run":
        return run_group(args.group)
    refusals = verify()
    print(json.dumps({"disposition": "ALLOW" if not refusals else "FAIL_CLOSED", "refusals": refusals}, indent=2))
    return 0 if not refusals else 1


if __name__ == "__main__":
    sys.exit(main())
