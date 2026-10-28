# Legacy → OLC: the target map and the screen anatomy

Measured at `order-management-main@2fb4dd382` (`olc/maestro-harness`). `$OLC` =
`frontend/mobile/mobile-driver-olc/mobile-driver-olc/src/commonMain/kotlin/in/porter/olc/mobile/driver/`.
Note the **nested** directory — `mobile-driver-olc/mobile-driver-olc`.

---

## 1. The mapping table

| Legacy (DriverAppV3) | OLC 2.0 target | Notes |
|---|---|---|
| `<Unit>Interactor : BaseStateVMInteractorV2` | `<Screen>ViewModel : BaseViewModel<Params, State, UIEvent>` | `in.porter.kmputils.coreui.BaseViewModel`. `updateState { it.copy(...) }`, `launch(dispatcher) {}`, `onStart()`, `onUIEvent()`. |
| `didBecomeActive()` + N × `launch { XHandler().invoke() }` | `onStart()` — one `launch {}` per concern, same flat list | The handler-per-concern shape survives; it just loses the inner classes. `WaypointViewModel.onStart()` has 14. |
| `<Unit>StateReducer` + `<Unit>State` | `<Screen>State`, no reducer | Reducer methods become inline `updateState {}`. |
| `<Unit>Presenter` streams | `<Screen>UIEvent` sealed interface **+ a `Channel` per throttled event** | See §4 — Compose calls `onUIEvent`, which `trySend`s into a channel that `onStart` collects through `TapThrottle`. |
| `<Unit>VM` + `<Unit>VMMapper` | a **pure top-level mapper function** `internal suspend fun <screen>State(live, strings, flags, vicinity): State.Content` | Not computed `val`s. The waypoint's is `waypointState(...)` at `WaypointState.kt:220` with 12 private helpers under it. Transcribe each predicate exactly. |
| a **sealed** `<Unit>VM` (V1/V2 variants) | a **sealed** `<Screen>State` (`Loading` / `Content`) + sealed sub-types inside `Content` | `WaypointState` is `sealed interface { Loading; Content }`; variants like `TaxBanner.TextOnly/Thumbnail/PipVideo` nest inside `Content`. |
| `<Unit>Service` / `<Unit>HttpService` | a method on the **right** client — see §2 | There are now four data entry points, not one. |
| `data/models/*Request/*Response` | `$OLC/data/dto/` | **Copy `@SerialName` byte-for-byte**, including error-enum values. |
| response → domain conversion in the interactor | `$OLC/data/mapper/<X>Mappers.kt` | `internal fun Dto.toDomain()`. Clients return **domain types, never DTOs**. |
| `usecases/` | `$OLC/journeys/orderjourney/domain/usecase/` | `@Inject internal class XUseCase(private val client: LiveOrderClient)`. 7 exist. |
| `entities/` enums | `$OLC/contract/entities/` if the host or state machine sees it; else `data/dto/` | `contract/` is the only non-`internal` package. |
| `<Unit>Builder` (manual construction) | `di/<Screen>Component.kt` (kotlin-inject) | Template in §3. |
| `<Unit>Listener` | the state machine, usually — **not** a listener interface | A screen reports a fact by `stateManager.dispatch(OlcStateMachineEvent.Driver.X)`; the machine advances the order and the router follows. A `<Screen>Listener` is now the exception, for a screen the journey cannot model. See §7. |
| `router.attachX/detachX` (child RIB) | a **section** under `screens/<screen>/sections/<x>/` | See §5. This is the big change: a child RIB is no longer a stop gate. |
| `router.attachX` for a *modal* child | a `journeyDialog<>` route, or a `ModalBottomSheet` inside the screen's `ui/` | Five `journeyDialog<>` destinations exist today; the journey has nine separate windows in total. |
| `stringsRepo.getScreenStrings<XStrings>(KEY)` | `contract/resources/<X>Strings.kt` + a `provideXxxStrings()` on `OlcStringsProvider` | 9 per-screen accessors + 2 nullable content providers (`provideTaxTrainingInfo`, `provideP2cCallDeflection`, both defaulting to `null` = feature off). The host owns the key→type map. See `host-stitch.md` §6. |
| `RemoteConfigRepo` **gate** | a `fun` on `OlcFeatureFlagProvider`, KDoc'd with the legacy config key | 10 declared. Every flag is a function, never a `val`, so each read hits the host's store at the moment of the call. |
| `RemoteConfigRepo` **number** | a field on `contract/entities/OlcConfigs`, with a default + a KDoc naming the legacy key and its resolved value | e.g. `tapDebounceMs` ← `debounce_timeout_in_millis` (code default 500L). |
| `FeatureAnalytics` / `EventRecorder` | `OlcAnalyticsManager` + names in `instrumentation/analytics/OlcAnalytics.Event` | See §6. Fully typed now. |
| `fullScreenLoader.showWhile { … }` | `journeys/common/ui/OlcFullScreenLoader` + an `isActionInFlight` flag on the state | A real blocking scrim that swallows taps, with a slow-network message after 5s. **A disabled button is not the same thing.** |
| `GetFlowWithThrottleFirst`, `exponentialThrottleUseCase` | `journeys/common/TapThrottle` over a per-event `Channel` | §4. Backed by kmp-utils' own `throttleFirst` / `exponentialThrottle`. |
| `uiUtility.hideKeyboard()`, IME action | the `otpImeActionDone()` / `hideKeyboardOnSubmit()` flags + `journeys/common/ui/DialogImeInsets` | |
| RxJava `Observable` | `Flow` | OLC is coroutines-only. |
| `klock` `TimeSpan` | `kotlin.time.Duration` | …except `OlcConfigs` still uses `com.soywiz.klock.milliseconds` for `ExponentialThrottleConfig`, which is a kmp-utils type. |
| Dagger `@Module`/`@Inject` | `me.tatarka.inject.annotations.Inject` | Different `Inject`. Check the import. |
| a **platform** call (dialer, maps, toast, external app) | `journeys/common/platform/` `expect`/`actual`, launched off `PlatformResource` | `OpenDialerUseCase`, `OpenMapNavigationUseCase`, `LaunchExternal`, `ToastUtils`. These are **not** on `OlcExternalActions`, which carries only hand-offs the host genuinely owns (chat, scanner, liveness, support, SOS). |

