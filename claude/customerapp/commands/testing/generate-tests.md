# Generate Cucumber Tests for Component

Generate a complete Cucumber test suite (Feature file + StepDefs + TestHelper + TestData) for any component type in the customerapp-shared project.

## Arguments

- **Source file paths** (required): One or more absolute paths to source `.kt` files to test, separated by spaces or newlines

## Instructions

### Step 0: Parse Input and Dispatch

Parse the input to extract all source file paths. If multiple files are provided:

1. **Dispatch parallel agents** — Use the Agent tool to spawn one subagent per file. Each subagent receives the full skill instructions (Steps 1–6) and a single file path.
2. **Each subagent independently** reads the source file, determines the component type, generates test files, and runs verification.
3. **Wait for all agents to complete**, then print a combined summary of all generated files.

If only a single file is provided, proceed directly to Step 1 without spawning subagents.

### Step 1: Read and Analyze the Source File

Read the source file at the provided path. Also read ALL constructor dependency types (their source files) to understand their APIs.

**For Interactors (RIB tests):** When the source file is an Interactor, you MUST also read all sibling RIB components in the same package/feature directory:
1. **State** data class (e.g., `{Feature}State.kt`) — understand all state fields, their types, nullability
2. **Params** data class (e.g., `{Feature}Params.kt`) — understand initialization/config values passed from parent
3. **Reducer** (e.g., `{Feature}StateReducer.kt`) — understand initial state values and all `update*()` methods
4. **VMMapper** (e.g., `{Feature}VMMapper.kt`) — understand ALL conditional mappings, nullable handling, formatting logic. This is critical for writing comprehensive VM assertions
5. **VM** data class (e.g., `{Feature}VM.kt`) — understand all VM fields, including nested helper VMs (e.g., `HeaderVM`, `ButtonVM`)
6. **Presenter** interface (e.g., `{Feature}Presenter.kt`) — understand all user action flows to build the FakePresenter
7. **Listener** interface (e.g., `{Feature}Listener.kt`) — understand parent callbacks
8. **Router** (e.g., `{Feature}Router.kt`) — understand child attach/detach methods
9. **All constructor dependencies** (repos, use cases, managers, etc.) — understand their APIs to mock them correctly

This ensures tests cover the full RIB lifecycle: user actions → handler logic → state updates → VM mapping → UI rendering.

Determine the **component type** from these categories:

| # | Type | Detection | Key Testing Focus |
|---|------|-----------|-------------------|
| 1 | **UseCase** | Class in `usecase/` or `usecases/` dir, has `operator fun invoke()` | Test return values based on dependency combinations |
| 2 | **RepoImpl** | Class name ends with `RepoImpl`, extends a Repo interface | Test `refresh()` / data flow, verify correct service calls and mapper usage |
| 3 | **HttpService** | Class name starts with `Http*Service` or is in `data/http/` dir | Test HTTP response parsing with MockEngine, test each API method |
| 4 | **Mapper** | Class name ends with `Mapper` or `VMMapper` | Test input→output transformations, conditional mappings |
| 5 | **Factory** | Class name ends with `Factory` or `RepoFactory` | Test object construction with various param combinations |
| 6 | **Reducer** | Class name ends with `Reducer`, extends `StateReducer` | Test state update methods, verify state transitions |
| 7 | **Manager** | Class name ends with `Manager` | Test coordination logic, verify dependency calls |
| 8 | **Tracker** | Class name ends with `Tracker` | Test event tracking, verify events recorded/not recorded |
| 9 | **Provider** | Class name ends with `Provider` | Test data provision logic, observable values |
| 10 | **DataSource** | Class name ends with `DataSource` | Test local/remote data access methods |
| 11 | **Handler** | Class name ends with `Handler` (standalone, not inner class) | Test handling logic, error cases |
| 12 | **Serializer** | Class name ends with `Serializer` | Test serialization/deserialization roundtrips |
| 13 | **Utils** | Class name ends with `Utils` or `Util` | Test utility methods with various inputs |
| 14 | **Client** | Class name ends with `Client` | Test external service wrapper methods |
| 15 | **Analytics** | Class name ends with `Analytics` (usually covered by RIB/interactor tests — only generate standalone tests if explicitly requested) | spyk the analytics class, call tracking methods, verify `recordEvent` called with correct event type and attributes |
| 16 | **Router** | Class name ends with `Router` | Test navigation logic, attach/detach flows |
| 17 | **Extensions** | File name ends with `Extensions` or `Ext` | Test extension functions with various inputs |
| 18 | **Interactor** | Class name ends with `Interactor`, extends `StateVMInteractor` or similar base | Test user interaction flows via FakePresenter, verify state transitions, analytics calls, listener/router delegation |
| 19 | **Listener (inner class)** | Inner class inside an Interactor, implements a `*Listener` interface | Test callback behavior when child components emit events, verify state updates and router/listener delegation |
| 20 | **Parser** | Class name ends with `Parser` | Test parsing of raw data (JSON, strings) into domain objects, edge cases with malformed/missing data |
| 21 | **ViewModel** | Class name ends with `ViewModel` (data class, not a VMMapper) | Test data class construction, equality, property access with DataTable inputs |

