# Worked example — `orderwaypoint` → the pre-end-trip journey

The reference migration. **Everything from order entry through the waypoint loop up to and including
the end-trip confirmation.** It is the right example because it is the largest unit in the legacy
flow, it had four child RIBs, it was already half-migrated to Compose on the legacy side, and it
shipped as a reviewable PR stack rather than one drop.

---

## The legacy unit

| | shared/ | app/ |
|---|---|---|
| `…/orderflow/orderwaypoint/` | **49 files, 3 432 lines** | **20 files, 1 199 lines** |

Shared sub-packages: `analytics/`, `assistant/`, `data/`, `dryrunincentivecard/`,
`orderwaypointcontextcard/`, `state/`, `view/`.

| Piece | Lines | Shape |
|---|---|---|
| `OrderWaypointInteractor` | 705 | `BaseStateVMInteractorV2`, **26 constructor deps**, `didBecomeActive()` = a flat list of ~17 `launch { XHandler().invoke() }`, **24 inner-class handlers** |
| `OrderWaypointParams` | 27 | 15 fields — including `porterLocationRepo: PorterLocationRepo` (a *repo* passed as a param) and `showUnderpaymentInstructionsStream: Flow<Unit>` |
| `state/OrderWaypointState` + `StateReducer` | 19 + 60 | 10 booleans/enums; 10 `suspend fun x() = updateState { it.copy(...) }` |
| `view/OrderWaypointPresenter` | 22 | `BasePresenter<OrderWaypointVM>`, 10 event flows **+ one imperative `fun centreMap(...)`** |
| `view/OrderWaypointVM` | 198 | `sealed class` → `OrderWaypointVMV1` and `sealed class OrderWaypointVMV2 { WaypointWithMapView, WaypointWithVisualWidget }`, ~20 nested VMs |
| `view/OrderWaypointVMMapper` (+3 helpers) | 325 + 394 | the derived-UI layer |
| `analytics/OrderWaypointAnalyticsV2` | 500 | |
| `OrderWaypointRouter` | 17 | 7 suspend attach/detach for **4 children** |
| app-side `OrderWaypointView` | 358 | the V1/V2 visibility toggle |
| `res/layout/rib_order_waypoint.xml` | 336 | plus 4 `<include>`s and **five `ComposeView`s** |

**The V1/V2 split is the whole shape of the screen**, and it is a visibility toggle between an XML
half and a Compose half — `OrderWaypointView.kt:142-162` flips `orderContentLyt` against
`orderContentComposeLyt`. On the V2 path `orderContentLyt` is GONE, which matters: the `addressTV` /
`addressHeaderTV` ids declared in `rib_order_waypoint.xml` are **not** what renders there. Reasoning
about layout order from that file is reasoning from the dead half.

---

## The target

```
screens/orderentrygate/   — OLC-only; replaces a decision legacy made without a screen
screens/waypoint/         — the loop: mark-arrived → start-trip → waypoint-complete → end-trip
  sections/ × 11          — the 4 child RIBs plus 7 regions that were inline in the XML
screens/acknowledge/      — the mid-stop ack phase
screens/orderdetail/      — the trip-details drawer (+ sections/address, sections/farebreakup)
screens/cancellation/, orderedits/, chainedcancelled/  — dialog destinations
navigation/support/       — the customer-support strip, as a journey-scoped section
domain/statemachine/      — OlcStateMachine, LiveStateMachine, EndedWorkflow
domain/OrderJourneyStateManager — the single-writer state hub
```

### Child RIB → section, concretely

| Legacy child RIB | OLC home | Shape |
|---|---|---|
| `orderwaypointcontextcard/` (6 files, 152 L) | `sections/contextcard/` | stateless — `ContextCardSection.kt` + tags |
| `dryrunincentivecard/` (13 files, 383 L) | `sections/dryrunincentive/` | **stateful** — Section + State + UIEvent + ViewModel + tags |
| `assistant/` (9 files, 359 L) | `sections/assistant/` | **stateful** — `AssistantViewModel : BaseViewModel<WaypointParams, AssistantState, Nothing>` |
| the order-context card attach | folded into `WaypointState.contextCards` | the parent VM already holds the order |