---

## 2. There are four data entry points, not one

The old rule "one `OlcClient`; add methods, do not add clients" is **superseded**. Current shape:

| Type | Scope | Holds |
|---|---|---|
| `data/client/OrderClient` ← `HttpOrderClient` | `@OlcScope` (process) | entry + eligibility: `fetchDriverOrderDetails()`, `fetchLoadAssistMetaData()` |
| `data/client/LiveOrderClient` ← `HttpLiveOrderClient` | `@OrderJourneyScope` | the waypoint cycle: `fetchVicinityInfo`, `markArrived`, `startTrip`, `verifyEndTripOtp`, `resendEndTripOtp`, `completeWaypoint`, `endTrip`, `fetchIncentives`, `fetchCancelReasons`, `cancelTrip`, `cancelTripWithAttribution`, `fetchEndTripVicinityInstructions` |
| `data/FusedOrderRepository` → `domain/OrderRepository` | `@OlcScope` | the read-through cache over the snapshot + the network |
| `data/retry/OlcReplayClient` | `@OlcScope` | background replay of a captured request body |

Put a new call on the client whose **scope and lifecycle** it belongs to. A journey-only call on the
process-scoped `OrderClient` keeps the headless spine coupled to UI-era state.

### Replay is narrow, on purpose

`OlcEndpoint` has exactly two members — `START_TRIP` and `WAYPOINT_COMPLETE` — and its KDoc says so:
*"never end_trip/mark_arrived/cancel"*. This ports legacy's retry set exactly. The paths live in one
place (`data/client/OlcRetryablePaths`) shared by the live call and the replay so they cannot drift.
Policy: 6 attempts, 1s/2s/4s/8s/16s backoff, retry on transport failure or a parsed 5xx, **never** on
a parsed 4xx business rejection. Scheduling goes through `OlcRetryEnqueue` (expect/actual) onto
`work/OlcRetryWorker` (WorkManager) so a replay runs with no UI mounted.

