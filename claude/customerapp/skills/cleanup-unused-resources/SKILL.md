---
name: cleanup-unused-resources
description: Use when finding or removing unused (orphan) resource FILES anywhere in the Porter monorepo — customerApp Android res/ (drawables, layouts, raw/lottie, anim, color, mipmap, menu, font, xml) AND customerapp-shared composeResources/ (Res.drawable, files/ lotties) — or re-validating a resource cleanup. Triggers: 'unused resources', 'orphan drawables/layouts', 'dead resource files', 'dead composeResources', 'clean up res/', 'unused lotties', or re-checking after deleting layouts/drawables.
trigger: /cleanup-unused-resources
---

# cleanup-unused-resources

One skill, one command, **both repos**. Lives in the **customerApp** repo (so it's versioned and
shared with the team) but scans customerApp *and* customerapp-shared, because the two
cross-reference each other's resources — neither can be scanned correctly in isolation.

```bash
cd <path>/customerApp

python3 .claude/skills/cleanup-unused-resources/scan.py                    # report, both repos
python3 .claude/skills/cleanup-unused-resources/scan.py --target shared    # customerapp-shared only
python3 .claude/skills/cleanup-unused-resources/scan.py --target app       # customerApp only
python3 .claude/skills/cleanup-unused-resources/scan.py --delete           # git rm + cascade loop
python3 .claude/skills/cleanup-unused-resources/scan.py --json
```

`--delete` uses `git rm` (staged, **never commits**). Unknown flags pass through to the engine.
Any cwd works — paths resolve from the script's own location, not the shell's.

## Layout assumption: the two repos are siblings

```
<workspace>/
  customerApp/            <- skill at customerApp/.claude/skills/cleanup-unused-resources/
  customerapp-shared/     <- resolved as ../customerapp-shared
```

`customerapp-shared` is found at **`../customerapp-shared`** relative to the customerApp repo
root. That is safe to assume: the composite build (`includeBuild`) requires the two to be
siblings — the project does not build otherwise. It's still checked, with an explicit error
rather than a silent "everything is orphaned" if the sibling is missing.

Nothing is hardcoded to one machine: `scan.py` derives the repo roots from `__file__`, and both
engines' own defaults do the same, so a fresh clone works with no edits.

## Two engines, because the reference models differ

| Engine | Target | Resource → reference form |
|---|---|---|
| `scan_android_res.py` | `customerApp/app/src/main/res` | `R.<type>.x`, `@<type>/x`, `@{…x…}`, `<Name>Binding` |
| `scan_compose_res.py` | `customerapp-shared/**/composeResources` + that module's `androidMain/res`, `assets` | `Res.drawable.x`, `Res.readBytes("files/x.lottie")`, plus `R.`/`@` for its android res |

`scan.py` just dispatches with the right roots. **Never point the Android engine at
`composeResources/`** — it has no concept of `Res.drawable.*` and would call every compose
drawable dead.

## Why it must scan across repos

Each engine gets the *other* repo as a reference-search root (`customerApp` ↔
`customerapp-shared`). That is not belt-and-braces, it is required:

**`customerapp-shared/shared/src/androidMain/res/font/` is the product's only font dir.**
Every reference to it is an `@font/lato_bold` inside a **customerApp** layout. Scan
`customerapp-shared` alone and all 11 `.ttf`s look dead.

**The iOS repo is deliberately excluded.** It cannot hold a real reference to anything either
engine owns — `Res` is `internal`, so a Swift `Image("ic_foo")` is the iOS asset catalog's own
resource that merely shares a name. Adding it as a search root only manufactures false
name-collisions and false soft-KEEPs (it was the source of several in the first sweep).

## The rules that make it correct

**1. `composeResources` is module-scoped — `Res` is `internal`.**
The generated accessor is `internal object Res`, so `booking`'s `Res.drawable.ic_price_drop`
is invisible to every other module. If the name appears elsewhere it is a **different resource
that happens to share the name** — e.g. customerApp's own `@drawable/ic_price_drop`. Not a
reference. The engine flags it `name collides with a resource elsewhere` and still calls it an
orphan. (This is also why the iOS repo is not scanned — every hit there is this false kind.)
Corollary: when two shared modules hold the same name, only the copy in the module that
actually references it survives (`ic_retry_20x20` is in both `booking` and `profile`; only
`booking` uses it).

**2. Android `res/` cascades; composeResources does not.**
A selector/layer-list drawable or a layout `<include>` keeps its children alive, so the first
scan sees the child as referenced. Deleting the parent orphans the child — only a re-scan
*after* deletion surfaces it. `--delete` loops until `converged at 0`; that line is the
guarantee there is no hidden second batch. Compose drawables never reference each other, so
that half normally converges in round 1.