The three regions that were *inline* in the XML but big enough to own a file became stateless
sections anyway: `address`, `orderinstructions`, `visualwidget` (423 L). `orderaction` and
`waitingtime` became stateful sections because each has a timer or an enable-cooldown of its own.

### What `OrderWaypointListener` became

Nothing. The waypoint does not report up — it calls `start_trip`, and **on success** dispatches
`OlcStateMachineEvent.Driver.TripStarted(timestamp)` carrying the server's own timestamp. The
machine bookkeeps that onto the order it already holds and advances locally; `render(state)` then
moves the route. The 7 `router.attach/detach` calls likewise disappeared into section composition
and `journeyDialog<>` destinations.

### What `OrderWaypointParams`' 15 fields became

- `porterLocationRepo` → `DriverLocationManager` on `OlcJourneyDependency`
- `vicinityInfo` → `stateManager.vicinity: StateFlow<VicinityInfo?>`
- `showUnderpaymentInstructionsStream` → `domain/UnderpaymentSignal`, journey-scoped *"raised by the
  journey and read by whichever screen is up, so the signal is shared at this scope rather than owned
  by either"*
- `showTaxTrainingInfo` → `OlcFeatureFlagProvider.showTaxTrainingInfo()` **and**
  `OlcStringsProvider.provideTaxTrainingInfo(): TaxTrainingInfo?`
- `canContinueWithPod` → `OlcFeatureFlagProvider.isPodUiEnabled()`
- the order itself → the state manager. `WaypointParams` is an `object`.

---

## How it shipped: four PRs, sliced by LAYER