---

## 3. DI — three scopes, nested

```
@OlcScope          OlcComponent          process-lifetime; built headless by OlcManagerBuilder
  └ @OrderJourneyScope  OrderJourneyComponent   one per journey mount; holds OlcJourneyDependency
      └ @<Screen>Scope      <Screen>Component       one per screen composition
```

`OlcComponent` takes the six `OlcPlatformDependency` members; `OrderJourneyComponent` takes
`OlcComponent` as its `@Component` parent plus `OlcJourneyDependency` and the journey listener, and
re-exposes each journey capability as an `@OrderJourneyScope @Provides get()`.

Screen component template — mirror exactly:

```kotlin
@<Screen>Scope
@Component
internal abstract class <Screen>Component(
  @Component val parent: OrderJourneyComponent,
  @get:Provides val params: <Screen>Params,
) {
  abstract val viewModel: <Screen>ViewModel

  // Section VMs live in the screen's scope — same lifecycle as the screen composable.
  internal abstract val <section>ViewModel: <Section>ViewModel
}

@KmpComponentCreate
internal expect fun create<Screen>Component(
  parent: OrderJourneyComponent,
  params: <Screen>Params,
): <Screen>Component

@Scope
@Target(AnnotationTarget.CLASS, AnnotationTarget.FUNCTION, AnnotationTarget.PROPERTY_GETTER)
internal annotation class <Screen>Scope
```

Two notes from `WaypointComponent`:

- **An assisted factory** is `(Dependency) -> ViewModel`, used when a callback arrives with the
  screen rather than the graph (`orderEntryGateViewModelFactory`).
- **A renderer kept as an interface purely as a screenshot-test seam** is bound to its default on the
  component, not on the contract: `internal val mapRenderer: OlcMapRenderer get() = DefaultOlcMapRenderer`.

### Coroutine context

`OlcComponent` provides **only** the exception-handler-wrapped `CoroutineContext`
(`coroutineContext.withOlcExceptionHandler()`); the raw one stays private. Every library coroutine
therefore reports failures through one pipe. Never inject a raw context.

---

## 4. Taps: `UIEvent` → `Channel` → `TapThrottle` → handler

Legacy wrapped taps in `GetFlowWithThrottleFirst` and `exponentialThrottleUseCase`. OLC restores
that, which is why `onUIEvent` is not where the work happens:

```kotlin
private val confirmEndTripClicks = Channel<Unit>(capacity = Channel.UNLIMITED)

override fun onUIEvent(event: WaypointUIEvent) = when (event) {
  WaypointUIEvent.ConfirmEndTripTapped -> confirmEndTripClicks.trySend(Unit)
  …
}

override fun onStart() {
  super.onStart()
  launch { tapThrottle(confirmEndTripClicks).collect { onConfirmEndTripTapped() } }
  …
}
```

`TapThrottle` (`journeys/common/TapThrottle.kt`) wraps kmp-utils' `throttleFirst(tapDebounceMs)` and,
with `withBackoff = true`, `exponentialThrottle(configs.throttleConfig)`. It is `@OrderJourneyScope`,
constructed from `OlcConfigs`.

**A tap with no throttle in legacy stays unthrottled.** Carry the legacy decision; do not throttle
everything "for safety".

---

## 5. Screen anatomy — one screen, many sections, one coordinator

The waypoint screen is 2 349 lines of screen + 2 229 lines of sections. Its structure is the pattern
for any large legacy RIB with children.

The canonical screen is **seven files**: `<X>Screen.kt`, `<X>State.kt` (+ its pure mapper),
`<X>UIEvent.kt`, `<X>ViewModel.kt`, `<X>Dependency.kt` (`data class <X>Dependency(val params)` +
`object <X>Params`), `di/<X>Component.kt`, `ui/<X>Content.kt` (+ `ui/<X>TestTags.kt`). Every screen
file ends with a top-level `build<X>Dependency(...)` that the graph calls.