### Step 2: Determine File Paths

Derive paths from the source file location. Given a source file at:
```
shared/src/commonMain/kotlin/in/porter/customerapp/shared/{feature_path}/{ClassName}.kt
```

Generate files at:

1. **StepDefs** → `shared/src/test/kotlin/in/porter/customerapp/shared/tests/{feature_path}/{ClassName}StepDefs.kt`
2. **TestHelper** → `shared/src/test/kotlin/in/porter/customerapp/shared/tests/{feature_path}/{ClassName}TestHelper.kt`
3. **TestData** → `shared/src/test/kotlin/in/porter/customerapp/shared/tests/{feature_path}/{ClassName}TestData.kt` (only if test data objects are needed)
4. **Feature file** → `shared/src/test/resources/in/porter/customerapp/shared/tests/{feature_path_with_dots}/{snake_case_name}.feature`
5. **FakePresenter** → `shared/src/test/kotlin/in/porter/customerapp/shared/tests/{feature_path}/Fake{Feature}Presenter.kt` (only for Interactor tests)

**CRITICAL path rules:**
- The test kotlin package is `` `in`.porter.customerapp.shared.tests.{feature_path} `` (note: `tests` replaces the original package after `shared`)
- The feature file resource path mirrors test kotlin path but uses dots for package separators in directory names. Example: `loggedin/booking/` in source becomes `loggedin.booking/` in resources. **Read existing feature files in nearby directories to match the exact convention used in the project.**
- Feature file names use `snake_case.feature`
- Create all necessary parent directories

### Step 3: Generate Files by Component Type

---

#### TYPE 1: UseCase

**Reference:** `IsProofOfDeliveryFeatureEnabled` tests at `shared/src/test/.../vehicleselection/usecase/`

**TestHelper:**
```kotlin
class {ClassName}TestHelper {
  // Mock ALL constructor dependencies with mockk(relaxed = true)
  val dep1: Dep1Type = mockk(relaxed = true)
  val dep2: Dep2Type = mockk(relaxed = true)

  // Instantiate the usecase with mocked deps
  val useCase = {ClassName}(dep1, dep2)
}
```

**StepDefs:**
```kotlin
class {ClassName}StepDefs {
  private lateinit var testHelper: {ClassName}TestHelper

  @Given("{ClassName} test helper is setup")
  fun testHelperIsSetup() {
    testHelper = {ClassName}TestHelper()
  }

  @When("dependency X returns {string} and dependency Y returns {string}")
  fun setupDependencies(val1: String, val2: String) {
    coEvery { testHelper.dep1.someProperty } returns val1.toBoolean()
    coEvery { testHelper.dep2.someProperty } returns val2.toBoolean()
  }

  @Then("usecase should return {string}")
  fun usecaseShouldReturn(expected: String) {
    testHelper.useCase() shouldBeEqualTo expected.toBoolean()
  }
}
```

**Feature:** Test all combinations of dependency values (truth table for boolean usecases). For non-boolean usecases, test key return value scenarios.

---

#### TYPE 2: RepoImpl

**Reference:** `PorterRewardRepoImpl` tests at `shared/src/test/.../rewards/repo/`

**TestHelper:**
```kotlin
class {ClassName}TestHelper {
  val service: ServiceType = mockk(relaxed = true)
  val mapper: MapperType = spyk(MapperType()) // spyk for mappers to verify calls

  init {
    coEvery { service.fetchSomething() } returns TestData.fakeResponse
  }

  fun buildRepo(/* configurable params */): {ClassName} = {ClassName}(
    scope = EmptyCoroutineContext,
    service = service,
    mapper = mapper,
  )
}
```

**TestData:**
```kotlin
object {ClassName}TestData {
  val fakeResponse = SomeResponse(/* realistic test values */)
}
```

**StepDefs:**
- `@Given` - Setup test helper, build repo with specific flags/params
- `@And` - Setup specific mock returns for different scenarios
- `@When` - Call `runBlocking { repo.refresh() }` or other repo methods
- `@Then` - `coVerify` correct service methods called, `verify` mapper calls
- `@And` - `coVerify(exactly = 0)` that incorrect methods were NOT called

**Feature:** Test each branch in refresh/data flow. Verify correct services called AND incorrect ones NOT called.

---

#### TYPE 3: HttpService

**Reference:** `HttpPartLoadService` tests at `shared/src/test/.../partLoad/`

**TestHelper:**
```kotlin
class {ClassName}TestHelper {
  private val httpClientProvider: HttpClientProvider = mockk(relaxed = true)
  lateinit var httpService: {ClassName}

  fun setupMockHttpClient(statusCode: HttpStatusCode, response: String = "{}") {
    val engine = MockEngine {
      respond(
        content = response.encodeToByteArray(),
        status = statusCode,
        headers = headersOf(HttpHeaders.ContentType, ContentType.Application.Json.toString()),
      )
    }
    val client = HttpClient(engine)
    coEvery { httpClientProvider.get() } returns client
    httpService = {ClassName}(httpClientProvider)
  }
}
```

