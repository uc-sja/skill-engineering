# The host stitch — wiring OLC into DriverAppV3

Measured on `DriverAppV3@tests/screenshot_test`, package
`app/src/main/java/com/theporter/android/driverapp/order/olc/` (9 files, 753 lines, untracked).

**Status today: the stitch is written but not compiled.** The dependency line in
`app/build.gradle.kts` (~`:586-590`) is commented out pending the library publish, so nothing under
`order/olc/` is on the build path. Treat every signature in it as *unverified against the real
contract* until that line is live — the one member already corrected this way was
`newMessageSignal()`, which was written as a `val` and is a function.

---

## The template is `order/allocation` (FuryLite)

Every file in `order/olc/` states this explicitly: the strings provider mirrors
`FuryLiteStringsProviderImpl.kt`, the module mirrors `MobileAllocationModule` 1:1, the dependency
coordinate mirrors `AllocationMobile`. **Read that package first.** A migration that invents its own
host shape is re-deriving a solved problem and will diverge on the details that matter (scoping,
error reporting, Dagger installation).

---

## 1. Declare the dependency

`buildSrc/src/main/kotlin/Libs.kt`:

```kotlin
private const val mobileDriverOlcVersion = "0.1.0"
object MobileDriverOlc { val Lib = "in.porter.olc:mobile-driver-olc:$mobileDriverOlcVersion" }
```

`app/build.gradle.kts`: `implementation(Libs.Android.Main.MobileDriverOlc.Lib)`.

Same composite-`includeBuild` substitution scheme as `AllocationMobile` and `Telemetry` — the
published coordinate is replaced by the local project during local dev. The module transitively
exposes the `in.porter.kmputils:*` artifacts (`commons`, `core-ui`, `analytics`), so **reuse those
directly inside OLC rather than re-adapting them at the seam.**

## 2. One Dagger `@Module`, installed in `AppComponent`

`OlcModule.kt` — every binding is `@Singleton @Provides fun provideX(impl: XImpl): X = impl`.
Then **two lines in `AppComponent.kt`**: the import, and `OlcModule::class` in the
`@Component(modules = […])` list, next to `MobileAllocationModule::class`.