```
screens/waypoint/
  WaypointScreen.kt          61   @Composable: rememberComponent → porterViewModel ×5 → Content
  WaypointViewModel.kt      443   the parent VM: state mapping, dialogs, analytics
  WaypointState.kt          502   sealed Loading/Content + the pure mapper fn + 12 helpers
  WaypointUIEvent.kt         15   sealed interface, 11 events
  WaypointAction.kt         162   the primary action's kind/label/colour/legacyTestId derivation
  TripActionCoordinator.kt  459   the ONE tap pipeline (see below)
  WaypointDependency.kt       8   data class Dependency(params) + `internal object WaypointParams`
  di/WaypointComponent.kt    52
  ui/WaypointContent.kt     296   the previewable, DI-free half
  ui/FarFromPointSheet.kt   211 · ui/UnderpaymentInstructionSheet.kt 121
  ui/WaypointTestTags.kt     12 · ui/FarFromPointTestTags.kt 7
  sections/<11 of them>
```

### `<Screen>Screen` vs `<Screen>Content`

`Screen` does DI and lifecycle; `Content` is pure and previewable. Keep them separate.

```kotlin
@Composable
internal fun WaypointScreen(journeyComponent: OrderJourneyComponent, dependency: WaypointDependency) {
  val component = rememberComponent<WaypointComponent> {
    createWaypointComponent(parent = journeyComponent, params = dependency.params)
  }
  val screenViewModel = porterViewModel { component.viewModel }
  val orderActionViewModel = porterViewModel { component.orderActionViewModel }
  …
  val strings = journeyComponent.olcStringsProvider.provideOrderWaypointStrings()
  WaypointContent(state = state, orderActionState = orderActionState, strings = strings,
    onUIEvent = screenViewModel::onUIEvent, onOrderActionUIEvent = orderActionViewModel::onUIEvent, …)
}
```

### Sections: three tiers

A legacy child RIB becomes a **section**. Pick the tier from what the child actually owned.

| Tier | Files | Use when | Examples |
|---|---|---|---|
| **A — stateful** | `<X>Section.kt`, `<X>State.kt`, `<X>ViewModel.kt`, `<X>TestTags.kt`, + `<X>UIEvent.kt` if it takes input | the section has an **independent clock, an independent fetch, or a lifecycle the parent cannot observe** | `orderaction`, `waitingtime`, `assistant`, `dryrunincentive` |
| **B — pure composable** | `<X>Section.kt` (+ `<X>TestTags.kt`) | it only renders what the parent state already holds | `address`, `banner`, `contextcard`, `orderinstructions`, `visualwidget` |
| **C — renderer seam** | `<X>Renderer.kt` (interface + `Default…` object) + `OlcPlatform<X>.kt` `expect`/`actual` | the section is platform-heavy and screenshot tests need a flat fake | `map`, `media` |

Tier A notes:

- The VM is `@<Screen>Scope @Inject`, declared on the **screen's** component, so it shares the
  screen's lifecycle — not the journey's.
- It reuses the **parent's** `Params` type, never its own:
  `BaseViewModel<WaypointParams, AssistantState, Nothing>`.
- **`Nothing` is the UIEvent type for a display-only section.** `WaitingTimeViewModel` and
  `AssistantViewModel` both use it. If you find yourself writing an empty sealed interface, use
  `Nothing`.
- The section's view *data* can still live on the parent state —
  `DryRunIncentiveState` is a thin holder wrapping a `WaypointState.DryRunIncentive`.
- Section VMs at the same scope may inject each other. `AssistantViewModel` takes
  `OrderActionViewModel` and `WaypointViewModel` directly and awaits their flows; that is legal
  precisely because all three are `@WaypointScope`.

Tier B notes: parameter style is **flat values, not a state object**, when the section needs a
slice (`AddressSection(headerLabel, addressLine, onNavigateTap, …)`), and the whole state object
when it needs most of it (`FareBreakupSection(data: OrderDetailState, …)`).

Tier C shape:

```kotlin
internal interface OlcMapRenderer { @Composable fun Map(state: OlcMapState, modifier: Modifier) }
internal object DefaultOlcMapRenderer : OlcMapRenderer { … }
@Composable internal expect fun OlcPlatformMap(state: OlcMapState, modifier: Modifier)
```