**TestData:**
```kotlin
object {ClassName}TestData {
  // JSON response strings matching the API response shape
  val successResponse = """{ "field1": "value1", "field2": 123 }""".trimMargin()
  // Request objects needed to call the service
  val testRequest = RequestType(/* values */)
}
```

**StepDefs:**
- `@Given` - Setup mock HTTP client with status code + response JSON
- `@Then` - Call service method in `runBlocking`, assert response fields with `assertEquals`

**Feature:** One scenario per API method. Test successful response parsing.

---

#### TYPE 4: Mapper / VMMapper

**Reference:** `VehicleDetailsVMMapper` tests at `shared/src/test/.../vehicledetails/`

**StepDefs (may not need separate TestHelper for simple mappers):**
```kotlin
class {ClassName}StepDefs {
  private val dep1: Dep1Type = mockk(relaxed = true)
  private lateinit var mapper: {ClassName}
  private lateinit var result: OutputType

  @Given("feature X is {string}")
  fun setupWithFeature(enabled: String) {
    every { dep1.someFlag } returns enabled.toBoolean()
    mapper = {ClassName}(dep1)
    result = mapper.map(inputData, inputState)
  }

  @Then("output should have field X as {string}")
  fun verifyOutput(expected: String) {
    assert(result.someField == expected)
  }
}
```

**Feature:** Test each conditional mapping path. Test with different input combinations to verify different output shapes.

---

#### TYPE 5: Factory

**StepDefs:** Test that factory creates correct objects with various input params.

**Feature:** One scenario per creation variant/configuration.

---

#### TYPE 6: Reducer

**Reference:** `GoodsV2InteractorStateReducer` tests at `shared/src/test/.../goodsv2/interactor/`

**StepDefs:**
```kotlin
class {ClassName}StepDefs {
  private lateinit var reducer: {ClassName}

  @Given("{ClassName} is initialized")
  fun setup() {
    reducer = {ClassName}()
  }

  @Then("initial state field X should be {string}")
  fun verifyInitialState(expected: String) {
    reducer.initState.fieldX shouldBeEqualTo expected
  }

  @When("update method is called with {string}")
  fun callUpdate(value: String) {
    runBlocking { reducer.updateFieldX(value) }
  }

  @Then("state field X should be {string}")
  fun verifyUpdatedState(expected: String) {
    // Access current state and verify
  }
}
```

**Feature:** Test initial state values. Test each `update*()` method produces correct state transitions.

---

#### TYPE 7: Manager

**Reference:** `NudgeManager` tests at `shared/src/test/.../nudge/`

**TestHelper:**
```kotlin
class {ClassName}TestHelper {
  val dep1: Dep1Type = mockk(relaxed = true)
  val dep2: Dep2Type = mockk(relaxed = true)
  val manager = {ClassName}(dep1, dep2)
}
```

**StepDefs:**
- `@Given` - Setup test helper
- `@When` - Configure mocks (e.g., remote config flags), call manager methods
- `@Then` - `coVerify` that correct dependency methods were/weren't called

**Feature:** Test manager behavior under different configuration flags. Verify correct delegation to dependencies.

---

#### TYPE 8: Tracker

**Reference:** `ApxorNudgeEventTracker` tests at `shared/src/test/.../apxor/`

**TestHelper:**
```kotlin
class {ClassName}TestHelper {
  // Expose tracking state for assertions
  var eventRecorded = false
  var eventName: String = ""
  var attrs: Map<String, Any>? = null

  fun setupAllowedEvents(events: List<String>) { /* ... */ }
  fun invokeTracker() { /* call tracker and capture result */ }
}
```

**StepDefs:**
- `@Given` - Setup tracker with allowed events/config
- `@When` - Invoke tracker with specific event name and attributes
- `@Then` - Assert event was recorded / not recorded

**Feature:** Test allowed vs disallowed events. Test with/without attributes.

---

#### TYPE 9: Provider

**TestHelper:** Similar to UseCase - mock dependencies, test data provision methods.

**Feature:** Test that provider returns expected data from dependencies under different conditions.

---

#### TYPE 10: DataSource

**TestHelper:** For remote data sources, similar to HttpService (mock HTTP). For local data sources, similar to UseCase pattern.

**Feature:** Test data fetch/store operations, caching behavior.

---

#### TYPE 11: Handler (standalone)

**Reference:** `ExceptionHandler` tests at `shared/src/test/.../base/`

**StepDefs:** Setup handler with mocked dependencies, invoke with different inputs, verify behavior.

**Feature:** Test handling of different input types, error cases, edge cases.

---

#### TYPE 12: Serializer

**Reference:** `CustomerTagSerializer` tests at `shared/src/test/.../network/model/`

