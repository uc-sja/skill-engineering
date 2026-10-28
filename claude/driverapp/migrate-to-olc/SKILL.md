---
name: migrate-to-olc
description: Migrate one legacy DriverAppV3 order-flow unit (a RIB under shared/.../orderflow/) into the OLC 2.0 library as a journey screen, at 100% behavioural parity. Use when asked to "port X to OLC", "migrate X to OLC 2.0", or "OLC-ify" an order-flow screen. Excludes unit/screenshot tests (separate skill); Maestro parity flows are in scope.
---

You are migrating **one** legacy order-flow unit from DriverAppV3 (RIBs + Dagger + flux) into the
OLC 2.0 library (Compose Multiplatform + kotlin-inject + Compose Navigation).

**The objective of a migration is 100% behavioural parity with legacy.** Parity is the default and
the tie-breaker. Anything that reduces, extends, or reshapes legacy behaviour — whether the LLD says
so, or the target repo's structure leaves no home for it — is a **divergence**, and divergences are
**not yours to decide**. See [STOP GATES](#stop-gates). This is the single most important rule in
this skill; the rest is mechanics.

Unit and screenshot tests are **out of scope** — a separate skill covers them. Do record, in the
ledger, which legacy tests describe behaviour you ported. **Maestro parity flows are in scope**, and
are how the parity claim gets checked: see [Phase 6](#phase-6).

---

## READ THIS FIRST — the module is no longer a scaffold

The pre-end-trip journey (order entry → the waypoint loop → end-trip confirmation) has **landed**:
~37 000 lines across four PRs, a state machine, snapshot persistence, background replay, typed
analytics, host-provided strings and flags, and a 103-flow Maestro suite.

Three consequences for how you work:

1. **Most of what this skill used to call a missing seam now exists.** `OlcStringsProvider`,
   `OlcFeatureFlagProvider`, `OlcConfigs`, `OlcAnalyticsManager`, the throttle, the full-screen
   loader, the state manager, phase→route dispatch — all real. Adding to one is usually a
   **15-line edit to an existing port, not a deferral**. Check before you defer.
2. **Your unit probably does not get a new screen.** Legacy units map onto *sections* of an existing
   screen, *dialog destinations*, or *phases of the state machine* at least as often as onto new
   routes. Establish which before you design anything.
3. **There is a reference migration to copy, not just a template to fill.** Read
   `references/worked-example-pre-end-trip.md` before Phase 2.

Re-measure rather than trusting these claims — including the ones in these files. The target repo
moves weekly, and its own harness README is currently stale in two places (see
`references/maestro-parity.md`).

### The reference files

| File | Read it when |
|---|---|
| `references/target-map.md` | Phase 2 onward. The full legacy→OLC mapping, DI templates, screen anatomy, section tiers, the coordinator, taps/throttle, analytics, navigation, persistence, conventions. |
| `references/worked-example-pre-end-trip.md` | Before Phase 2. The `orderwaypoint` migration end to end, its 4-PR slicing, and the stop gates it closed. |
| `references/maestro-parity.md` | Phase 0 (for ledger heading 14) and Phase 6. Test-tag rules, the harness, and how a copied flow proves parity. |
| `references/host-stitch.md` | Only when your unit needs something new from DriverAppV3. |

---

## THE THREE REPOS

| Role | Repo | Path | Stack |
|------|------|------|-------|
| **SOURCE** (legacy) | `DriverAppV3` | `~/AndroidStudioProjects/DriverAppV3` | RIBs, Dagger, flux `BaseStateVMInteractorV2`, RxJava2 + coroutines, XML + Compose |
| **TARGET** (library) | `porterin/order-system` → `order-management-main` | `~/AndroidStudioProjects/order-management-main` | CMP, kotlin-inject, Compose Navigation, Ktor, coroutines only |
| **HOST** (adapters) | `DriverAppV3` again | `app/src/main/java/com/theporter/android/driverapp/order/olc/` | Dagger module bridging host services into the OLC contract |

Target source root (`$OLC` below) — note the **nested** directory:

```
$OLC = order-management-main/frontend/mobile/mobile-driver-olc/mobile-driver-olc/src/commonMain/kotlin/in/porter/olc/mobile/driver/
```

`kinar/mobile-driver-olc` is a **stale decoy clone**. It yields false "not implemented" verdicts.
The live module is the one above.

**Step 0 of every run:** verify both paths exist and print the target's branch + SHA. If the target
checkout is missing or at a different path, **ask** — do not guess, and do not attempt the migration
inside DriverAppV3.

---

## WORKFLOW

```
0. Orient       → confirm repos + SHA, locate the unit, read the LLD, find its target home
1. Inventory    → build the Parity Ledger from LEGACY ONLY
2. Map          → assign every ledger row a target home
3. Stop gates   → batch every conflict to the user; record decisions
4. Implement    → write code in dependency order, sliced by layer
5. Verify       → walk the ledger; report
6. Prove        → copy legacy's Maestro flows and run them
```

Phases 1 and 3 are where the value is. Do not rush them to get to code.

---

## PHASE 0 — ORIENT

1. **Resolve the legacy unit.** Shared logic:
   `shared/src/commonMain/kotlin/in/porter/driverapp/shared/root/loggedin/orderflow/<unit>/`.
   Android shell: `app/src/main/java/com/theporter/android/driverapp/ribs/root/loggedin/orderflow/<unit>/`.
   Layout: `app/src/main/res/layout/rib_<unit>.xml`. **Read all three.** The shell holds behaviour the
   shared module does not (view binding, keyboard, back handling, child attach points), and the
   layout holds the *order* of things and the test ids.
   - If the layout contains a `ComposeView`, the unit is **already half-migrated**. Find out which
     half actually renders in each VM variant before you reason about anything from the XML — the
     dead half is still in the file.
2. **Read the LLD** section for this unit (Notion, *"Partner App OLC 2.0 Docs"*). If you cannot
   reach it, say so and proceed from legacy + repo, flagging that LLD reconciliation is unverified —
   do not silently skip it.
3. **Read the target.** In this order: the module `README.md`, `docs/2026-09-21-maestro-test-tag-naming.md`,
   `references/target-map.md` in this skill, then the neighbouring screen most like your unit.
4. **Decide the target home — this is a Phase-0 question, not a Phase-2 one.** One legacy RIB maps
   onto exactly one of:

   | If the legacy unit… | its home is |
   |---|---|
   | is a full screen the driver navigates to | a `journeyRoute<>` destination under `screens/<x>/` |
   | is a modal/overlay over another screen | a `journeyDialog<>` destination, or a `ModalBottomSheet` in the parent's `ui/` |
   | is a child RIB attached into a region of a parent screen | a **section** under `screens/<parent>/sections/<x>/` |
   | is a lifecycle step with no UI of its own | a phase on `OlcState` + a `render()` arm |
   | splits by `source`/version into two purposes | two screens (the `collectotp`/`collectotpv2` → `starttripotp`/`endtripotp` precedent) |
   | is always on screen alongside whatever else is | a permanently-mounted surface, like `OrderDetail` in the drawer — **not** a route |

   If the scaffold's shape contradicts the LLD, the scaffold usually wins (it encodes later
   decisions) — but that is a STOP GATE, not your call.
5. **Ask the params question early**: can the state hub answer what this screen needs? If yes its
   `Params` is an `object`. Only a fact that arrived with a push and must survive a process death
   becomes a route argument.

---

## PHASE 1 — THE PARITY LEDGER

The ledger is the deliverable that makes parity checkable. Build it from **legacy only** — do not
look at the target while writing it, or you will inventory what is easy to port instead of what
exists.

Write it to `docs/olc-migration/<unit>-parity-ledger.md` **in DriverAppV3**. It stays in the legacy
repo because that is where the behaviour it describes lives. Two worked ledgers already exist there
(`collectotp-parity-ledger.md`, `tripdetails-contact-block-parity-ledger.md`) — match their format.

Enumerate under these **16** headings. Every row needs a `file:line` citation; a row without
evidence is a guess.

| # | Heading | What to capture |
|---|---|---|
| 1 | **Params** | Every field of `<Unit>Params`, and whether the interactor *actually reads it*. Unused params are rows too (status: Dropped). Note any field that is a repo or a `Flow` — those become seams, not params. |
| 2 | **State** | Every field of `<Unit>State` + its initial value from the reducer's `initState`. |
| 3 | **UI events** | Every member of `<Unit>Presenter` — streams *and* imperative methods (`centreMap(...)`). |
| 4 | **Handlers** | Every `inner class …Handler` and every branch inside it. One row per *branch*. |
| 5 | **Network** | Endpoint path, which client (OMS vs Gateway), request/response DTOs, **every `@SerialName`**, the error-response type and each error enum value, custom timeouts, retry/WorkManager enqueue. |
| 6 | **VM mapping** | Every predicate in `<Unit>VMMapper` and its helpers. Transcribe the boolean expressions **verbatim**; they are where parity quietly dies. If the VM is a sealed tree (V1/V2), capture the discriminator. |
| 7 | **Strings** | The `ViewStrings` class, the vernac key, and the **actual current values** from `app/src/main/assets/vernac/english_strings.json`. Note `#argN` placeholders. |
| 8 | **Analytics** | Every `track*`: event **type** (`ImpressionEvent`/`ActionEvent.Click`/`ActionEvent.Swipe`/`StateEvent`/legacy), identifier, `stateEventName`, attributes — including the base map passed to `FeatureAnalytics(...)`. |
| 9 | **Constants** | Every magic number and `companion object` constant. |
| 10 | **Children** | Every `router.attachX/detachX`, what the child does, and **which ViewGroup it attaches into** (that is the section boundary). |
| 11 | **Listener** | Every method on `<Unit>Listener` and exactly when each fires. |
| 12 | **Flags & config** | Every `RemoteConfigRepo` / `AppConfigRepo` / Statsig read. Split **gates** (→ `OlcFeatureFlagProvider`) from **numbers** (→ `OlcConfigs`), and record each one's code default. |
| 13 | **Cross-cutting** | `fullScreenLoader.showWhile`, `exponentialThrottleUseCase` / `GetFlowWithThrottleFirst`, `uiUtility.hideKeyboard()`, IME actions, back handling, `Dispatchers.Main` hops, error toasts. |
| 14 | **Test ids** | Every `@+id/` in the layout and every `setTestResourceId` — and how many of #7955's Maestro flows select on each. This decides the tag values; see `references/maestro-parity.md`. |
| 15 | **Persistence** | Anything that must survive process death or must happen **once per order** (a `var` in legacy is often a bug that a relaunch hides). |
| 16 | **Known bugs / dead paths** | Behaviour that is clearly wrong or unreachable. Do **not** decide to fix or preserve — flag it. |

Row format:

```markdown
| ID | Legacy behaviour | Evidence | Target home | Status | Decision |
|----|------------------|----------|-------------|--------|----------|
| N-03 | verify_otp POSTs `{otp_request_source, order_id, otp}` to Gateway `orders/verify_otp` | CollectOtpService.kt:26 | LiveOrderClient.verifyEndTripOtp | Ported | — |
```

`Status` ∈ `Ported` · `Divergence` · `Deferred` · `Dropped`. Only `Ported` needs no decision
reference; the other three **must** cite an approved entry in the Divergence Register.

---

## PHASE 2 — MAPPING LEGACY → OLC

Assign every ledger row a target home. **The full mapping table, the DI templates, the screen
anatomy, the section split, the coordinator pattern, analytics, navigation and persistence are in
`references/target-map.md`.** Read it now.

The architectural shift, in one line: *the flux Interactor's orchestration collapses into a
ViewModel plus a Coordinator; the VMMapper becomes a pure top-level mapper function; the children
become sections; the Listener becomes a state-machine dispatch.*

---

## STOP GATES

> **Parity is the objective. When legacy says one thing and the LLD or the target repo says another,
> you stop and ask. You do not resolve it yourself, and you do not silently ship the target's
> version because it was easier to write.**

### When to stop

- **A. The LLD contradicts legacy.** It models fewer/different states, results, or steps than legacy
  produces. *(The LLD's flat `{Verified, Invalid}` OTP result vs legacy's third state,
  `RetryLimitExhausted`, which drives a lockout and a support fallback.)*
- **B. The target repo has no home for a legacy behaviour** — **and you have checked that it really
  doesn't.** Before raising a B, confirm: is there a `fun` you could add to `OlcFeatureFlagProvider`?
  A field on `OlcConfigs`? An accessor on `OlcStringsProvider`? A `contract/resources` data class?
  A section package? Most former Bs are now one of those. A genuine B is a *shape* the module
  cannot express — not a member it happens not to have yet.
- **C. The target repo contradicts the LLD.** *(The repo's two-screen OTP split vs the LLD's single
  `Otp(source)` screen.)*
- **D. Legacy behaviour is a bug, dead path, or clearly unintended.** Porting bugs faithfully and
  fixing them are both defensible; picking is a product call. *(`collectotp` V1 logs its submit event
  as `btn_otp_cancel`.)*
- **E. A legacy affordance crosses OLC's boundary.** Post-trip screens (payment, rating, thank-you),
  the host's cancellation sheet, host chrome (`drawer_opener`, `recenterBtn`). These are not gaps to
  fill — they are the handback, and the question is whether the handback is in the right place.
- **F. A behaviour depends on infrastructure that genuinely does not exist yet.** This is `Deferred`,
  and *deferral is still a decision the user makes*, because it determines whether the screen ships.

### How to stop

Do **not** interrupt once per finding. Collect conflicts as you go and raise them in batched rounds
(up to 4 per round via `AskUserQuestion`), at the end of Phase 1 and again at the end of Phase 2.
For each conflict, in this order:

1. **What legacy does**, with the `file:line` citation and the concrete user-visible effect.
2. **What the LLD / repo says instead**, cited.
3. **Options**, each with its parity cost.
4. **Your recommendation**, in one line, with the reason.

Then wait. Do not start writing the affected code while the question is open — do the unaffected
work instead.

### After the answer

Record it in a **Divergence Register** at the bottom of the ledger. Never leave a decision only in
the chat:

```markdown
### Divergence Register

| ID | Legacy behaviour | Chosen behaviour | Rationale | Decided by | Date |
|----|------------------|------------------|-----------|------------|------|
| D-01 | Single OTP RIB with `source` param | Two screens: starttripotp + endtripotp | Start & end are different purposes; APIs differ | <manager>, ruling | 2026-08-13 |
```

Then flip the ledger row's `Status` and point it at the `D-nn`.

**A `Deferred` row must also leave a tagged marker in the code**, so the gap is greppable:

| Tag | Means |
|-----|-------|
| `TODO(HOST)` | needs something from the DriverAppV3 side |
| `TODO(strings)` | needs a `contract/resources` type or a host accessor |
| `TODO(SEAM)` | needs a journey-infra seam that does not exist |
| `TODO(PHASE2)` | post-trip; outside OLC's current boundary |

Write the *exact* code that will go in once the seam lands, as a comment. A deferral you can paste
in later is cheap; one you have to re-derive is not.

*(`TODO(LAYER-B)` is retired — the state manager and phase→route dispatch exist.)*

---

## PHASE 4 — IMPLEMENT

Write in dependency order so every file compiles against something real:

```
dto → mapper → client method → use case → state machine event
    → State (+ the pure mapper fn) → UIEvent → ViewModel → Coordinator
    → Section composables → Content → Screen → DI component
    → route registration → strings → flags/config → analytics → test tags
```

**Slice the PRs by layer, not by screen** — the reference migration shipped as
*contract+data+domain* → *shared UI foundation* → *screen content+state* → *VMs+DI+nav+host wiring*.
Each slice is reviewable on one axis. See `references/worked-example-pre-end-trip.md`.

Conventions are in `references/target-map.md` §9. The ones most often got wrong:

- Package escape `` `in` `` in **every** file and import.
- `me.tatarka.inject.annotations.Inject`, never `javax.inject`.
- Everything `internal` except `contract/`.
- `@SerialName` and analytics event names copied **verbatim**, with a comment saying why.
- Preserve the analytics event **type**, not just the name.
- Clients return domain types; DTOs never leave `data/`.
- A "once per order" rule needs a store in `data/persistence/`, not a `var`.
- `RecordException.invoke(e)` as well as the user-facing toast — reporting and displaying are two
  different obligations, and binding the error to `_` satisfies neither.

---

## PHASE 5 — VERIFY

1. **Walk the ledger top to bottom.** Every row is `Ported`, or cites an approved `D-nn`. Any row
   still blank means the migration is not done — say so plainly, do not round up.
2. **Re-read your own diff against the ledger predicates.** Silent divergences hide inside `copy()`
   calls and boolean expressions, not in missing files. Compare each branch of the mapper function
   against the legacy `VMMapper` expression character by character.
3. **Grep the new code** for `TODO(HOST|strings|SEAM|PHASE2)` and list every hit in the report.
4. **Re-measure anything you are about to tabulate.** Stamp branch@SHA. Never reuse a snapshot your
   own edits invalidated.
5. **Offer** to build — do not run builds unprompted.
6. **Write the migration report** to `docs/olc-migration/<unit>-report.md`: files added/changed,
   ledger counts by status, the Divergence Register, open TODOs with owners, and a one-line honest
   verdict on whether the screen is at parity today.

---

## <a id="phase-6"></a>PHASE 6 — PROVE IT WITH MAESTRO

A ledger is a claim. The suite is the check. **Full detail in `references/maestro-parity.md`** —
the short version:

1. **Tag the new surfaces with the legacy view ids, verbatim.** One `<X>TestTags.kt` per screen and
   per section. `testTagsAsResourceId` must be exported **once per window** — every dialog and
   bottom sheet is its own window, and the failure is silent.
2. **Measure id coverage** of the legacy flow folders that cover your unit, before judging any of
   them. A copied flow stops at its first missing id.
3. **Copy the flows**, keeping legacy's paths and `appId: ${APP_ID}` header. Write one by hand only
   where legacy has none.
4. **Add a fixture scenario folder** for each variant your unit needs — an overlay, not a copy.
   Assert something **only your scenario carries**, because an unknown scenario name silently falls
   through to the default data.
5. **Add the flows to a config and the config to `ci/device_jobs.txt`.** A flow runs iff a config
   names it.
6. **When a copy fails, the flow is usually right and OLC is usually wrong.** Do not loosen it.

---

## ANTI-PATTERNS

- Reading the target scaffold before inventorying legacy. You will port the shape, not the behaviour.
- "The LLD says X, so X." The LLD was written before the code; legacy is what ships to drivers today.
  When they disagree, that is a question, not an answer.
- Treating a missing seam as a reason to drop behaviour — **or** as a stop gate without first
  checking whether it is one `fun` on an existing port.
- Promoting a section to a nav route to give it a lifecycle. The DI scope does that.
- Adding a client because a new call "doesn't fit". Put it on the client whose scope it belongs to.
- Renaming analytics events, vernac keys, or `@SerialName` values while porting. Adding a new name
  *alongside* a legacy one is fine; replacing is a divergence.
- Flattening an `ImpressionEvent` or `ActionEvent.Swipe` into a `StateEvent` because `recordEvent`
  was the first method you saw.
- Fixing a legacy bug on the way past. Flag it.
- Writing a Maestro flow against OLC when legacy has one to copy.
- Loosening a copied flow until it passes.
- Citing a parked diagnosis without re-reading it. One of the three "unreachable" findings in the
  reference migration turned out to be a missing test tag.
- Declaring the migration complete when TODOs remain. Report the gaps.
- Writing unit or screenshot tests here. Separate skill.