Bound on the screen component (`internal val mapRenderer: OlcMapRenderer get() = DefaultOlcMapRenderer`)
and threaded down as a parameter. The interface is **not** a host slot — per the rollout call the map
is module-owned; it stays an interface purely as a test seam.

**A pure function shared between a section VM and the parent mapper gets its own file.**
`waitingtime/WaitingTime.kt` is nothing but `internal fun OlcState.Live.accruedWaitingSeconds(): Long`
— *"so the panel chip and the VM behind it always agree."*

Do **not** promote a section to a nav route to give it a lifecycle. The scope does that.

### The coordinator

When one user action can be started from several places and must behave identically — the swipe
section, a dialog confirmation, a push — extract a `@<Screen>Scope @Inject class <X>Coordinator`
that owns guards, the use case, and the lifecycle dispatch, and reports back through flows:

```kotlin
internal sealed interface TripActionFeedback {
  data class ShowDialog(val dialog: WaypointState.Dialog) : TripActionFeedback
}

val feedback: SharedFlow<TripActionFeedback>
val inFlight: StateFlow<Boolean>
```

The VM folds `feedback` into the rendered dialogs and `inFlight` into the loader. This replaced six
partial tap paths with one matching legacy's (commit `dba346c7a`). Two details worth copying:

```kotlin
private suspend fun working(action: suspend () -> Unit) {
  _inFlight.emit(true)
  try { guarded(action) } finally {
    // Deliberately an assignment, not emit(): this runs during cancellation unwinding, where a
    // suspending clear would strand the screen's loader on.
    _inFlight.value = false
  }
}

private suspend fun guarded(action: suspend () -> Unit) {
  try { action() }
  catch (e: CancellationException) { throw e }
  catch (e: Exception) {
    showError(strings.requestFailed)
    RecordException.invoke(e)   // report AS WELL AS show — binding to `_` sent nothing to the host
  }
}
```

---

## 6. Analytics — typed, and the legacy names are the contract

`OlcAnalyticsManager` is `@OlcScope`, injected, fire-and-forget on `appDispatchers.io`, and emits
**every** kmp-utils event type:

| Method | Emits | Legacy equivalent |
|---|---|---|
| `recordImpression(name, attrs)` | `ImpressionEvent.ViewShown` | `ImpressionEvent.ViewShown` |
| `recordClick(name, attrs)` | `ActionEvent.Click` | `ActionEvent.Click` |
| `recordSwipe(name, attrs)` | `ActionEvent.Swipe` | `ActionEvent.Swipe` |
| `recordEvent(name, attrs, stateEventName)` | `StateEvent.State` | `StateEvent.State` |
| `recordLegacy(name, attrs, metrics)` | `LegacyEvent` | pre-kmp-utils senders — **the one recorder that merges no common attributes**, because the legacy senders it ports carried none |

`setOrderContext(attributes)` pushes the active order's attributes onto every event (the manager
outlives the journey, so a journey-scoped observer pushes on change and clears on teardown). That is
`FeatureAnalytics`' base-attribute merge, ported.

Event names live as `const val`s in `OlcAnalytics.Event`, **set to the legacy wire name verbatim**,
with a comment saying so:

```kotlin
// Waypoint screen — names mirror the legacy OrderWaypointEventIdentifiers/OrderWaypointAnalyticsV2
// wire names so dashboards keep working across the migration.
const val NAVIGATE_TAPPED = "fragment_order_v2_navigate_icon_imageview"
```

