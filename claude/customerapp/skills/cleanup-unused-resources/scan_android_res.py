#!/usr/bin/env python3
"""Find unused file-per-resource entries in an Android module. See SKILL.md for the rules.

  scan_android_res.py [--repo PATH] [--res PATH] [--assets PATH] [--delete] [--json]

Normally driven by scan.py; run directly only to target a different module. Covers
drawable/layout/raw/color/anim/animator/mipmap/menu/font/xml — values/ needs
`lint UnusedResources` instead. --delete re-scans until convergence, since deleting a
selector or <include> parent orphans children the first pass saw as referenced.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

FILE_TYPES = {"drawable","layout","raw","color","anim","animator","mipmap","menu","font","xml"}
SKIP = ("/build/","/.git/","/.gradle/","/.idea/","/.kotlin/")
SRC_GLOBS = ("*.kt","*.java","*.xml","*.gradle","*.kts","*.pro")
RES_EXT = re.compile(r"\.(png|webp|jpg|jpeg|xml|json|gif|ttf|otf|svg|lottie|mp3|mp4|wav|riv)$")

camel = lambda n: "".join(w.capitalize() for w in n.split("_"))

def stem_of(name):
    return name[:-6] if name.endswith(".9.png") else RES_EXT.sub("", name)

def enumerate_resources(res_dir):
    res = {}  # (type,name) -> [Path]
    for p in res_dir.rglob("*"):
        if not p.is_file(): continue
        t = p.parent.name.split("-")[0]
        if t not in FILE_TYPES: continue
        res.setdefault((t, stem_of(p.name)), []).append(p)
    return res

def build_corpus(repo, cache):
    """Return [(path,text)], reusing cached reads; drop files that vanished."""
    corpus = []
    seen = set()
    for g in SRC_GLOBS:
        for p in repo.rglob(g):
            sp = str(p)
            if any(s in sp for s in SKIP): continue
            seen.add(sp)
            if sp not in cache:
                try: cache[sp] = p.read_text(encoding="utf-8", errors="ignore")
                except Exception: cache[sp] = ""
            corpus.append((sp, cache[sp]))
    for gone in set(cache) - seen:   # purge deleted files from cache
        cache.pop(gone, None)
    return corpus

def asset_stems(assets_dir):
    if not assets_dir.exists(): return set()
    return {p.stem for p in assets_dir.rglob("*") if p.is_file()}

def has_resref(t, n, corpus, self_paths):
    pats = [re.compile(r"\bR\."+re.escape(t)+r"\."+re.escape(n)+r"\b"),
            re.compile(r"@"+re.escape(t)+r"/"+re.escape(n)+r"\b"),
            re.compile(r"@\{[^}]*\b"+re.escape(n)+r"\b[^}]*\}")]
    if t == "layout":
        pats.append(re.compile(r"\b"+re.escape(camel(n)+"Binding")+r"\b"))
    for path, txt in corpus:
        if path in self_paths: continue
        for pat in pats:
            if pat.search(txt): return True
    return False

def soft_signals(n, corpus, astems, self_paths):
    reasons = []
    gi = re.compile(r"getIdentifier\s*\([^)]*"+re.escape(n))
    if any(gi.search(txt) for _, txt in corpus): reasons.append("getIdentifier")
    if n in astems: reasons.append("assets/ dup")
    q = re.compile(r"""["'][^"']*\b"""+re.escape(n)+r"""\b[^"']*["']""")
    for path, txt in corpus:
        if path in self_paths: continue
        if q.search(txt): reasons.append("quoted-string/path"); break
    return reasons

def detect(repo, res_dir, assets_dir, cache):
    resources = enumerate_resources(res_dir)
    corpus = build_corpus(repo, cache)
    astems = asset_stems(assets_dir)
    true_orphans, keep = [], []
    for (t, n), paths in sorted(resources.items()):
        sp = {str(x.resolve()) for x in paths}
        if has_resref(t, n, corpus, sp):
            continue
        reasons = soft_signals(n, corpus, astems, sp)
        (keep if reasons else true_orphans).append((t, n, paths, reasons))
    return resources, true_orphans, keep

def git_rm(paths, repo):
    for p in paths:
        subprocess.run(["git","rm","-q",str(p)], cwd=repo,
                       capture_output=True, text=True)

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    default_repo = str(Path(__file__).resolve().parents[3])  # the customerApp repo
    ap.add_argument("--repo", default=default_repo,
                    help="repo root scanned for references (default: the customerApp repo "
                         "this skill lives in)")
    ap.add_argument("--res", default=None, help="res dir (default: <repo>/app/src/main/res)")
    ap.add_argument("--assets", default=None, help="assets dir (default: <repo>/app/src/main/assets)")
    ap.add_argument("--delete", action="store_true",
                    help="git rm true orphans and loop until convergence (cascade-safe)")
    ap.add_argument("--json", action="store_true", help="emit JSON summary")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    res_dir = Path(args.res).resolve() if args.res else repo/"app/src/main/res"
    assets_dir = Path(args.assets).resolve() if args.assets else repo/"app/src/main/assets"
    if not res_dir.exists():
        sys.exit(f"res dir not found: {res_dir}")

    cache = {}
    rounds = []
    while True:
        resources, true_orphans, keep = detect(repo, res_dir, assets_dir, cache)
        rounds.append(true_orphans)
        if not args.json:
            rnd = len(rounds)
            print(f"\n{'='*72}\nROUND {rnd}  —  {len(resources)} resource ids scanned")
            print(f"TRUE ORPHANS: {len(true_orphans)}    FLAGGED-BUT-KEEP: {len(keep)}")
            for t, n, paths, _ in true_orphans:
                print(f"  ✗ {t}/{n}  ({len(paths)} file{'s' if len(paths)>1 else ''})")
            if rnd == 1 and keep:
                print("  -- kept (soft signal, NOT deleted): --")
                for t, n, _, reasons in keep:
                    print(f"  • {t}/{n}  <- {', '.join(reasons)}")
        if not args.delete or not true_orphans:
            break
        flat = [p for _, _, paths, _ in true_orphans for p in paths]
        git_rm(flat, repo)
        if not args.json:
            print(f"  -> git rm staged {len(flat)} files; re-scanning for cascade...")

    if args.json:
        print(json.dumps({
            "rounds": len(rounds),
            "deleted_ids": [f"{t}/{n}" for rnd in rounds for t,n,_,_ in rnd] if args.delete else [],
            "true_orphans_final_round": [f"{t}/{n}" for t,n,_,_ in rounds[-1]],
            "kept": [f"{t}/{n}: {','.join(r)}" for t,n,_,r in keep],
        }, indent=2))
    else:
        total = sum(len(r) for r in rounds)
        print(f"\n{'='*72}")
        if args.delete:
            print(f"DONE — staged {total} orphan ids over {len(rounds)} round(s); converged at 0.")
            print("Review with `git diff --cached --stat`. Nothing committed.")
        else:
            print(f"REPORT ONLY — {len(rounds[0])} true orphans found (run with --delete to remove).")
            print("Note: values/ resources (strings/colors/dimens/styles) need `lint UnusedResources`.")

if __name__ == "__main__":
    main()