**3. A resource is a TRUE ORPHAN only if it has none of these.**

| Signal | Form | Notes |
|---|---|---|
| Code ref | `R.<type>.<name>` / `Res.drawable.<name>` | |
| XML ref | `@<type>/<name>` | incl. from other drawables/layouts (cascade source) |
| Data-binding | `@{ … name … }` | |
| ViewBinding | `<CamelCase>Binding` | layouts only; word-boundary, no substring traps |
| Dynamic | `getIdentifier(… "<name>" …)` | backend-driven; KEEP |
| Asset dup | `assets/` file w/ same stem | res/raw lottie loaded by string → KEEP |
| String/path | `"<name>"` in any quoted string | KEEP |
| Same-stem sibling | `<stem>.json` ↔ `<stem>.lottie` | the stem *is* string-loaded → KEEP, human decides |

The last four are **soft signals → reported as `KEEP`, never auto-deleted.** Word-boundary
matching on the *reference form* is what makes `checkbox`/`delete`/`star` safe while still
protecting string-loaded lotties like `coin_rotation`.

## Workflow

1. **Report first.** Read the `KEEP` list and every `<- reason` note on the orphans — those are
   the only judgement calls.
2. **Verify independently.** Don't trust one scan. Re-grep each orphan against its *owning
   module's* sources (short `os.walk` loop, excluding `build/` and the resource dirs). Expect
   zero. This is what lets you delete 60+ files without a build.
3. **`--delete`**, wait for `converged at 0`.
4. **Check blast radius:** `git status --short | grep -v '^D '` — no unexpected edits.
5. **`values/` sweep (optional, customerApp).** Strings/colors/dimens aren't files, so lint owns
   them. Report tasks are skipped by project config and lint needs JDK 17 (Kotlin tasks use 21):
   `export JAVA_HOME=/Library/Java/JavaVirtualMachines/jdk-17.jdk/Contents/Home`
   `./gradlew :app:lintPorterProductionDebug -Dorg.gradle.java.home="$JAVA_HOME"`
6. Commit/PR only when explicitly asked (`/raise-pr`).

## Gotchas

- **`getIdentifier()` bridge is load-bearing.** `MarkerIconResourceHelper.android.kt` maps
  `Res.drawable.ic_pick_up_marker` → `getIdentifier("ic_pick_up_marker", …)`, resolving against
  `booking/src/main/res/drawable/`. Those Android copies have no `R.`/`@drawable/` ref but are
  required. The engine soft-KEEPs any android res whose bare name appears as a string literal
  while `getIdentifier` exists in the corpus.
- **Lottie/JSON are loaded BY NAME — never auto-delete a same-stem sibling.** Match the full
  filename to decide *referenced*, but when only a sibling extension is referenced
  (`vehicle_selection_loader.json` is loaded, `.lottie` sits beside it) the stem is still a
  live string at the load site. The extension is chosen at the call site and swapping it is a
  one-line change, so the engine reports these as **`KEEP`, not orphan** — a human confirms
  which format the loader wants. Deleting on the scanner's word here is the one way this skill
  can break a screen without any reference disappearing.
- **`src/main/res` vs `src/androidMain/res`.** customerapp-shared uses both (`booking` uses
  `src/main/res`). Both engines accept either.
- **`git log -S` (pickaxe) lies** about when a reference died — it counts the bare string in any
  file, including ones being deleted. Use the scanner's reference counting.
- **Multi-density files:** `--delete` removes every density/config variant of a name.
- **`assets/localization/*.json`** in shared are locale-selected at runtime → always KEEP.
- Don't run Gradle to "verify" unless asked; step 2's grep is the check.

## Last runs

- **2026-08-10 · customerapp-shared** (MOB-12162, shared PR #6770) — 460 resource files →
  **61 deleted**, 374 used. booking 27, shared 19, profile 9, onboarding 5, payments 1.
  Re-scan after deletion: 399 files, **0 orphans**, 1 KEEP. customerApp scanned the same day:
  1437 ids, **0 orphans** — already clean, so no PR there.
  This run is why the same-stem rule changed: `vehicle_selection_loader.lottie` was reported as a
  hard orphan, and the user held it back because lottie/json are loaded by name. The engine now
  soft-KEEPs that case instead of deleting it.
- **2026-08-07 · customerapp-shared** — same 62-file sweep, never committed (branch discarded);
  superseded by the run above.
- **customerApp** — 167 `res/` files deleted in an earlier sweep; re-validate lottie + ViewBinding
  signals when re-running.