> Forgetting the `AppComponent` edit fails at the **consumer** (`OlcPlatformDependency` "cannot be
> provided"), not at the module. Put the warning in the module header, as this one does.

## 3. The two dependency surfaces

The library splits what the host supplies in two, and the split is load-bearing:

| Surface | Supplied at | Holds |
|---|---|---|
| `OlcPlatformDependency` (6 members) | `OlcManagerBuilder.create(...)` | only what the **headless** order spine needs: `httpClientProvider`, `storageManager`, `eventRecorder`, `logger`, `appDispatchers`, `coroutineContext` |
| `OlcJourneyDependency` (13 members) | `addOlcGraph(...)` | everything only the **rendered** journey consumes: `stringsProvider`, `externalActions`, `platformResource`, `platformRinger`, `hasUnreadChat`, `orderNotifications`, `incogniaLogger`, `olcFeatureFlagProvider`, `olcPlatformDataProvider`, `olcConfigs`, `driverLocationManager`, `locationUploader`, `orderDestinationPublisher` |

A host can therefore build `OlcManager` and answer `hasActiveOrder()` — and keep the snapshot and
background replay working — with **no UI wiring at all**. Do not fold a journey capability into
`OlcPlatformDependency` to make a constructor shorter; that re-couples the headless path to the UI.

`*DependencyImpl` is a **pure passthrough**: constructor params prefixed `platform*`, members exposed
via `get()`, zero logic.

## 4. The dependency-direction rule

OLC has no reverse dependency on the host, but it *does* depend on kmp-utils. So:

- **kmp-utils-typed and carries host state** (`EventRecorder`, `ConnectivityListener`,
  `PlatformResource`) → **forward the app's existing binding**. Never write an adapter. There is no
  analytics adapter in `order/olc/` for exactly this reason: `eventRecorder` is injected straight
  from the app graph and handed over as-is.
- **kmp-utils-typed and stateless** (`Logger`, `AppDispatchers`) → construct inline, and push back on
  the library owner to drop it from the contract.

## 5. Entry point: a Compose nav-graph, not an Activity/Fragment/RIB

```kotlin
@Singleton
class OlcJourneyHost @Inject constructor(private val platformDependency: OlcPlatformDependency) {
  private val olcManager: OlcManager by lazy { OlcManagerBuilder.create(platformDependency).build() }
  fun NavGraphBuilder.registerOlcGraph(navController: NavController, onJourneyComplete: () -> Unit) { … }
  fun enterOlcJourney(navController: NavController) { navController.navigate(OlcJourneyGraph) }
}
```

`addOlcGraph` must be called **inside the host's root `NavHost { }` block** — it registers
`OlcJourneyGraph` as a nested graph, and everything inside it is an implementation detail. The
journey reports completion through `onJourneyComplete`, which pops the journey off the controller.

Entry is gated on `olcManager.hasActiveOrder()`.

## 6. Strings: the host owns the key→type map

OLC ships **zero copy**. The provider has one `provideXxxStrings()` per screen, returning a
`contract/resources/<X>Strings` data class. The host implementation sources each field from one of
three tiers:

```kotlin
class OlcStringsProviderImpl @Inject constructor(
  private val stringsRepo: StringsRepo,      // vernac dictionary, per current locale
  private val application: MainApplication,  // for app-global @string resources
) : OlcStringsProvider {
  override fun provideEndTripOtpStrings(): EndTripOtpStrings {
    val screen = stringsRepo.getScreenStrings<CollectOtpV2Strings>(PartnerStringMapperImplView.COLLECT_OTP_V_2)
    val root   = stringsRepo.getScreenStrings<RootStrings>(PartnerStringMapperImplView.ROOT)
    return EndTripOtpStrings(
      …,                                       // 1. the screen's own vernac bundle
      networkError = root.networkError,        // 2. RootStrings, for shared error banners
      loaderMessage = application.getString(R.string.loader_message), // 3. an Android resource
    )
  }
}
```

**OLC never hardcodes a vernac key.** The library ships the *shape*; the host maps legacy's
`PartnerStringMapperImplView.<KEY>` onto it. That is also why a screen-split divergence (one legacy
RIB → two OLC screens) costs the host nothing: two accessors reading two legacy keys.

Placeholders travel unfilled: the catalogue writes `#arg1`, `#arg2`, and the library fills them with
`String.withArgs(...)` (`journeys/common/HostStringArgs.kt`). Matching only the exact `#argN` token
is deliberate — the catalogue carries colours in the same `#` notation. An unsupplied argument leaves
its placeholder rather than failing.

## 7. Configs: remote config behind a total fallback

`OlcConfigs` is a plain data class of numbers with defaults and a KDoc on each naming the exact
legacy remote-config key and its resolved value. The host builds it from `RemoteConfigRepo`:

```kotlin
fun provideOlcConfigs(remoteConfigRepo: RemoteConfigRepo): OlcConfigs =
  runCatching {
    val rc = remoteConfigRepo.remoteConfig
    OlcConfigs(locationUploadIntervalMs = …, tapDebounceMs = rc.debounceTimeoutInMillis, …)
  }.getOrElse { OlcConfigs(locationUploadIntervalMs = DEFAULT) }
```

**A remote-config failure must never break library startup** — hence `runCatching { … }.getOrElse`.
Numeric tuning goes on `OlcConfigs`; **gates go on `OlcFeatureFlagProvider`**, where every flag is a
`fun` (not a `val`) so each read hits the host's store at the moment of the call and a
snapshot-at-construction implementation is impossible to write by accident.

## 8. HTTP: two already-authenticated Ktor clients

`OlcHttpClientProvider` exposes `gatewayClient()` and `omsClient()` from the host's `RemoteModule`.
Routing is a property of the endpoint, and the library encodes it (`OlcReplayClient` replays each
endpoint on the client it was issued on): `start_trip` / `verify_otp` / `resend_otp` on the gateway,
`waypoint_complete` / `end_trip` on OMS.

## 9. Rx→contract bridging must **report**, never swallow

```kotlin
// WRONG — the empty consumer consumes the error, so it never becomes an undeliverable
// Rx error and RxPluginErrorHandler never sees it either. The failure vanishes.
audioAssistant.playAudio(url, freq).subscribe({ }, { })

// RIGHT
audioAssistant.playAudio(url, freq).subscribe({ }, { errorProcessor.process(it) })
```

Non-suspend contract methods wrapping suspend/Rx host APIs launch on
`CoroutineScope(coroutineContext + SupervisorJob())`.

## 10. The Activity-scope problem — decide it once, up front

`@Singleton` adapters cannot hold an Activity, but scanner, liveness, in-app review and SOS all
attach RIBs or need the foreground Activity. The current wiring invents:

```kotlin
interface CurrentActivityProvider {
  fun rootViewGroup(): ViewGroup?
  fun pdfCaptureManager(): PDFCaptureManager?
  fun inAppReviewManager(): InAppReviewManager?
}
```

This is the single biggest structural gap in the host stitch. The alternative is an Activity-scoped
subcomponent. Either is defensible; drifting between them per-adapter is not.

## 11. Placeholders throw loudly

```kotlin
override suspend fun put(key: String, value: String) =
  error("LocalStorageManager not wired — bind SharedPreferences/DataStore")
```

Silent wrong data is worse than a crash in a build nobody ships yet. The exception is where a no-op
is the behaviourally **correct** interim — `DriverLocationUploaderImpl` returns `flowOf(false)`
because the host keeps uploading location itself until that path migrates.

## 12. Keep a `WIRING_MANIFEST.md` next to the adapters

One table of every contract member with a "compiles once the dep exists?" column, plus a numbered
list of genuine gaps and the owner-gate (which PRs must merge and publish before the
`build.gradle.kts` line can be uncommented). Every inline `TODO(host)` has a row in it.

---

## What is NOT the host's, and what is not OLC's

- **The order-cancelled sheet stays in DriverAppV3** and is not being ported. The push arrives at the
  host, not at OLC: `ActivityNotificationHandler.showOrderCancelledPopup` attaches
  `CancellationNotificationBottomSheetParams` through `MainActivity → RootRibNavController →
  LoggedIn`. OrderFlow — the layer OLC replaces — has **zero** attach sites in that chain. OLC
  receives the same push as an `OrderNotification` and forwards only `alert` to the state machine;
  the attribution rides along for the host's screen.
- **Payment, rating and the thank-you sheet are phase two** and currently the host's.
  `OrderEntryGateAction` exits the journey on `Ended` precisely so the driver is not stranded on the
  waypoint after end-trip; the handback carries `OlcResult.EndedHandoff(order, fare, phase)`.
- **There is no OLC-vs-legacy switch in the host today.** The only fallback path is
  `OlcResult.NotEligible`, and the rollout flag (`mobile_olc_full_rollout`) exists only in a comment.
  Do not assume a gate exists because the migration implies one.
