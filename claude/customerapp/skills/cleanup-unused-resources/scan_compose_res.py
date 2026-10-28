#!/usr/bin/env python3
"""Find unused resources in a KMP / Compose Multiplatform repo. See SKILL.md for the rules.

    scan_compose_res.py [--root REPO] [--search-root DIR ...] [--delete] [--json]

Normally driven by scan.py (which supplies --root and the cross-repo --search-roots); run
directly only to target a different KMP repo. Handles composeResources/drawable
(`Res.drawable.x`), composeResources/files (`Res.readBytes("files/x")`), and the module's own
androidMain|main res/ + assets/.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict

DEFAULT_ROOT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "customerapp-shared"))

SOURCE_EXTS = {".kt", ".kts", ".java", ".swift", ".xml", ".json", ".gradle", ".pro", ".m", ".h"}
SKIP_DIR_PARTS = {"build", ".git", ".gradle", ".idea", "node_modules", "DerivedData", ".kotlin"}

# file-per-resource Android res types
ANDROID_FILE_TYPES = {
    "drawable", "layout", "raw", "color", "anim", "animator",
    "mipmap", "menu", "font", "xml", "transition", "navigation",
}


def quoted_re(name):
    """<name> inside a quoted string — the soft signal scan_android_res.py uses too."""
    return re.compile(r"""["'][^"']*\b%s\b[^"']*["']""" % re.escape(name))


def walk(base):
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_PARTS]
        for f in filenames:
            yield os.path.join(dirpath, f)


def module_of(path, root):
    """First path segment under root == gradle module (best effort)."""
    rel = os.path.relpath(path, root)
    return rel.split(os.sep)[0]


def collect_resources(root):
    """Return list of resource dicts and the set of directories holding them."""
    resources = []
    res_dirs = set()

    for path in walk(root):
        parts = path.split(os.sep)
        fname = os.path.basename(path)
        if fname == ".DS_Store":
            continue

        # --- composeResources ---
        if "composeResources" in parts:
            i = parts.index("composeResources")
            res_dirs.add(os.sep.join(parts[: i + 1]))
            if i + 1 >= len(parts) - 1:
                continue
            bucket = parts[i + 1]
            kind = bucket.split("-")[0]
            if kind == "drawable":
                resources.append({
                    "system": "composeResources",
                    "kind": "drawable",
                    "name": os.path.splitext(fname)[0],
                    "module": module_of(path, root),
                    "path": path,
                    "qualifier": bucket,
                })
            else:
                resources.append({
                    "system": "composeResources",
                    "kind": bucket,
                    "name": fname,
                    "module": module_of(path, root),
                    "path": path,
                    "qualifier": bucket,
                })
            continue

        # --- android res/ ---
        if "res" in parts:
            i = len(parts) - 1 - parts[::-1].index("res")
            if i + 2 < len(parts) + 0 and i + 1 < len(parts) - 1:
                bucket = parts[i + 1]
                kind = bucket.split("-")[0]
                if kind in ANDROID_FILE_TYPES:
                    res_dirs.add(os.sep.join(parts[: i + 1]))
                    resources.append({
                        "system": "androidRes",
                        "kind": kind,
                        "name": os.path.splitext(fname)[0],
                        "module": module_of(path, root),
                        "path": path,
                        "qualifier": bucket,
                    })
                    continue

        # --- assets/ ---
        if "assets" in parts:
            i = parts.index("assets")
            res_dirs.add(os.sep.join(parts[: i + 1]))
            resources.append({
                "system": "assets",
                "kind": "assets",
                "name": fname,
                "module": module_of(path, root),
                "path": path,
                "qualifier": os.sep.join(parts[i + 1: -1]),
            })

    return resources, res_dirs


def collect_sources(search_roots, res_dirs):
    """Map source file path -> text, excluding anything inside a resource dir."""
    sources = {}
    for sr in search_roots:
        for path in walk(sr):
            if os.path.splitext(path)[1] not in SOURCE_EXTS:
                continue
            if any(path.startswith(rd + os.sep) for rd in res_dirs):
                continue
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    sources[path] = fh.read()
            except OSError:
                pass
    return sources


def build_index(sources, root):
    """Pre-tokenise every source into (module -> set of identifiers) and keep raw text."""
    by_module_tokens = defaultdict(set)
    all_tokens = set()
    texts = []
    for path, text in sources.items():
        toks = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text))
        mod = module_of(path, root) if path.startswith(root + os.sep) else "<external>"
        by_module_tokens[mod] |= toks
        all_tokens |= toks
        texts.append((path, text))
    return by_module_tokens, all_tokens, texts