**StepDefs:**
```kotlin
class {ClassName}StepDefs {
  private lateinit var serializedOutput: String
  private lateinit var deserializedResult: TargetType

  @Given("a {TargetType} with value {string}")
  fun givenValue(value: String) { /* setup */ }

  @When("it is serialized")
  fun serialize() {
    serializedOutput = Json.encodeToString({ClassName}(), targetValue)
  }

  @Then("the output should be {string}")
  fun verifyOutput(expected: String) {
    assertEquals(expected, serializedOutput.trim('"'))
  }

  @Given("a JSON string {string}")
  fun givenJson(json: String) { jsonInput = json }

  @When("it is deserialized")
  fun deserialize() {
    deserializedResult = Json.decodeFromString({ClassName}(), jsonInput)
  }

  @Then("the result should be {string}")
  fun verifyDeserialized(expected: String) {
    assertEquals(TargetType.valueOf(expected), deserializedResult)
  }
}
```

**Feature:** Test serialization roundtrips. Test each enum/variant value. Test edge cases (unknown values).

---

#### TYPE 13: Utils

**Reference:** `VehicleVariantUtils` tests at `shared/src/test/.../vehicleselection/usecases/`

**TestHelper:**
```kotlin
class {ClassName}TestHelper {
  // Setup methods for different input scenarios
  fun setupScenarioA() { /* prepare test data */ }
  fun setupScenarioB() { /* prepare test data */ }

  // Action methods
  fun callMethodX() { result = {ClassName}.methodX(inputData) }

  // Result accessors
  fun getResult(): ResultType = result
  fun isResultNull(): Boolean = result == null
}
```

**StepDefs:**
- `@Given` - Setup input data scenarios
- `@When` - Call utility methods with prepared data
- `@Then` - Assert results match expectations

**Feature:** Test each utility method with various inputs. Test edge cases (empty lists, null values, boundary values).

---

#### TYPE 14: Client

**TestHelper:** Similar to HttpService if HTTP-based. For SDK wrappers, mock the underlying SDK and verify calls.

**Feature:** Test each client method. Verify correct parameters passed to underlying service.

---

#### TYPE 15: Analytics

> **NOTE:** Analytics classes are usually tested as part of RIB/interactor test coverage. Only generate standalone analytics tests if the user explicitly requests it.

**TestHelper:**
```kotlin
class {ClassName}TestHelper {
  val eventRecorder: EventRecorder = mockk(relaxed = true)
  val eventPublisher: AnalyticsEventPublisher = mockk(relaxed = true)
  // spyk the analytics class so we can verify internal calls
  val analytics = spyk({ClassName}(eventRecorder = eventRecorder, eventPublisher = eventPublisher, /* other mocked deps */))
}
```

**StepDefs:**
```kotlin
class {ClassName}StepDefs {
  private lateinit var testHelper: {ClassName}TestHelper

  @Given("{ClassName} test helper is setup")
  fun testHelperIsSetup() {
    testHelper = {ClassName}TestHelper()
  }

  @When("track method X is called")
  fun trackMethodXIsCalled() {
    testHelper.analytics.trackMethodX(/* params */)
  }

  @Then("event should be recorded with name {string}")
  fun eventShouldBeRecorded(eventName: String) {
    verify { testHelper.analytics.recordEvent(match { it.eventIdentifiers.eventName == eventName }) }
  }
}
```

**Feature:** One scenario per tracking method. Verify event names and key attributes.

---

#### TYPE 16: Router

**StepDefs:** Test navigation logic. Verify correct child attachment/detachment based on state/actions.

**Feature:** Test each navigation path (attach, detach, goBack).

---

#### TYPE 17: Extensions

**StepDefs:** Test each extension function with various input values.

**Feature:** One scenario per extension function, testing key input/output combinations.

---

#### TYPE 18: Interactor

**Reference:** `PodAcknowledgementInteractor` tests at `shared/src/test/.../podacknowledgement/`

Interactor tests require three supporting files: **TestHelper**, **FakePresenter**, and **StepDefs**. The Interactor is the most complex component type — it orchestrates presenter events, state transitions, analytics, listener callbacks, and router navigation.

**FakePresenter** (required — create alongside TestHelper):
```kotlin
class Fake{Feature}Presenter : {Feature}Presenter {
  var lastRenderedVM: {Feature}VM? = null
    private set

  // MutableSharedFlow for each user action
  private val actionTaps = newMutableSharedFlow<Unit>()
  private val inputChanges = newMutableStateFlow<String?>(null)

  // Public methods to simulate user interactions
  fun tapAction() { actionTaps.tryEmit(Unit) }
  fun updateInput(value: String?) { inputChanges.tryEmit(value) }

  // Implement presenter interface methods
  override fun didTapAction(): Flow<Unit> = actionTaps.asSharedFlow()
  override fun inputChanged(): Flow<String> = inputChanges.filterNotNull()
  override fun render(vm: {Feature}VM) { lastRenderedVM = vm }
}
```

