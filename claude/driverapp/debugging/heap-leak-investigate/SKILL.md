---
name: heap-leak-investigate
description: Investigate a leak surfaced by the heap-dump digest — pull the dump's retention evidence with the devtool, scan the codebase for the root cause, and produce a hypothesis with evidence and a fix suggestion. Use when given a dump uid, a digest line, or suspect class names from the #heap-dump digest channel.
---

# Heap-Leak Investigation

Turn a digest suspect line into a root-cause hypothesis by combining the
dump's retention evidence with a codebase scan. This encodes the investigation
methodology from the 2026 fleet analysis (findings #1–#16); the pipeline and
its devtool live in `tools/heap-dump-pipeline/` (see its README for how the
digest is built).

## Inputs

Accept any of: a dump uid, a pasted digest line, or bare suspect class names.

1. **Get the dump's evidence** with the devtool (needs `gcloud auth login` for
   fleet dumps; see `tools/heap-dump-pipeline/README.md`):

   ```bash
   python3 tools/heap-dump-pipeline/devtool.py analyze <uid>      # digest facts + top-3 retention chains
   python3 tools/heap-dump-pipeline/devtool.py trace <class>      # retention chain for any other class
   python3 tools/heap-dump-pipeline/devtool.py retainers <class>  # who holds the instances (owner × field)
   python3 tools/heap-dump-pipeline/devtool.py resolve <name>     # obf↔clear lookup + R8-merge check
   ```

   The run's per-dump summary JSONs are also uploaded as the workflow-run
   artifact `summaries-<run_id>` (linked from the digest) if you'd rather read
   than re-analyze. The part rows (`by_retained`/`by_shallow`/`by_instances`,
   counts + retained MB) and the retention chains (dominator hops with field
   names) are the primary evidence. Counts matter more than sizes: N objects
   of class X at exactly the same count as class Y implies a shared
   construction site.

2. **Trust the names before accusing.** Run `resolve <class>` on every class
   you are about to blame: an `R8-merged ×N` answer means instances of that
   runtime class may belong to any of the merged siblings — corroborate with
   `retainers` structure (owner classes, field names) before naming a team's
   class. Rows the digest already flags `R8-merged` / "mapping mismatch?" are
   excluded from suspects for exactly this reason.

3. **Locate the suspect classes.** For each non-JDK class in the evidence:
   find the source (this repo, or flag it as kmp-utils / third-party — for
   kmp-utils check `~/StudioProjects/kmp-utils` if present). Note the module
   and who constructs it (search `@Inject`, `@Provides`, `by lazy`, direct
   constructor calls).

## Pattern checklist (check in this order — they cover findings #1–#16)

For each pattern: run the grep, and if it hits, read the surrounding code
before concluding. Presence of a pattern is a lead, not a verdict.

| # | Pattern (finding precedents) | What to grep for on the suspect + its retainers |
|---|---|---|
| 1 | **Unscoped DI construction** (#6, #8, #16) | `@Inject constructor` on the class WITHOUT `@Singleton`/scope annotation; consumers holding `Provider<X>` and calling `.get()` inside loops/hot paths; `@Provides` without scope. Matching instance counts across classes = one unscoped binding fanning out. |
| 2 | **Undisposed subscription/collector** (#1, #2, #5, #10) | `launchIn(`, `.subscribe(`, `.collect {` inside `init {}`, `onAttachedToWindow`, `onViewAttached` — then check for the symmetric `cancel`/`dispose` in `onDetachedFromWindow`/`willResignActive`/`onCleared`. Also `registerForActivityResult` collectors on Activity-scoped flows. |
| 3 | **Unbounded static cache/pool** (#2, #11) | `companion object` / `static` fields holding collections (`LongSparseArray`, `HashMap`, pools); Epoxy `UnboundedViewPool`; caches with no eviction (`LruCache` absent where a map grows per item). |
| 4 | **Unbounded queue / missing backpressure** (#3, #12, #13, #14) | `Channel(` with `UNLIMITED`/no capacity; `LinkedBlockingQueue` producers with no consumer-failure handling; per-event `launch {}` that enqueues; executors wrapping unbounded queues (`LimitedConcurrencyExecutor` pattern). |
| 5 | **Lock convoy on per-event path** (#15) | `Mutex(`, `withLock`, `Semaphore(` inside functions called per analytics/log/network event; suspending callers that pile up (`CancellableContinuationImpl` count ≈ backlog size). |
| 6 | **Wrong-scope CoroutineScope** (#5, #10) | `GlobalScope`, `MainScope()`, `CoroutineScope(Dispatchers.` constructed in Views/RIBs/handlers without lifecycle-bound cancel; `CoroutineScope by` delegation on views. |
| 7 | **Static GC-root pinning** (#2 phoenix.au) | In the retention chain: a `Class<...>` or `*ClassLoader` at the top with a library-owned static (`phoenix`, `zz*`, `m140.*`) — often third-party; fix is teardown calls (`onDestroy`) not Porter-side scoping. |

If none of the seven hit, reason from first principles on the retention
chain: who is the lowest NOT_LEAKING node, what field points down, and what
code writes that field? A genuinely novel mechanism (cf. the dd-sdk
`PendingTrace` hashCode bug, finding #16) is found by explaining why the
*removal/cleanup* path can't run, not by pattern lookup.

## Cross-checks before concluding

- Check earlier digests in the channel (and open MOB tickets) — a recurring
  suspect at similar magnitude is an existing leak resurfacing, not a new one.
- Check instance-count ratios between the flooding classes (constant ratios =
  same codepath; state the arithmetic).
- If the suspect is in kmp-utils or a third-party SDK, say so explicitly —
  the fix lands in a different repo (note the fork/version pinning, e.g.
  `in.porter:dd-sdk-android` fork, kmp-utils composite build).

## Output format

```
## Hypothesis
<one paragraph: mechanism, why instances accumulate, why cleanup never runs>

## Evidence
- heap: <counts/MB/ratios from the summary + trace hops that matter>
- code: <file:line references from the greps, quoted minimally>

## Suggested fix
<concrete: annotation/scope change, dispose site, bounded queue, teardown call
— matching the codebase's existing patterns (RIB interactorScope, @Singleton)>

## Pattern-checklist addition (only if none of #1–#7 matched)
<draft bullet for the table above, so the next investigation catches this class of bug>
```

Confidence discipline: label the hypothesis high/medium/low. If the evidence
supports two mechanisms, present both with a discriminating experiment (a
grep, a debug-build probe, or a devtool `trace`/`retainers` query) rather
than picking one by fiat.