def classify(resources, by_module_tokens, all_tokens, texts, root):
    """Annotate each resource with used/orphan/keep + reason."""
    joined = "\n".join(t for _, t in texts)

    dynamic_re = re.compile(r"getIdentifier\s*\(|allDrawableResources|allStringResources")
    has_dynamic = bool(dynamic_re.search(joined))

    for r in resources:
        name = r["name"]
        r["refs_module"] = 0
        r["refs_repo"] = 0
        r["reason"] = ""

        if r["system"] == "assets":
            r["status"] = "keep"
            r["reason"] = "assets/ are loaded by runtime string path (locale/backend driven)"
            continue

        if r["system"] == "composeResources" and r["kind"] == "drawable":
            # `Res` is internal, so only a same-module reference can be real
            in_mod = name in by_module_tokens.get(r["module"], set())
            in_repo = name in all_tokens
            r["refs_module"] = int(in_mod)
            r["refs_repo"] = int(in_repo)
            if in_mod:
                r["status"] = "used"
            else:
                r["status"] = "orphan"
                if in_repo:
                    r["reason"] = "name collides with a resource elsewhere; no ref in its own module"
            continue

        if r["system"] == "composeResources":
            # files/ etc are loaded by exact path, so match the full filename
            stem = os.path.splitext(name)[0]
            n_full = len(re.findall(re.escape(name), joined))
            r["refs_repo"] = n_full
            r["refs_module"] = n_full
            if n_full:
                r["status"] = "used"
                continue
            sibling_used = any(
                o is not r
                and o["system"] == "composeResources"
                and o["kind"] == r["kind"]
                and os.path.splitext(o["name"])[0] == stem
                and re.search(re.escape(o["name"]), joined)
                for o in resources
            )
            if sibling_used:
                # the stem IS loaded by string, just via another extension. Lottie/json are
                # routinely swapped at the load site, so this is a judgement call, not a corpse.
                r["status"] = "keep"
                r["reason"] = (f"sibling '{stem}.*' with a different extension is the one "
                               f"referenced — confirm which format the loader wants")
            elif re.search(r'"[^"]*%s[^"]*"' % re.escape(stem), joined):
                r["status"] = "keep"
                r["reason"] = "stem appears in a string — path may be built dynamically"
            else:
                r["status"] = "orphan"
            continue

        # androidRes
        code_re = re.compile(r"\bR\.%s\.%s\b" % (re.escape(r["kind"]), re.escape(name)))
        xml_re = re.compile(r"@(?:\w+:)?%s/%s\b" % (re.escape(r["kind"]), re.escape(name)))
        n = len(code_re.findall(joined)) + len(xml_re.findall(joined))
        r["refs_repo"] = n
        r["refs_module"] = n
        if n:
            r["status"] = "used"
        elif has_dynamic and re.search(r'"%s"' % re.escape(name), joined):
            r["status"] = "keep"
            r["reason"] = "name appears as a string literal and getIdentifier() is used somewhere"
        elif quoted_re(name).search(joined):
            # lotties/json are loaded by name with the extension chosen at the call site,
            # so a bare quoted name is a live reference the R./@ patterns cannot see
            r["status"] = "keep"
            r["reason"] = "name appears in a quoted string — likely loaded by name at runtime"
        else:
            r["status"] = "orphan"

    return resources


def scan(root, search_roots):
    resources, res_dirs = collect_resources(root)
    sources = collect_sources(search_roots, res_dirs)
    by_mod, all_toks, texts = build_index(sources, root)
    return classify(resources, by_mod, all_toks, texts, root), len(sources)


def report(resources, n_sources, root):
    orphans = [r for r in resources if r["status"] == "orphan"]
    keeps = [r for r in resources if r["status"] == "keep" and r["system"] != "assets"]
    used = [r for r in resources if r["status"] == "used"]

    print(f"\nScanned {len(resources)} resource files against {n_sources} source files.")
    print(f"  used   : {len(used)}")
    print(f"  keep   : {len(keeps)}  (soft signal — never auto-deleted)")
    print(f"  ORPHAN : {len(orphans)}")

    if keeps:
        print("\n--- KEEP (soft signals) ---")
        for r in sorted(keeps, key=lambda x: (x["module"], x["name"])):
            print(f"  {r['module']:<12} {r['kind']:<10} {r['name']:<45} {r['reason']}")

    if orphans:
        by_mod = defaultdict(list)
        for r in orphans:
            by_mod[r["module"]].append(r)
        print("\n--- TRUE ORPHANS ---")
        for mod in sorted(by_mod):
            group = by_mod[mod]
            print(f"\n  [{mod}]  ({len(group)})")
            for r in sorted(group, key=lambda x: (x["kind"], x["name"])):
                note = f"   <- {r['reason']}" if r["reason"] else ""
                print(f"    {r['kind']:<10} {os.path.relpath(r['path'], root)}{note}")
    return orphans


def delete(orphans, root):
    if not orphans:
        return 0
    paths = sorted({r["path"] for r in orphans})
    rc = subprocess.run(
        ["git", "rm", "-q", "--"] + paths, cwd=root,
        capture_output=True, text=True,
    )
    if rc.returncode != 0:
        # fall back for untracked files
        for p in paths:
            try:
                os.remove(p)
            except OSError:
                pass
        print(f"  (git rm reported: {rc.stderr.strip()[:200]})")
    return len(paths)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=DEFAULT_ROOT, help="KMP repo whose resources are scanned")
    ap.add_argument("--search-root", action="append", default=[],
                    help="extra root to search for references (repeatable)")
    ap.add_argument("--delete", action="store_true", help="git rm orphans, looping until converged")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = os.path.abspath(args.root)
    search_roots = [root] + [os.path.abspath(p) for p in args.search_root]

    resources, n_sources = scan(root, search_roots)

    if args.json:
        print(json.dumps(resources, indent=2))
        return

    orphans = report(resources, n_sources, root)

    if not args.delete:
        if orphans:
            print(f"\nRe-run with --delete to git rm these {len(orphans)} files (cascade-safe).")
        return

    total = 0
    round_no = 0
    while True:
        round_no += 1
        n = delete(orphans, root)
        total += n
        print(f"\n[round {round_no}] deleted {n} file(s)")
        if n == 0:
            print(f"converged at 0 — total deleted: {total}")
            break
        resources, _ = scan(root, search_roots)
        orphans = [r for r in resources if r["status"] == "orphan"]
        if not orphans:
            print(f"converged at 0 — total deleted: {total}")
            break
        print(f"[round {round_no}] cascade surfaced {len(orphans)} newly-orphaned file(s)")


if __name__ == "__main__":
    sys.exit(main())