**Key imports for FakePresenter:**
- `` `in`.porter.kmputils.commons.newMutableSharedFlow ``
- `` `in`.porter.kmputils.commons.newMutableStateFlow ``
- `` `in`.porter.kmputils.commons.newMutableReplaySharedFlow ``
- `` `in`.porter.kmputils.commons.ui.analytics.ActionWithAttributes ``
- `` `in`.porter.kmputils.commons.ui.analytics.ActionableViewType.CLICKABLE ``
- `` `in`.porter.kmputils.commons.ui.analytics.toActionWithAttributes ``

**TestHelper:**
```kotlin
class {Feature}TestHelper {
  @OptIn(ExperimentalCoroutinesApi::class)
  val dispatcher = UnconfinedTestDispatcher()
  val presenter = Fake{Feature}Presenter()
  val listener: {Feature}Listener = mockk(relaxed = true)
  val router: {Feature}Router = mockk(relaxed = true)
  val reducer = {Feature}StateReducer(dispatcher)
  val vmMapper = {Feature}VMMapper()
  private val eventRecorder = mockk<EventRecorder>(relaxed = true)
  val analytics: {Feature}Analytics = spyk({Feature}Analytics(eventRecorder))

  fun buildInteractor(): {Feature}Interactor {
    return {Feature}Interactor(
      dispatcher = StateVMInteractorDispatchers(dispatcher, dispatcher, dispatcher),
      coroutineExceptionHandler = FakeCoroutineExceptionHandlerProvider(
        mockk(relaxed = true), FakeAppLanguageRepo(),
      ).buildInteractorCoroutineExceptionHandler(),
      reducer = reducer,
      vmMapper = vmMapper,
      presenter = presenter,
      listener = listener,
      analytics = analytics,
      // ... other deps as mockk(relaxed = true)
    ).also { it.router = router }
  }
}
```

**StepDefs:**
```kotlin
class {Feature}InteractorStepDefs {
  private lateinit var testHelper: {Feature}TestHelper
  private lateinit var interactor: {Feature}Interactor

  @Given("{Feature} screen is setup")
  fun setup() {
    testHelper = {Feature}TestHelper()
    interactor = testHelper.buildInteractor()
  }

  @Given("the {Feature}Interactor is active")
  fun activate() {
    interactor.didBecomeActive()
  }

  @When("the user taps action X")
  fun tapAction() {
    testHelper.presenter.tapAction()
  }

  @Then("state field X should be {string}")
  fun verifyState(expected: String) {
    interactor.currState.fieldX shouldBeEqualTo expected
  }

  // --- VM stream assertions ---

  @Then("vm field X should be {string}")
  fun verifyVM(expected: String) {
    interactor.vmStream.value.fieldX shouldBeEqualTo expected
  }

  // Nested/helper VM assertions — when the VM contains inner data classes
  // e.g., VM has headerVM: HeaderVM, buttonVM: ButtonVM, etc.
  @Then("{Feature} vm headerVM title should be {string}")
  fun verifyHeaderTitle(expected: String) {
    interactor.vmStream.value.headerVM.title shouldBeEqualTo expected
  }

  @Then("{Feature} vm buttonVM isEnabled should be {string}")
  fun verifyButtonEnabled(expected: String) {
    interactor.vmStream.value.buttonVM.isEnabled shouldBeEqualTo expected.toBoolean()
  }

  @Then("{Feature} vm buttonVM text should be {string}")
  fun verifyButtonText(expected: String) {
    interactor.vmStream.value.buttonVM.text shouldBeEqualTo expected
  }

  // --- Analytics / Listener / Router assertions ---

  @Then("analytics event X should be recorded")
  fun verifyAnalytics() {
    verify { testHelper.analytics.trackEventX(any()) }
  }

  @Then("listener callback X should be invoked")
  fun verifyListener() {
    coVerify { testHelper.listener.onCallbackX() }
  }

  @Then("router should attach child X")
  fun verifyRouter() {
    coVerify { testHelper.router.attachChildX(any()) }
  }
}
```

**Feature:** Test each user interaction flow end-to-end:
- User taps → state updates correctly
- User taps → VM reflects correct mapped values (validate ALL VM fields, including nullables)
- User taps → nested/helper VM fields update correctly (e.g., `headerVM.title`, `buttonVM.isEnabled`)
- State change → VM inner data class fields change accordingly
- Different params → VM reflects correct initial values
- Nullable VM fields → test both null and non-null cases
- User taps → analytics recorded
- User taps → listener/router delegation
- Submit without required state → nothing happens
- Dismiss/back actions → correct cleanup

**CRITICAL: Never update state directly — always follow production flow:**

Tests MUST trigger state changes the same way production code does. If the interactor listens to a stream, filters data, and writes to state via a Handler, the test must:
1. Mock the dependency that provides the stream/data
2. Trigger the flow (e.g., `interactor.didBecomeActive()` or simulate a presenter event)
3. Let the Handler logic run and update state naturally
4. Then assert on `interactor.currState` and `interactor.vmStream.value`

**❌ BAD — directly updating state via reducer:**
```kotlin
@When("state is updated with selected vehicle")
fun updateState() {
  // ❌ NEVER DO THIS — bypasses production logic (filtering, validation, etc.)
  runBlocking { testHelper.reducer.updateSelectedVehicle(vehicle) }
}
```