| # | PR | Files | Lines | Contents |
|---|---|---|---|---|
| 1 | `contract, data and domain core` (#813) | 126 | +6 110 | `contract/` entities + resources + ports, `data/dto`, `data/mapper`, `data/client`, `data/persistence`, `data/retry`, `domain/statemachine`, `domain/usecase`, `instrumentation/analytics`, and the wire/round-trip tests |
| 2 | `shared UI foundation` (#811) | 68 | +2 404 | `journeys/theme/`, `journeys/common/ui/`, `journeys/common/platform/` expect-actuals, **38 drawables + 3 fonts + 1 lottie** copied from legacy, `BaseComposeTest`/`BaseScreenshotTest` |
| 3 | `screen content and state` (#812) | 120 | +15 072 | every `<X>Section.kt`, `<X>Content.kt`, `<X>State.kt`, `<X>TestTags.kt` — and their compose/screenshot tests |
| 4 | `view models, DI spine, navigation and host wiring` (#814) | 90 | +14 096 | every `<X>ViewModel.kt`, `di/<X>Component.kt`, the whole `navigation/` package, `component/`, `TripActionCoordinator`, and the sample host |

**Slice by layer, not by screen.** Each PR compiles and is reviewable on its own axis — a reviewer of
#813 checks wire names and state transitions without reading a single Composable; a reviewer of #812
checks pixels without reading a mapper. Slicing by screen would have put the same four concerns in
every PR and made none of them reviewable.

After the stack landed, the follow-ups were small and single-purpose:
`refactor: one tap pipeline, matching legacy's, instead of six partial ones` (the coordinator),
`refactor: make the end-trip settle window host config, not a constant`,
`test: Maestro UI suite, mock-backed sample host and farm CI`.

---

## Stop gates that this migration CLOSED

The earlier version of this skill listed these as class-B ("the target repo has no home") and
class-F ("deferred") gates. They are resolved, and **the resolution is the pattern to copy**.

| Was | Now |
|---|---|
| `OlcStringsProvider` is an empty class → hardcode + `TODO(strings)` | 9 `provideXxxStrings()` accessors over 9 `contract/resources/<X>Strings` data classes; `#argN` substitution via `String.withArgs`. A legacy vernac screen class maps 1:1. |
| `OlcFeatureFlagProvider` is an empty marker interface → drop the flags | 11 flags, each a `fun`/`suspend fun` KDoc'd with its legacy remote-config key and default (`otpImeActionDone` ← `otp_collect_ime_action_done`, …) |
| `OlcAnalyticsManager` emits `StateEvent.State` only → 4 of 8 events would flatten | `recordImpression` / `recordClick` / `recordSwipe` / `recordEvent` / `recordLegacy`, plus `setOrderContext` for the per-order base attributes |
| no flux throttle helpers → dropping double-tap protection is a divergence | `TapThrottle` over a per-event `Channel`, config-driven, backed by kmp-utils' own `throttleFirst` / `exponentialThrottle` |
| `fullScreenLoader.showWhile` has no equivalent → a disabled button | `OlcFullScreenLoader` — a real tap-swallowing scrim with a 5s slow-network message, driven by `isActionInFlight` |
| the state manager does not exist → `Params(Order(""))` placeholder, `TODO(LAYER-B)` | `OrderJourneyStateManager` + `render(state)`. Screen params are an `object`; the screen reads the order off the hub |
| child RIBs have no OLC concept → dropped, needs product sign-off | `sections/`, with scope-matched VMs for the ones that had state |
| customer support → "open the OrderDetail drawer, carrying the legacy conflation" | `navigation/support/CustomerSupportSection` + its own VM at journey scope |
| OTP routes are in `DRAWER_DISABLED_ROUTES` | they are `journeyDialog<>` destinations in their own windows |

**The lesson is not "those gates were wrong."** They were correct when raised — raising them is what
got them designed properly instead of papered over. The lesson is that **a missing seam in OLC is now
usually a 15-line addition to an existing port, not a deferral**: one more `fun` on
`OlcFeatureFlagProvider`, one more field on `OlcConfigs`, one more accessor on `OlcStringsProvider`.
Check whether the seam exists before you deferring to it.

---

## What the harness found about this migration

Copied `journeys/orders/vicinity/` (10 flows) and `trip_start_end/` against the finished screens.
Three causes, in order of what they teach:

1. **A real regression against production.** `CheckWithinWaypointDistanceUseCase` guarded on
   `radiusMeters <= 0` and short-circuited the check; legacy guards on the **waypoint's** own
   `maxDistance` and then evaluates `distance < radius`, so a 0 radius *warns*. A driver on such an
   order could mark arrived from anywhere. Fixed in `69e16da17`; the radius overload, which had no
   coverage at all, now has four cases.
2. **A wire format read half-way.** Legacy carries the waiting-card copy in two places —
   `pickupVicinityVisibilityInfo` (v1) and `waitingTimeAppConfigs.<screen>.waitingTimeHeader` (v2).
   `VicinityInfoDto` declares only the v2 pair and `WaypointState` gates the card on
   `enabled.screens != null`, so a v1 payload renders no card. **Still open.**
3. **A missing tag read as a missing screen.** Legacy calls the navigate control `navigateIcon` on
   `OrderWaypointView.kt` and `btn_navigate` on `OrderWaypointV2OrderContent.kt`; OLC had taken only
   the v1 name. One extra layout-free node carrying `btn_navigate` (`AddressSection.kt`) unparked two
   flows. It had been written up as "OLC has no v2 arrived page" — **re-read a parked diagnosis
   before citing it.**

None of the three was findable by a flow written against OLC.

---

## Still open on this unit

| Row | Legacy | Current target |
|---|---|---|
| v1 waiting-card wire | `pickupVicinityVisibilityInfo` / `dropVicinityVisibilityInfo` carry the card's copy | `VicinityInfoDto` declares only the v2 pair; the card does not render on a v1 payload |
| per-waypoint contact | legacy's drawer lists a contact **per waypoint** (`tvWaypointContactName`, `layoutWaypointContact`) | `OrderDetailState` carries one order-level `order.contact` — and OLC dials the wrong number when a stop carries its own. See `docs/olc-migration/tripdetails-contact-block-parity-ledger.md` H-04 |
| avoid-calling popup | sits behind the per-waypoint contact row | unreachable while that row is missing |
| AC-3 mid-waypoint ack | the `ACKNOWLEDGEMENT` wire status | no fixture carries one, and the mock's `advanceWaypoints` would erase it. Blocked on the `MockServerState` vs `OrderState` debt, **not** on OLC |
| context-card show-after delay | legacy passes 180s | `olcConfigs.contextCardShowAfterDelaySeconds` exists and defaults to 0; two copied flows die on `tvInviteTitle` until a host passes 180 |
