# Proving parity with Maestro — the harness, and how to use it

Measured at `order-management-main@2fb4dd382` (branch `olc/maestro-harness`), against
DriverAppV3 PR #7955 (`[1/6] Maestro automation`).

The migration's parity claim is only as good as what can disagree with it. The harness exists so a
flow **written against the app that ships to drivers today** can run, unedited, against the migrated
OLC screen. That is the signal; everything else in this file is machinery to keep it honest.

---

## The one rule

> **Copy legacy's flow first. Write one by hand only where legacy has none.**

A copied flow carries legacy's assertions verbatim, so it *can* fail. A flow written against OLC can
only assert what its author already believed OLC should do — the same belief that produced OLC. Every
real finding in this suite came from a copy.

The vicinity set proves it. Ten flows copied, three passed untouched, seven failed for exactly three
causes — **and not one of the three was visible to any hand-written flow**:

| Cause | Flows | Why the hand-written flows could not see it |
|---|---|---|
| Zero vicinity radius read backwards (`CheckWithinWaypointDistanceUseCase` guarded on the *radius*, legacy guards on the waypoint's `maxDistance`) — a driver on a 0-radius order could mark arrived from anywhere | 4 | they all use radius 100, where both readings agree |
| The v1 waiting-card wire (`pickupVicinityVisibilityInfo`) is never read; `VicinityInfoDto` declares only the v2 pair | 2 | they all run the v2 payload |
| A missing test tag read as a missing page (`btn_navigate` existed on `OrderWaypointV2OrderContent.kt`, OLC had taken only the v1 name `navigateIcon`) | 1 | they assert the ids OLC has |

The first was a **migration regression against production**, not an open product question. Which is
exactly the class of defect a parity migration exists to prevent and a self-written test cannot find.

---

## Test tags: the tag value **is** the legacy view id

See `mobile-driver-olc/docs/2026-09-21-maestro-test-tag-naming.md` for the full argument.

> A tag's value IS the legacy driver-app view id the element descends from, **verbatim**. An element
> with no legacy counterpart takes an OLC-native name and says so where it is declared.

Measured against #7955's 551 flows: `addressTV` / `primaryActionBtn` are selected by **103** of them.
Matching the id buys those 103 for free.

**Placement: once per WINDOW, not once per journey.** `testTagsAsResourceId` resolves by walking
`SemanticsNode.parent` upward, and the walk **stops at the window root**. `Dialog`, `AlertDialog` and
`ModalBottomSheet` each host their own platform window and inherit nothing. Seven of the module's
first ten tags sat inside dialog windows — enabling the flag only on the activity would have left
every OTP tag invisible, and the failure is silent (the element is simply not found, which reads as
a broken app).

The module's answer: `journeys/common/ui/TestTagsAsResourceId.{kt,android.kt,ios.kt}` — an
`expect`/`actual` `Modifier.exportTestTagsAsResourceIds()` (Android-only API, `commonMain` call
sites, mirroring `DialogImeInsets` in the same package).

**Enumerate the windows yourself; do not take a count from a doc.** The Sep-2026 tag doc says nine,
and its own table lists five that carry no tags "and are left alone". At `2fb4dd382` there are
**eleven**, and ten of them export:

| Window | Where it is declared | Exports? |
|---|---|---|
| host activity → scaffold's `ModalNavigationDrawer` | host `MainActivity`, `OrderDetailsDrawer.kt:46` | ✅ |
| 5 × `journeyDialog<>` (StartTripOtp, EndTripOtp, Cancellation, OrderEdits, ChainedCancelled) | `OrderJourneyGraph.kt`, via the shared `DialogWindowRoot` wrapper at `:151-159` | ✅ |
| "Can't start trip" / "Confirm end trip" `AlertDialog` | `WaypointContent.kt:245, 254` | ✅ |
| Underpayment / far-from-point / visual-widget `ModalBottomSheet` | `UnderpaymentInstructionSheet.kt:54`, `FarFromPointSheet.kt:67`, `VisualWidgetSection.kt:349` | ✅ |

A new sheet or dialog is a new window. Wrap it in a `Box(Modifier.exportTestTagsAsResourceIds(),
propagateMinConstraints = true)` at the moment you add it, or every tag inside it is invisible and
nothing will tell you.

**Two file conventions coexist. Follow the first; recognise the second.**

1. **`<X>TestTags.kt`, one per screen and per section** — 17 objects at this HEAD
   (`WaypointTestTags`, `AddressTestTags`, `SwipeButtonTestTags`, `ContextCardTestTags`,
   `CustomerSupportTestTags`, …). Constant names are `KIND_SUBJECT`: `TXT_TITLE`, `BTN_VERIFY`,
   `IMG_THUMBNAIL`, `ROW_RETAKE`, `BOX_PIP`, `COL_STOPS_SHEET`, `DOT_UNREAD`, `GRP_DOORSTEP`.
2. **Inline `internal const val …_TAG` at the bottom of the composable file** — the older shape,
   57 constants across 10 files, still live in `orderdetail/` (21 + 20 + 4 in its two sections),
   `waypoint/ui/WaypointContent.kt` and a handful of one-offs.

Values follow one rule either way: the legacy id **verbatim** where a legacy view existed
(`primaryActionBtn`, `addressTV`, `tvAvoidCallRequest`, `waitingTimerV2ComposeLyt`,
`order_trip_details_address_layout_address_textview`), and an OLC-native `<kind>_<name>` only where
none did (`btn_visual_widget_audio`, `box_tax_banner_pip`, `card_dry_run_incentive`,
`loader_order_entry_gate`).

Two instructive cases:

- **The Compose AlertDialog carries legacy's *platform* ids.** `WaypointContent.kt:289-296` tags the
  end-trip confirmation `"android:id/message"`, `"android:id/button1"`, `"android:id/button2"`,
  because legacy drove a real platform dialog and the copied flows select on those. A Compose dialog
  cannot carry a platform id — so it carries the string.
- **A fully server-driven surface gets no tags.** `CancellationContent.kt` (441 lines) has none; its
  tests select by text, because every label on it comes from the server.

**Dynamic ids too.** `WaypointPrimaryAction` carries a `legacyTestId: String` computed by
`legacyActionTestId(type, phase, stopNumber)` (`WaypointAction.kt:77`), because legacy's CTA id
changes per waypoint (`arrivedAtPickupBtn`, `startTripBtn`, `stop1ReachedBtn`, `endTripBtn`). A
single static tag would have silently unparked nothing.

**The collision hazard.** A legacy id is unique only within its own layout; a tag is a bare string in
one semantics tree. `submitBtn` is declared in 4 layouts, `callCustomerSupportBtn` in 3, `cancelBtn`
in 2. None collides in OLC *today* only because both OTP sheets are single-occupancy dialog windows.
**The scaffold's window is the one that holds several screens at once** — it keeps `OrderDetailScreen`
composed in the drawer alongside the live inner route. Check a new id against that window's set
before reusing a legacy id there, and re-check the OTP ids if a `journeyDialog<>` is ever converted
to an inline route.

---

## Measure id coverage BEFORE judging a copied folder

A copied flow stops at its **first** missing id, so one untagged container makes a folder look like a
wall of missing behaviour when the behaviour is all there. `trip_start_end` asked for 33 ids; OLC
exported 12; seven were surfaces OLC already had and had simply not tagged, taking it to 19/33.

```sh
# what the copied flows want
grep -rhoE 'id: "[A-Za-z_][A-Za-z0-9_|.:/]*"' maestro/journeys/orders/<folder>/ \
  | sed 's/id: "//;s/"$//' | tr '|' '\n' | grep -v '^android:' | sort -u > /tmp/want.txt
# what the library exports
grep -rhoE '"[A-Za-z_][A-Za-z0-9_]*"' --include="*.kt" mobile-driver-olc/src/commonMain/kotlin \
  | tr -d '"' | sort -u > /tmp/have.txt
comm -23 /tmp/want.txt /tmp/have.txt
```

Then **check each missing id against the legacy layout that declares it** before calling it a tag
gap:

```sh
grep -rl "@+id/<name>" $DRIVERAPP/app/src/main/res/layout/
```

That step is load-bearing. Five ids that looked tag-only (`cashToCollectTitleTxt`,
`fareInfoRecyclerView`, `underpaymentInstructionText`, …) are all declared in
`rib_payment_summary.xml` — post-trip, outside OLC's boundary, not tags anyone should add.
`underpaymentInstructionText` is the trap: OLC *does* have an underpayment sheet, so the name matches
something real and the wrong conclusion is the easy one.

---

## How the harness works

### A scenario is a folder

```yaml
- runFlow:
    file: ../../../subflows/reach_order.yaml
    env:
      SCENARIO: "vicinity_far"
```

`reach_order` relaunches with `clearState`, fires `olcmock://scenario/<name>`, and taps the one
neutral entry button. `FixtureLoader.resolveFixturePath` then builds `by_scenario/<name>/<path>` and
falls back to the shared fixture when the scenario does not override that file. So:

- **Adding a variation is `mkdir` plus the files it changes.** No Kotlin, no rebuild of routing.
- **It is an overlay**, not a copy of everything.
- **An unknown name is not an error.** Every lookup falls through to the shared fixture — a
  *misspelled* scenario silently gives you the default data and your flow tests nothing.
  **Assert something only your scenario carries.** `olc_scenario_overlay.yaml` guards the mechanism
  itself; without it `resolveFixturePath` could break and every other flow would still pass.

This is DriverAppV3's own mechanism, copied — which is why its flows run here unedited. DriverAppV3
carries **244 scenario dirs / 545 files**; the OLC sample carries 53.

### Pushes mid-journey

A scenario is chosen before the journey is entered, so it cannot express a push. `MockPushActivity`
is the way in — `NoDisplay`, finishes in `onCreate`, so the journey behind it is never left:

```yaml
- openLink: "olcmock://push/end_trip?order_id=crn-1"
- openLink: "olcmock://push/cancel_order?alert=...&attribution=..."
- openLink: "olcmock://push/order_edit?type=SwitchToWaypoint"
- openLink: "olcmock://push/offline"   # every call fails, as a transport failure does
- openLink: "olcmock://push/online"
```

The sample host also registers legacy's `portermock://notify/` host verbatim, so the copied
cancellation flows speak legacy's scheme unchanged.

### The mock backend is a flat path table

`composeApp/.../mock/engine/MockBackend.kt` — one `when {}` over `request.url.encodedPath`.
Variant selection is by **fixture presence**, not by a flag:

```kotlin
path == "/orders/verify_otp" -> when {
  fixtures.hasScenarioCopy(VERIFY_OTP_RETRY_LIMIT)   -> BadRequest to VERIFY_OTP_RETRY_LIMIT
  fixtures.hasScenarioCopy(VERIFY_OTP_ALREADY_VERIFIED) -> BadRequest to VERIFY_OTP_ALREADY_VERIFIED
  else -> OK to "orders/verify_otp.json"
}
```

`MockMode` and its sixteen flags, and the eighteen case buttons that set them, were **deleted** once
the last flow stopped naming a case. A variation is a folder; adding one needs no Kotlin.

Two entry buttons remain, and **the button labels are the API** — Maestro selects on them, nothing in
Kotlin references a caption, so renaming or deleting one compiles cleanly and breaks flows silently
(it happened; four flows):

| Button | Why it exists |
|---|---|
| `Start ordinary trip` | the neutral entry; resets `MockServerState` so no flow inherits the previous one's server-side progress |
| `Resume active order` | attempts entry *without* resetting server state. Its one caller is `olc_offline_resume`, where the attempt must **fail** — that is the subject of the test |

### Surviving a process death

`SampleOLCStorageManager` writes to **SharedPreferences, not a map** — with a map, every relaunch
looked like a first launch and the library's restore path was unreachable.

Two things persist, and the split matters. The library's snapshot is one; `MockServerState` is the
other, standing in for what a **backend** would remember. A `start_trip` the server recorded must
survive the restart, so `MockServerState.tripStarted` is file-backed too — without it the mock
answers "still at the pickup" forever and the app looks as though it lost the driver's progress.

A relaunching flow uses `launchApp` **without** `clearState` and re-enters via `Resume active order`.

---

## Known debt: `MockServerState` vs DriverAppV3's `OrderState`

**This is debt from the harness port, not phase-two scope** — it should have come across and did not.

The OLC mock remembers two flat facts, `tripStarted` and `completedWaypoints`. DriverAppV3's harness
keeps a lifecycle (`app/src/maestro/java/.../http/mock/state/OrderState.kt`): a trip phase of
`NOT_STARTED`/`LIVE`/`ENDED`/`COMPLETED`, a current waypoint index, a per-waypoint status, and the
transitions `recordTripStarted()`, `recordWaypointCompleted()`, `recordTripEnded()`,
`recordJobEnded()`. It projects the phase into two separate API-shaped strings — `orderStatus()` and
`currentWaypointStatus()` — because "`ENDED` plus a `PAYMENT` waypoint is what resumes on Collect
Payment".

Nothing needs the difference today and it cannot be hit by accident (every fixture ships
`order_status: NOT_STARTED`), which is why `advanceWaypoints` can hardcode `"LIVE"` and rewrite
unconditionally. **But it is what blocks AC-3**: a fixture declaring `ACKNOWLEDGEMENT` on the mid stop
would have it erased before the driver arrived there.

Port it to match rather than growing it a feature at a time. Every place this harness diverged from
#7955 cost more than carrying it would have — `MockMode`'s 16 flags, the `legacy_base` third fixture
tier, and a widened `hasScenarioCopy` were all removed afterwards for exactly that reason, and each
was locally justified as "OLC does not need #7955's version" at the time.

---

## Rules that each cost real debugging time

- **Never declare `env:` defaults in a subflow.** A subflow's own `env:` outranks its caller's and
  silently discards what was passed. Use an `evalScript` guard:
  `- evalScript: "${output.SC = (typeof SCENARIO !== 'undefined') ? SCENARIO : ''}"`
- **Never inline a threshold swipe.** Maestro reports `swipe` COMPLETED on either side of the
  distance threshold, so a drag stretched by load does nothing, **silently**. Use
  `subflows/swipe_primary_action.yaml`, which retries behind a gate.
- **Prove arrival with a positive witness**, never `assertNotVisible` on the previous screen — a
  popped destination can stay composed, so its absence proves nothing.
- **`text:` is a full-string match.** Use `.*` on both sides for a substring.
- **Scroll to anything below the fold before asserting.** Worse for a NEGATIVE assertion, where "not
  visible" is satisfied by the element merely being off-screen — the check passes for the wrong reason.
- **Pin Maestro to 2.6.1** in all three runners (local export, CI's `MAESTRO_VERSION`, BrowserStack's
  `maestroVersion`). 2.7.0 added *"Maestro can now also match elements with their accessibility
  text"*, so on 2.x a `text:` selector falls back to `contentDescription` and on 2.6.1 it does not.
  That difference cost a real-device run: 82 selectors matched locally and failed on every device,
  because a label was published as a `contentDescription` instead of the `text` semantics property.
  2.6.1 is the **stricter** matcher, which is the right way round.
- **A dialog destination is invisible to assertions about the screen beneath it.** While the
  start-trip OTP is up, the hierarchy holds only its own nodes — the waypoint screen is absent even
  though the scrim plainly shows it. DriverAppV3 attaches its prompt as a child view in the *same*
  window, so legacy flows could read through. Judging this from a screenshot makes it look like a
  geometry problem: pixels show what was drawn, not which window drew it.
- **The waypoint screen needs a Maps API key** in the host manifest
  (`com.google.android.geo.API_KEY`). Without it the Maps SDK does not initialise and takes the app
  down the moment the screen composes, with a stack naming no app code at all
  (`IllegalStateException: LayoutNode should be attached to an owner` inside
  `ColumnMeasurePolicy.measure`). The sample carries a placeholder key for this reason.

---

## What the suite is, and keeping the numbers honest

| Tree | Count | Holds |
|---|---|---|
| `maestro/journeys/orders/` | 80 | flows copied **verbatim** from #7955, keeping legacy's folder layout and `appId: ${APP_ID}` header |
| `maestro/flows/` | 23 | flows **rewritten** for OLC — because a verbatim copy could not run (OLC's shape differs, e.g. legacy drove a platform `AlertDialog` with `android:id/button1`), or to consolidate two legacy flows that need the same walk |

80 + 23 = **103**, and the 13 configs name exactly 103 distinct paths between them. Verified at this
HEAD. `ci/device_jobs.txt` carries the same count. **Keep these in step** — the README's table once
read "81 + 13 = 94" long after the OTP set took `flows/` to 23.

Nine of #7955's thirteen `journeys/orders/` folders are in scope. `notification` (24, pre-order),
`payment` (22), `rating` (3) and `schedule` (8) are deliberately not: they start on a screen that
does not exist yet, so a copy would fail on its first line. Copy them when phase two starts — a
folder of flows that all fail immediately is noise, not a backlog.

**A flow executes if and only if a config names it, and `device_jobs.txt` assigns every config to a
device.** That coupling is deliberate: the emulator and the farm previously kept separate lists and
drifted, reddening the job on every labelled PR regardless of the flows.

### Two stale claims in the harness README — check before citing

Both are things the README itself tells you to verify, and both are currently false at
`2fb4dd382`:

- The README documents `# COVERS Cxxxxx` headers and `ci/case_ids_per_flow.py` reading them. **Zero
  flows carry a `COVERS` line.** The script and `report.sh`'s "N of M cases passed" header therefore
  report nothing.
- The README devotes a section to `WHY THIS IS RED` headers being unreliable. **Zero flows carry
  one.** (The warning is still worth internalising: at the last measurement 42 flows carried the
  header and only 2 were actually red.)

Both were real when written. Re-run `grep` before you reason from either. The README's own standing
instruction applies to itself: *"Verify a row against `ls` before you trust it, and before you edit
it."*

### When a copy fails

**Do not loosen a copied flow until it passes.** Its assertions came from an app running in
production; when one fails, the flow is usually right and OLC is usually wrong. There is no `gap`
tag and no gap register — every red fails the build. A flow that documents a real behavioural
difference has two honest homes: **fixed**, or **parked with the cause written down**.