**✅ GOOD — triggering the actual production flow:**
```kotlin
@Given("{Feature} dependency returns vehicle list")
fun setupDependency() {
  // Mock the dependency that the Handler reads from
  coEvery { testHelper.vehicleRepo.getVehicles() } returns listOf(testVehicle)
}

@When("{Feature} screen becomes active")
fun activate() {
  // Handler in didBecomeActive() will call repo, filter, and update state
  interactor.didBecomeActive()
}

@When("user selects vehicle at index {int}")
fun selectVehicle(index: Int) {
  // Simulate the actual user action via FakePresenter
  testHelper.presenter.selectVehicle(index)
}

@Then("{Feature} vm selectedVehicleName should be {string}")
fun verifyVM(expected: String) {
  interactor.vmStream.value.selectedVehicleName shouldBeEqualTo expected
}
```

**VM validation strategy:**

The VM is produced by the VMMapper from State + Params. Tests must comprehensively validate VM fields because the VMMapper may have conditional logic (nullables, formatting, visibility flags, etc.):

1. **Read the VMMapper source** to understand all conditional mappings
2. **Test each conditional path** — e.g., if VMMapper shows/hides a field based on a nullable state field, test both null and non-null cases
3. **Validate ALL VM fields** in each scenario, not just the field being changed — other fields may be affected by the same state change
4. **Test with different Params** if VMMapper uses params for mapping (e.g., feature flags, config values)
5. **Nested/helper VMs** — write assertions for each inner VM's fields (e.g., `interactor.vmStream.value.headerVM.title`, `interactor.vmStream.value.buttonVM.isEnabled`)

**Key testing principles for Interactors:**
1. Always call `interactor.didBecomeActive()` before simulating user interactions
2. Use the FakePresenter to emit events (NOT mockk — presenters use Flow-based APIs)
3. **NEVER call reducer methods directly** to set up state — always mock dependencies and trigger the actual production flow (presenter events, `didBecomeActive()`, mock stream emissions) that causes the Handler to update state
4. Access state via `interactor.currState` for state assertions
5. Access VM via `interactor.vmStream.value` for VM assertions — validate both top-level and nested VM fields (helper VMs like `headerVM`, `buttonVM`, etc.)
6. When the VM contains nested data classes (helper VMs), write separate step defs for each inner VM's fields to verify that state-to-VM mapping is correct
7. Use `verify {}` for analytics, `coVerify {}` for listener/router calls
8. Use `spyk()` for analytics (to verify `recordEvent` calls on a real instance)
9. Use `mockk(relaxed = true)` for listener and router

---

#### TYPE 19: Listener (inner class)

**Reference:** `LocationDetailsBottomListenerImpl` tests at `shared/src/test/.../locationdetails/interactor/`

Listener tests verify the behavior of inner `*ListenerImpl` classes inside Interactors — these handle callbacks from child components.