A new business-vocabulary name may be added **alongside** a legacy one, never instead of it. Two
generic envelopes exist for legacy events that had no name of their own: `LEGACY_BUTTON_PRESS =
"button_press"` (the button's name rides in a `button` attribute) and `LEGACY_DATA_EVENT =
"data_event"`.

**Preserve the event *type*, not just the name — including where legacy got it wrong.** The module
carries this verbatim:

```kotlin
OlcState.WaypointPhase.Arrived -> when (live.activeWaypoint.type) {
  Waypoint.Type.START  -> analytics.recordSwipe(Event.CONTINUE_TRIP_SWIPED, attributes)
  // Legacy anomaly, preserved: Click, not Swipe.
  Waypoint.Type.MIDDLE -> analytics.recordClick(Event.CONTINUE_TRIP_SWIPED, attributes)
  Waypoint.Type.END    -> analytics.recordSwipe(Event.END_TRIP_SWIPED, attributes)
}
```

The **same event name** is a Swipe on one waypoint type and a Click on another, because legacy sent
it that way. Normalising the middle arm would be a silent divergence — a different row in a
dashboard for the same control. If the anomaly bothers you, it is a **D-nn**, not a cleanup.

---

## 7. Navigation — phase → route, and params mostly do not travel

Routes are `@Serializable` members of `OrderJourneyRoute` — **declared inside
`navigation/OrderJourneyNavigationManager.kt:25-61`**, not in a file of their own. There is no
`OlcJourneyRoute.kt` and no `OrderJourneyContent.kt`; the graph is
`navigation/OrderJourneyGraph.kt`.

`journeyRoute` / `journeyDialog` / `journeyNavigation` are **kmp-utils**, not local — see
`kmp-utils/core-ui/.../coreui/navigation/GraphScope.kt`. Registration:

- `journeyRoute<R> { component -> … }` — an inline destination (`OrderEntryGate`, `Waypoint`,
  `Acknowledge`), each wrapped in `JourneyBackHandler { }`.
- `journeyDialog<R>(dialogProperties) { component -> DialogWindowRoot { … } }` — its own window
  (`StartTripOtp`, `EndTripOtp`, `Cancellation`, `OrderEdits`, `ChainedCancelled`), each with
  explicit `DialogProperties(dismissOnBackPress = …, dismissOnClickOutside = false,
  usePlatformDefaultWidth = false)`. The `DialogWindowRoot` wrapper is what applies
  `exportTestTagsAsResourceIds()`.

The manager **holds no NavController**: it enqueues `NavCommand`s onto a `Channel(UNLIMITED)`
exposed as `commands: Flow<NavCommand>`, which the `journeyNavigation` DSL collects and applies
under `repeatOnLifecycle(STARTED)`. Two rules live there and are easy to break:

- `switchTo(route)` does `popUpTo(OrderEntryGate) { inclusive = false }; launchSingleTop = true` —
  the entry gate stays at the root with a single live destination above it, so state transitions
  never pile screens up.
- `navigateTo(route)` **pops before navigating** when the current destination already has the same
  route class. Reuse would keep the *first* push's arguments — so the driver would acknowledge
  edits they never saw.

Phase → route dispatch is one 25-line pure function:

```kotlin
internal fun render(state: OlcState): OrderJourneyRoute? = when (state) {
  OlcState.Allocated -> OrderJourneyRoute.OrderEntryGate
  is OlcState.Live -> when (state.phase) {
    InVicinity, Arrived -> OrderJourneyRoute.Waypoint
    CollectAcknowledgement -> OrderJourneyRoute.Acknowledge
  }
  is OlcState.Ended, is OlcState.Terminal -> null   // the journey exits
}
```

**An overlay is not a phase.** The OTP dialog is opened *imperatively* by the trip-action result and
floats over the waypoint while the phase stays `Arrived` — exactly legacy's `CollectOtp` semantics,
where the running timer keeps ticking underneath.

**Params mostly do not travel through nav**, and the split is deliberate:

| Screen | Params | Why |
|---|---|---|
| `Waypoint`, `Acknowledge`, `OrderDetail` | `internal object XParams` | *"The screen reads the order off the state manager, so it takes no route arguments."* — the identical one-line KDoc in all three |
| `EndTripOtp` | `EndTripOtpParams(orderId)` ← `toRoute<EndTripOtp>().orderId` | the sheet's own call needs an id a restored stack must re-supply |
| `Cancellation` | `CancellationParams(cancelChainedOrder)` | which order is being cancelled is not derivable from the live state |
| `OrderEdits` | none — `edits` is passed straight to the composable | the pushed payload *is* the screen; `typeMap = mapOf(typeOf<List<OrderEdit>>() to OrderEditListNavType)`, base64url-wrapped JSON chosen so the deep-link matcher's decode pass is a no-op |
| `OrderEntryGate` | a **callback** dependency: `OrderEntryGateDependency(onExit = …)` | and so it is the one screen with **no component and no `di/` folder** — its VM comes from an assisted factory on `OrderJourneyComponent` |

The question to ask is not "what did the legacy params carry" but **"can the state hub answer
this?"** If yes, it is an `object`. If it is a fact that arrived with a push and must survive a
process death, it is a route argument.

Note also that `OrderDetail` is **not a nav destination at all** — it is mounted permanently inside
`navigation/OrderDetailsDrawer.kt` so its heavy composition survives every intra-journey navigation.

### The state hub

`domain/OrderJourneyStateManager` is the single writer. Every mutation serialises on
`appDispatchers.io.limitedParallelism(1)`; **persistence precedes emission**, so an observer of
`state` never sees a state that has not been written. `bootstrap()` rehydrates from the snapshot;
`dispatch(event)` advances the machine; `applyVicinity`/`rederive` re-resolve. The snapshot clears on
`Terminal` and on `Ended`.

### `Driver` events are post-outcome facts — this is the screen↔journey contract

```kotlin
internal sealed interface OlcStateMachineEvent {
  sealed interface Driver : OlcStateMachineEvent {
    data class MarkArrived(val timestamp: Long?) : Driver
    data class TripStarted(val timestamp: Long?) : Driver
    data class WaypointCompleted(val exitTimestamp: Long?) : Driver
    data class TripEnded(val fare: Fare?) : Driver
    data object AcknowledgementCollected : Driver
    data object Cancel : Driver
  }
  sealed interface Notif : OlcStateMachineEvent { /* decoded from the host's orderNotifications */ }
}
```

The acting ViewModel (or its coordinator) **makes the API call first, and dispatches the event only
after it succeeds**, carrying the response's own facts — server timestamps, the settled fare. The
machine bookkeeps those onto the order it already holds and advances **locally**. Nothing re-fetches
order details on the action path; a full re-fetch happens only at entry/restore and on an
order-update notification.

### The two event families have opposite failure policies

- **A `Driver` event on an illegal (state, event) pair `error()`s loudly.** Its validity is
  guaranteed by the UI that just made the call, so a violation is a bug in your migration.
- **A stale `Notif` event is dropped silently** via `ignoreStaleNotif(event, state)`. Pushes
  duplicate and reorder; that is normal.

Getting this backwards is a classic migration defect: swallow a bad Driver transition and the order
silently stops advancing; `error()` on a duplicate push and you crash a driver mid-trip.

(`Notif.UpdateOrder` is not a transition at all — it is resolved by re-running the derivation on the
re-fetched order. `updateOrderIsNotATransition(): Nothing` encodes that.)

The machine is split three ways, and keeping the split is what makes an in-session advance and a
restore's re-derivation identical:

| Piece | Role |
|---|---|
| `OlcStateMachine` | the holder — `var currState`, no I/O, no persistence |
| `LiveStateMachine` / `EndedWorkflow` | stateless policies. `LiveStateMachine` has **no constructor deps** — a pure policy over (state, event, vicinity) |
| `OrderJourneyStateManager` | the single writer: serialises, persists, emits |

Order bookkeeping lives in **file-private extension functions** on the machine
(`Order.withArrival(timestamp)`, `Order.advancedPastActive(exitTimestamp)`), not in a VM.

Three further rules fall out, and each is a parity trap if broken:

- **A screen never navigates itself** on an action's success. It dispatches; `render(state)` moves
  the route. (The OTP challenge is the exception, and it is navigation precisely because it is *not*
  a state change.)
- **The event carries the server's facts, not the client's clock.** `MarkArrived(timestamp)` is the
  server's arrival time — waiting-time billing reads it.
- **A failed call dispatches nothing.** The error path shows and reports (§5); the state is unmoved.

---

## 8. Persistence — process-death resume is real

`data/persistence/` (7 files, ~690 lines) over the host's `OLCStorageManager`
(`suspend put/get/remove(key)` — *"the host owns the storage; the library owns the serialization and
keys"*).

| File | Holds |
|---|---|
| `DatabaseSnapshot` + `SnapshotMappers` + `data/mapper/OrderPersistenceMappers` | the serialised journey snapshot |
| `DatabaseOrderStateRepository` → `domain/OrderStateRepository` | `load` / `update` / `clear`, one JSON blob at `"olc_active_order"` |
| `PrimaryActionEnableTimestampCache` | per-screen CTA cooldown deadlines, keyed `"$orderId:$screenUid"` |
| `ChainedAttachStore`, `P2cPopupImpressionStore`, `UnderpaymentAckStore` | one-shot / per-order facts the driver must not be re-asked |

Four conventions, each of which is a bug if ignored:

- **Persist an `Am` mirror, never a domain type.** Every persisted type has a `@Serializable`
  `XxxAm` twin (`OlcStateAm`, `VicinityInfoAm`, `StartTripRequestAm`). The order itself is stored as
  the **DTO wire payload**, not the domain `Order`. `OlcStateAm` stores only the *phase* and is
  reconstructed against the order on load.
- **Compat is defaulted fields plus read-compat records.** `WaypointScreenConfigAm.waitingTimeHeader
  = ""` so a snapshot written while that copy lived elsewhere still restores;
  `WaypointPhaseAm.VerifyOtp(source)` is *"kept for read-compat only — restores as Arrived and is
  never written anymore"*. A migration that renames a persisted field without a default silently
  breaks every driver mid-trip at upgrade.
- **A corrupt blob is removed, not retried.** Record the exception, `remove(KEY)`, read as absent —
  *"the journey bootstraps fresh from the server instead of failing every launch on the same bytes."*
  The read idiom is `runCatching { decode }.onFailure { RecordException }.getOrNull()`.
- **A "show this once per order" rule needs a store, not a `var`.** Three of the seven exist only
  because the legacy behaviour was once-per-order and a field resets on relaunch.
  `P2cPopupImpressionStore` also resets its slate when it sees a different order id, so it never
  grows.

## 8a. Other seams easy to re-derive wrongly

- **Clock.** `platform/DateTimeProvider` is injected. Never call `Clock.System` in a VM or section.
- **Coroutine failures.** `platform/coroutines/withOlcExceptionHandler()` wraps non-cancellation
  throwables in `OlcException` (keeping the original as `cause` so host crash grouping still sees
  the real type) and stamps `ProductComponentContext("driver-olc")`. The raw context is never
  injectable — see §3.
- **Toasts are non-cancellable on purpose** (`journeys/common/ui/ToastUtils`), so an error raised
  during scope teardown still reaches the driver.
- **`DialogImeInsets`** exists because a `journeyDialog<>` destination reports zero IME insets.
- **Use-case shape**: a single action gets `suspend operator fun invoke(Request): Response`. The
  grab-bag of reads and secondary calls is **one aggregate facade** (`LiveOrderActionsUseCase`, 9
  named methods) rather than nine one-method classes.

---

## 9. Conventions that are non-negotiable

- Package escape: `` package `in`.porter.olc.mobile.driver.… `` — every file, every import.
- **Everything is `internal`** except types under `contract/`, which the host consumes.
- kotlin-inject only: `me.tatarka.inject.annotations.{Inject, Component, Provides, KmpComponentCreate, Scope}`.
- Clients return **domain types**. DTOs never leave `data/`.
- `@SerialName` values copied from legacy verbatim, including error-type enum values.
- Two `Order` types exist: `data/dto/Order` (thin, has `orderId`) and `contract/entities/Order`
  (rich, domain). Requests use the **dto** one.
- Comment **why**, not what — and name the legacy source. The module's own comments are the reason
  a reader can tell a deliberate quirk from a bug: *"Legacy stack order (rib_order_waypoint.xml
  constraint chain): the generic server card sits ABOVE the schedule-slot card."*
- Keep comments under ~20 words (there was a cleanup commit for exactly this).
