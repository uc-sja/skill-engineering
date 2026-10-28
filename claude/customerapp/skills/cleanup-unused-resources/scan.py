#!/usr/bin/env python3
"""
Unused-resource sweep for customerApp + customerapp-shared. See SKILL.md for the rules.

    scan.py [--target app|shared|both] [--delete] [--json]

Each engine searches BOTH repos for references, because customerapp-shared's fonts are only
referenced from customerApp layouts. Paths resolve from this file, so any cwd works.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
APP_REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
WORKSPACE = os.path.normpath(os.path.join(APP_REPO, ".."))
SHARED_REPO = os.path.join(WORKSPACE, "customerapp-shared")


def search_roots(exclude):
    return [
        r
        for r in (APP_REPO, SHARED_REPO)
        if os.path.normpath(r) != os.path.normpath(exclude) and os.path.isdir(r)
    ]


TARGETS = {
    "app": {
        "label": "customerApp  (Android res/)",
        "script": "scan_android_res.py",
        "repo": APP_REPO,
        "args": lambda: ["--repo", APP_REPO],
    },
    "shared": {
        "label": "customerapp-shared  (composeResources/ + androidMain res/)",
        "script": "scan_compose_res.py",
        "repo": SHARED_REPO,
        "args": lambda: ["--root", SHARED_REPO]
        + [a for r in search_roots(SHARED_REPO) for a in ("--search-root", r)],
    },
}


def run(spec, extra):
    if not os.path.isdir(spec["repo"]):
        rel = os.path.relpath(spec["repo"], APP_REPO)
        print(f"\n### ERROR: {spec['label']}")
        print(f"    expected the repo at ./{rel} (relative to customerApp), but it is not there.")
        print(f"    customerApp and customerapp-shared must be siblings — the composite")
        print(f"    build requires it. Clone it beside customerApp and re-run.")
        return 1
    cmd = [sys.executable, os.path.join(HERE, spec["script"])] + spec["args"]() + extra
    # flush: the child writes unbuffered, so an unflushed header lands after it when piped
    print(f"\n{'=' * 78}\n### {spec['label']}\n{'=' * 78}", flush=True)
    return subprocess.run(cmd, cwd=WORKSPACE).returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["app", "shared", "both"], default="both")
    ap.add_argument("--delete", action="store_true")
    ap.add_argument("--json", action="store_true")
    args, passthrough = ap.parse_known_args()

    extra = list(passthrough)
    if args.delete:
        extra.append("--delete")
    if args.json:
        extra.append("--json")

    names = ["app", "shared"] if args.target == "both" else [args.target]
    rc = 0
    for n in names:
        rc |= run(TARGETS[n], extra)

    if not args.json:
        print(f"\n{'=' * 78}")
        print("Deletions (if any) are STAGED, not committed. Review with:")
        for n in names:
            print(f"  git -C {TARGETS[n]['repo']} diff --cached --name-status --diff-filter=D")
    return rc


if __name__ == "__main__":
    sys.exit(main())