**TestHelper** (reuse the parent Interactor's TestHelper if it exists, or create one):
```kotlin
class {ListenerName}ImplTestHelper {
  @OptIn(ExperimentalCoroutinesApi::class)
  val dispatcher = UnconfinedTestDispatcher()
  val presenter = Fake{Feature}Presenter()
  val listener: {Feature}Listener = mockk(relaxed = true)
  val router: {Feature}Router = mockk(relaxed = true)
  val reducer = {Feature}StateReducer(dispatcher)
  val vmMapper = {Feature}VMMapper()
  private val eventRecorder = mockk<EventRecorder>(relaxed = true)
  val analytics: {Feature}Analytics = spyk({Feature}Analytics(eventRecorder))
  lateinit var interactor: {Feature}Interactor
  lateinit var childListener: {Feature}Interactor.{ListenerName}Impl

  fun buildAndActivate() {
    interactor = {Feature}Interactor(
      dispatcher = StateVMInteractorDispatchers(dispatcher, dispatcher, dispatcher),
      // ... other deps
      presenter = presenter,
      listener = listener,
      analytics = analytics,
    ).also { it.router = router }
    interactor.didBecomeActive()
    childListener = interactor.{ListenerName}Impl()
  }
}
```

**StepDefs:**
```kotlin
class {ListenerName}ImplStepDefs {
  private lateinit var testHelper: {ListenerName}ImplTestHelper

  @Given("{ListenerName}Impl test helper is setup and interactor is active")
  fun setup() {
    testHelper = {ListenerName}ImplTestHelper()
    testHelper.buildAndActivate()
  }

  @When("{ListenerName}Impl onSomeCallback is invoked")
  fun invokeCallback() {
    testHelper.childListener.onSomeCallback()
  }

  @When("{ListenerName}Impl onAnotherCallback is invoked with test data")
  fun invokeCallbackWithData() {
    testHelper.childListener.onAnotherCallback(TestData.someValue)
  }

  @Then("interactor state field X should be {string}")
  fun verifyState(expected: String) {
    testHelper.interactor.currState.fieldX shouldBeEqualTo expected
  }

  @Then("router should attach child component")
  fun verifyRouterAttach() {
    coVerify { testHelper.router.attachSomeChild(any()) }
  }

  @Then("parent listener onParentCallback should be invoked")
  fun verifyParentListener() {
    verify { testHelper.listener.onParentCallback(any()) }
  }

  @Then("keyboard should be hidden")
  fun verifyKeyboardHidden() {
    verify { testHelper.uiUtility.hideKeyboard() }
  }
}
```

**Feature:**
```gherkin
Feature: {ListenerName}Impl

  Background:
    Given {ListenerName}Impl test helper is setup and interactor is active

  Scenario: onSomeCallback updates state and attaches child
    When {ListenerName}Impl onSomeCallback is invoked
    Then interactor state field X should be "expectedValue"
    And router should attach child component

  Scenario: onAnotherCallback delegates to parent listener
    When {ListenerName}Impl onAnotherCallback is invoked with test data
    Then parent listener onParentCallback should be invoked
```

**Key testing principles for Listeners:**
1. Always use Cucumber (StepDefs + Feature file), not Spek2
2. Access inner class via `interactor.{ListenerName}Impl()`
3. Always call `interactor.didBecomeActive()` before accessing the listener
4. Test each callback method: state updates, router calls, parent listener delegation
5. Use `coVerify` for suspend functions, `verify` for non-suspend

---

#### TYPE 20: Parser

**Reference:** `GoodsV2JsonParser` tests at `shared/src/test/.../goodsv2/data/`

**StepDefs:**
```kotlin
class {ClassName}StepDefs {
  private lateinit var payload: JsonObject
  private var parsedResult: ResultType? = null

  @Given("{ClassName} json payload:")
  fun setPayload(doc: String) {
    payload = Json.parseToJsonElement(doc).jsonObject
  }

  @When("json is parsed")
  fun parsePayload() {
    parsedResult = {ClassName}.parse(payload)
  }

  @Then("parsed field X count should be {int}")
  fun assertCount(expected: Int) {
    assertEquals(expected, parsedResult?.items?.size)
  }

  @Then("parsed result should be null")
  fun assertNull() {
    assertEquals(null, parsedResult)
  }

  @Then("parsed field X should be min {int} max {int} default {int}")
  fun assertRange(min: Int, max: Int, def: Int) {
    assertEquals(Triple(min, max, def), Triple(parsedResult?.min, parsedResult?.max, parsedResult?.default))
  }
}
```

**Feature:** Use `Doc String` (triple quotes) in Gherkin to pass JSON payloads:
```gherkin
Feature: GoodsV2JsonParser

  Scenario: Parse valid payload
    Given GoodsV2JsonParser json payload:
      """
      { "types": [{"id": 1, "name": "Electronics"}], "defaults": [1] }
      """
    When json is parsed
    Then parsed field X count should be 1

  Scenario: Parse empty payload
    Given GoodsV2JsonParser json payload:
      """
      {}
      """
    When json is parsed
    Then parsed result should be null
```

**Key testing principles for Parsers:**
1. Test with valid, minimal, empty, and malformed payloads
2. Use Gherkin Doc Strings for inline JSON
3. Verify counts, field values, and null/missing data handling
4. Test each parse method separately if the parser has multiple methods

---

#### TYPE 21: ViewModel (data class)

**Reference:** `LogoutConfirmationViewModel` tests at `shared/src/test/.../logout/view/`

> **NOTE:** This is for ViewModel **data classes** (simple data containers). For VMMappers (transformation logic), use TYPE 4.

**StepDefs:**
```kotlin
class {ClassName}StepDefs {
  private var viewModel: {ClassName}? = null
  private var firstViewModel: {ClassName}? = null
  private var secondViewModel: {ClassName}? = null

  @When("creating a {ClassName} with the following properties:")
  fun createViewModel(dataTable: DataTable) {
    val properties = dataTable.asMap(String::class.java, String::class.java)
    viewModel = {ClassName}(
      field1 = properties["field1"] ?: "",
      field2 = properties["field2"] ?: "",
    )
  }

  @When("creating two identical {ClassName}s")
  fun createTwoIdentical() {
    firstViewModel = {ClassName}(field1 = "Same", field2 = "Same")
    secondViewModel = {ClassName}(field1 = "Same", field2 = "Same")
  }

  @When("creating two different {ClassName}s")
  fun createTwoDifferent() {
    firstViewModel = {ClassName}(field1 = "First", field2 = "First")
    secondViewModel = {ClassName}(field1 = "Second", field2 = "Second")
  }

  @Then("the {ClassName} should have field1 {string}")
  fun verifyField(expected: String) {
    assertEquals(expected, viewModel?.field1)
  }

  @Then("they should be equal")
  fun verifyEqual() {
    assertEquals(firstViewModel, secondViewModel)
    assertEquals(firstViewModel?.hashCode(), secondViewModel?.hashCode())
  }

  @Then("they should not be equal")
  fun verifyNotEqual() {
    assertNotEquals(firstViewModel, secondViewModel)
  }
}
```

**Feature:** Use Cucumber `DataTable` for property-based construction:
```gherkin
Feature: LogoutConfirmationViewModel

  Scenario: Create ViewModel with properties
    When creating a LogoutConfirmationViewModel with the following properties:
      | title            | Log Out?          |
      | subtitle         | Are you sure?     |
      | cancelButtonText | Cancel            |
      | confirmButtonText| Confirm           |
    Then the LogoutConfirmationViewModel should have title "Log Out?"
    And the LogoutConfirmationViewModel should have subtitle "Are you sure?"

  Scenario: Equality of identical ViewModels
    When creating two identical LogoutConfirmationViewModels
    Then they should be equal

  Scenario: Inequality of different ViewModels
    When creating two different LogoutConfirmationViewModels
    Then they should not be equal
```

**Key testing principles for ViewModels:**
1. Test property construction via DataTable
2. Test data class equality and hashCode
3. Test with edge case values (empty strings, special characters)
4. No mocks needed — these are pure data classes

---

### Step 4: Code Style Rules

1. **Package names** use backtick-escaped `in`: `` `in`.porter.customerapp.shared.tests.{path} ``
2. **Imports (Cucumber tests):**
   - `io.cucumber.java.en.Given`, `io.cucumber.java.en.When`, `io.cucumber.java.en.Then`, `io.cucumber.java.en.And`
   - `io.mockk.mockk`, `io.mockk.coEvery`, `io.mockk.every`, `io.mockk.coVerify`, `io.mockk.verify`, `io.mockk.spyk`
   - `org.amshove.kluent.shouldBeEqualTo`, `org.amshove.kluent.shouldBe`, `org.amshove.kluent.shouldBeTrue`, `org.amshove.kluent.shouldBeFalse` (preferred assertions)
   - Or `kotlin.test.assertEquals`, `org.junit.Assert.assertEquals` (alternative)
   - `kotlinx.coroutines.runBlocking` (for suspend functions)
   - `kotlin.coroutines.EmptyCoroutineContext` (for repos needing CoroutineContext)
3. **No `runTest {}`** - use `runBlocking` instead (runTest never completes on CI/CD)
4. **No Spek2** - always use Cucumber (StepDefs + Feature file) for all new tests. Never use `Spek`, `describe/it`, or `by memoized`. Legacy Spek2 tests exist in the codebase but all new tests must use Cucumber.
5. **Indent:** 2 spaces
6. **Trailing commas:** Allowed
7. **AAA pattern strictly:**
   - `@Given` = Arrange only (setup)
   - `@When` / `@And` after When = Act only (execute behavior)
   - `@Then` / `@And` after Then = Assert only (verify)
8. **Feature file:** Use `Background` for common setup, separate `Scenario` for each test case
9. **Step text:** Make step definitions unique and descriptive. Include the class name in `Background` Given steps to avoid conflicts with other step defs.
10. **TestBuilder vs TestHelper:** Some features use `*TestBuilder` (object with `build*()` factory methods) instead of `*TestHelper` (class with mocked deps as properties). Check if a TestBuilder already exists for the feature before creating a TestHelper. Use the same pattern as nearby tests.
11. **FakePresenter:** Required for Interactor tests. Implements the Presenter interface with `MutableSharedFlow`/`MutableStateFlow` to simulate user events. Never mock a Presenter with mockk — use a Fake implementation instead.
12. **No inline mock configuration:** Never use `mockk(relaxed = true) { every { invoke() } returns value }` — Kotlin cannot infer type arguments inside the mockk lambda. Instead, use plain `mockk(relaxed = true)` and configure return values separately in `@Given` steps if needed.

### Step 5: Generate and Write Files

1. Read the source file and ALL its constructor dependencies (read their source files too to understand their API surface — properties, methods, return types). **For Interactors:** also read all sibling RIB components as described in Step 1 (State, Params, Reducer, VMMapper, VM, Presenter, Listener, Router)
2. Determine component type from the table above
3. Generate all test files following the matching type pattern
4. Write the files to the correct paths (create directories if needed)
5. Print a summary of generated files with full paths

### Step 6: Done

After generating all test files, print a summary of the generated files with full paths, then tell the user:

> I have written the tests. Please run the test coverage command to test the coverage. If you face any compile issues, please do share and I'll fix them.

## Example Usage

### Single file
```
/generate-tests /path/to/CanUseRewardsBannerV2Api.kt
```

Generates:
- `CanUseRewardsBannerV2ApiStepDefs.kt`
- `CanUseRewardsBannerV2ApiTestHelper.kt`
- `can_use_rewards_banner_v2_api.feature`

### Multiple files (processed in parallel)
```
/generate-tests /path/to/CanUseRewardsBannerV2Api.kt /path/to/PorterRewardRepoImpl.kt /path/to/HttpRewardBannerService.kt
```

Generates tests for all three files simultaneously using parallel agents, then prints a combined summary.
