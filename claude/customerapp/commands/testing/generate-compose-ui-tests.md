# Generate Compose UI Tests
# Created by Birendra Sharma

Generate a complete Compose UI test file for any ComposeView using ComposeTestRule, test tags, and event callback verification.

## Arguments

- **ComposeView file path** (required): Absolute path to the `*ComposeView.kt` file to test

## Instructions

### Step 0: Parse Input and Dispatch

Parse the input to extract the ComposeView file path. If multiple files are provided:

1. **Dispatch parallel agents** — Use the Agent tool to spawn one subagent per file. Each subagent receives the full skill instructions (Steps 1-7) and a single file path.
2. **Each subagent independently** reads the source file, discovers sibling files, generates the test, and runs verification.
3. **Wait for all agents to complete**, then print a combined summary.

If only a single file is provided, proceed directly to Step 1.

### Step 1: Read and Analyze the ComposeView

Read the ComposeView file AND discover all related sibling files in the same feature directory.

#### 1.1 Files to Read (in order)

1. **ComposeView** (provided path) — Extract:
   - Composable function signature and all parameters (`vm`, `onEvent`, `language`, etc.)
   - All `Modifier.testResourceId(TestTags.*)` usages
   - All `onEvent(UIEvent.*)` emissions
   - Conditional rendering logic (`if`, `when`, `?.let`, `takeIf`)
   - List composables (`LazyColumn`, `LazyRow`, `items`, `itemsIndexed`)
   - Child composable invocations

2. **VM data class** — Search in the `view/` sibling directory or same package:
   - All fields, types, nullability
   - Sealed class variants and their properties
   - Nested/helper VM data classes (e.g., `HeaderVM`, `ButtonVM`)

3. **TestTags object** — Search in the same `compose/` directory:
   - All `const val` tag constants
   - Map each tag to the composable element it identifies

4. **UIEvents sealed class** — Search in the same `compose/` directory:
   - All event subclasses
   - Constructor parameters for each event (e.g., `data class OnItemTapped(val id: String)`)

5. **Child ComposeView files** — Any `*ComposeView.kt` in the same `compose/` directory:
   - Their parameters, test tags, and events
   - Helps determine what the parent delegates to children

#### 1.2 Analysis Output

After reading, produce a mental checklist:

- **Elements**: List of all UI elements with their test tags
- **Events**: List of all events with their trigger (which element, which gesture)
- **Conditions**: List of all conditional visibility branches (field name + true/false)
- **Nullables**: List of all nullable VM fields that affect UI
- **Sealed variants**: List of all sealed class variants rendered differently
- **Lists**: List type, item type, item click events
- **States**: Which combination of VM fields produces loading/empty/error/success

### Step 2: Determine File Paths

Derive the test file path dynamically from the source file path.

#### Path Derivation Rules

Given source file at:
```
{project_root}/{module}/src/commonMain/kotlin/{package_path}/compose/{ClassName}.kt
```

Generate test file at:
```
{project_root}/{module}/src/androidUnitTest/kotlin/{package_path}/{ClassName}Test.kt
```

**Rules:**
1. **Module is dynamic** — extract from source path (the directory before `/src/`). Examples: `booking`, `shared`, `payments`, `profile`, `onboarding`, `commons`
2. **Source set** — replace `commonMain` with `androidUnitTest`
3. **Drop `compose/` directory** — test file goes into the parent feature directory, not `compose/`
4. **File name** — append `Test` to the source class name: `TripsComposeView.kt` -> `TripsComposeViewTest.kt`
5. **Package** — mirrors the source package minus the `.compose` segment

**Example derivations:**

| Source | Test |
|--------|------|
| `booking/src/commonMain/kotlin/.../trips/compose/TripsComposeView.kt` | `booking/src/androidUnitTest/kotlin/.../trips/TripsComposeViewTest.kt` |
| `payments/src/commonMain/kotlin/.../main/PaymentMainComposeView.kt` | `payments/src/androidUnitTest/kotlin/.../main/PaymentMainComposeViewTest.kt` |
| `shared/src/commonMain/kotlin/.../home/compose/HomeComposeView.kt` | `shared/src/androidUnitTest/kotlin/.../home/HomeComposeViewTest.kt` |

**If the source file is NOT inside a `compose/` directory**, keep the same directory structure:
```
{module}/src/commonMain/kotlin/{package_path}/{ClassName}.kt
→ {module}/src/androidUnitTest/kotlin/{package_path}/{ClassName}Test.kt
```

Create all necessary parent directories before writing the test file.

### Step 3: Generate Test File

#### 3.1 Test Class Skeleton

```kotlin
package `in`.porter.customerapp.shared.{derived_package}

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onFirst
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.performClick
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
// Import VM, TestTags, UIEvents from source package

@RunWith(AndroidJUnit4::class)
class {ClassName}Test {

  @get:Rule
  val composeTestRule = createComposeRule()

  // --- VM Builders ---

  private fun buildVM(
    // Every VM field listed with a sensible default
  ): {FeatureVM} = {FeatureVM}(
    // Map all fields to defaults
  )

  // Builder for each nested/list item VM
  private fun buildItemVM(
    // Every field with a default
  ): {ItemVM} = {ItemVM}(...)

  // --- Content Helper ---

  private fun setContent(
    vm: {FeatureVM} = buildVM(),
    onEvent: ({UIEvents}) -> Unit = {},
  ) {
    composeTestRule.setContent {
      {ComposeViewFunction}(
        vm = vm,
        onEvent = onEvent,
      )
    }
  }

  // --- Tests ---
}
```

**Builder rules:**
- Every VM field MUST have a default value in the builder
- Use realistic defaults (not "foo", "bar", "test")
- Nullable fields default to `null`
- Boolean fields default to `false`
- List fields default to `emptyList()`
- String fields default to realistic placeholder text
- Create separate builder functions for nested VMs and list item VMs

#### 3.2 Test Categories

Generate tests in this order. **Skip a category ONLY if the ComposeView has zero elements matching it.**

---

**Category 1: Screen Root & Static Rendering**

For the screen root and always-visible elements:

```kotlin
@Test
fun test_screen_root_is_displayed() {
  setContent()
  composeTestRule
    .onNodeWithTag(TestTags.SCREEN_ROOT)
    .assertIsDisplayed()
}

@Test
fun test_{element}_displays_correct_text() {
  setContent(vm = buildVM(title = "Order History"))
  composeTestRule
    .onNodeWithTag(TestTags.TITLE)
    .assertTextEquals("Order History")
}
```

---

**Category 2: Conditional Visibility**

For every `if`/`when`/`?.let`/`takeIf` in the ComposeView that controls element visibility, generate a **pair** of tests:

```kotlin
@Test
fun test_{element}_visible_when_{condition}_true() {
  setContent(vm = buildVM(showBadge = true))
  composeTestRule
    .onNodeWithTag(TestTags.BADGE)
    .assertIsDisplayed()
}

@Test
fun test_{element}_hidden_when_{condition}_false() {
  setContent(vm = buildVM(showBadge = false))
  composeTestRule
    .onNodeWithTag(TestTags.BADGE)
    .assertDoesNotExist()
}
```

---

**Category 3: State Variations**

Generate one test per major UI state. Identify states from the VM fields (e.g., `isLoading`, `emptyVM`, `retryVM`, list emptiness):

```kotlin
@Test
fun test_loading_state_shows_loader_hides_content() {
  setContent(vm = buildVM(isLoading = true))
  composeTestRule.onNodeWithTag(TestTags.LOADER).assertIsDisplayed()
  composeTestRule.onNodeWithTag(TestTags.ORDER_LIST).assertDoesNotExist()
}

@Test
fun test_empty_state_shows_empty_view() {
  setContent(vm = buildVM(emptyVM = buildEmptyVM(), items = emptyList()))
  composeTestRule.onNodeWithTag(TestTags.EMPTY_VIEW).assertIsDisplayed()
}

@Test
fun test_error_state_shows_retry_view() {
  setContent(vm = buildVM(retryVM = buildRetryVM()))
  composeTestRule.onNodeWithTag(TestTags.RETRY_VIEW).assertIsDisplayed()
}

@Test
fun test_success_state_shows_content_hides_loader() {
  setContent(vm = buildVM(
    isLoading = false,
    items = listOf(buildItemVM()),
  ))
  composeTestRule.onNodeWithTag(TestTags.ORDER_LIST).assertIsDisplayed()
  composeTestRule.onNodeWithTag(TestTags.LOADER).assertDoesNotExist()
}
```

If the ComposeView has **state priority logic** (e.g., empty wins over loading), add priority tests:

```kotlin
@Test
fun test_empty_state_takes_priority_over_loading() {
  setContent(vm = buildVM(isLoading = true, emptyVM = buildEmptyVM()))
  composeTestRule.onNodeWithTag(TestTags.EMPTY_VIEW).assertIsDisplayed()
  composeTestRule.onNodeWithTag(TestTags.LOADER).assertDoesNotExist()
}
```

---

**Category 4: User Interactions (Event Verification)**

For every clickable element that emits a UI event:

```kotlin
@Test
fun test_{element}_click_emits_{event_name}() {
  var capturedEvent: {UIEvents}? = null
  setContent(
    vm = buildVM(/* state that makes element visible and clickable */),
    onEvent = { capturedEvent = it },
  )
  composeTestRule
    .onNodeWithTag(TestTags.ELEMENT)
    .performClick()
  assert(capturedEvent is {UIEvents}.{ExpectedEvent})
}
```

For events **with parameters**, also verify the parameter value:

```kotlin
@Test
fun test_order_card_click_emits_event_with_correct_crn() {
  var capturedEvent: {UIEvents}? = null
  setContent(
    vm = buildVM(items = listOf(buildItemVM(crn = "CRN123"))),
    onEvent = { capturedEvent = it },
  )
  composeTestRule
    .onAllNodesWithTag(TestTags.ORDER_CARD)
    .onFirst()
    .performClick()
  val event = capturedEvent as {UIEvents}.OnTripTapped
  assert(event.crn == "CRN123")
}
```

**CRITICAL:** Every subclass of the UIEvents sealed class MUST have at least one test verifying it is emitted.

---

**Category 5: List Rendering**

If the ComposeView contains `LazyColumn`, `LazyRow`, or `items {}`:

```kotlin
@Test
fun test_list_renders_correct_item_count() {
  val items = listOf(buildItemVM("1"), buildItemVM("2"), buildItemVM("3"))
  setContent(vm = buildVM(items = items))
  composeTestRule
    .onAllNodesWithTag(TestTags.LIST_ITEM)
    .assertCountEquals(3)
}

@Test
fun test_single_item_list_renders() {
  setContent(vm = buildVM(items = listOf(buildItemVM())))
  composeTestRule
    .onAllNodesWithTag(TestTags.LIST_ITEM)
    .assertCountEquals(1)
}

@Test
fun test_empty_list_does_not_render_items() {
  setContent(vm = buildVM(items = emptyList()))
  composeTestRule
    .onNodeWithTag(TestTags.LIST_ITEM)
    .assertDoesNotExist()
}

@Test
fun test_list_item_displays_correct_content() {
  setContent(vm = buildVM(items = listOf(buildItemVM(title = "Express Delivery"))))
  composeTestRule
    .onAllNodesWithTag(TestTags.ITEM_TITLE)
    .onFirst()
    .assertTextEquals("Express Delivery")
}

@Test
fun test_list_item_click_emits_event_with_correct_id() {
  var capturedEvent: {UIEvents}? = null
  setContent(
    vm = buildVM(items = listOf(buildItemVM(id = "item_1"))),
    onEvent = { capturedEvent = it },
  )
  composeTestRule
    .onAllNodesWithTag(TestTags.LIST_ITEM)
    .onFirst()
    .performClick()
  val event = capturedEvent as {UIEvents}.OnItemTapped
  assert(event.id == "item_1")
}
```

---

**Category 6: Nullable / Optional Fields**

For every nullable VM field that controls whether a UI element appears:

```kotlin
@Test
fun test_{element}_hidden_when_{field}_is_null() {
  setContent(vm = buildVM(optionalField = null))
  composeTestRule
    .onNodeWithTag(TestTags.OPTIONAL_ELEMENT)
    .assertDoesNotExist()
}

@Test
fun test_{element}_visible_when_{field}_is_not_null() {
  setContent(vm = buildVM(optionalField = "Some Value"))
  composeTestRule
    .onNodeWithTag(TestTags.OPTIONAL_ELEMENT)
    .assertIsDisplayed()
}

@Test
fun test_{element}_displays_non_null_field_text() {
  setContent(vm = buildVM(optionalField = "Discount Applied"))
  composeTestRule
    .onNodeWithTag(TestTags.OPTIONAL_ELEMENT)
    .assertTextEquals("Discount Applied")
}
```

---

**Category 7: Sealed Class Variants**

If the VM or list items use sealed classes with different visual representations:

```kotlin
@Test
fun test_{variant_a}_renders_variant_specific_elements() {
  val item = buildVariantA(title = "Header Section")
  setContent(vm = buildVM(items = listOf(item)))
  composeTestRule
    .onNodeWithTag(TestTags.HEADER_TITLE)
    .assertIsDisplayed()
    .assertTextEquals("Header Section")
}

@Test
fun test_{variant_b}_renders_variant_specific_elements() {
  val item = buildVariantB(label = "Order Item")
  setContent(vm = buildVM(items = listOf(item)))
  composeTestRule
    .onNodeWithTag(TestTags.ORDER_LABEL)
    .assertIsDisplayed()
}

@Test
fun test_mixed_variants_render_correctly() {
  val items = listOf(buildVariantA(), buildVariantB(), buildVariantB())
  setContent(vm = buildVM(items = items))
  composeTestRule
    .onAllNodesWithTag(TestTags.ORDER_LABEL)
    .assertCountEquals(2)
}
```

---

**Category 8: Edge Cases**

```kotlin
@Test
fun test_long_text_does_not_crash() {
  setContent(vm = buildVM(title = "A".repeat(500)))
  composeTestRule
    .onNodeWithTag(TestTags.TITLE)
    .assertIsDisplayed()
}

@Test
fun test_empty_string_field_renders_without_crash() {
  setContent(vm = buildVM(title = ""))
  composeTestRule
    .onNodeWithTag(TestTags.TITLE)
    .assertExists()
}

@Test
fun test_all_nullable_fields_null_does_not_crash() {
  setContent(vm = buildVM(
    // set every nullable field to null
  ))
  composeTestRule
    .onNodeWithTag(TestTags.SCREEN_ROOT)
    .assertIsDisplayed()
}
```

If lists exist, add a large list test:

```kotlin
@Test
fun test_large_list_renders_without_crash() {
  val items = List(50) { buildItemVM(id = "item_$it") }
  setContent(vm = buildVM(items = items))
  composeTestRule
    .onNodeWithTag(TestTags.ORDER_LIST)
    .assertIsDisplayed()
}
```

---

**Category 9: Child ComposeView Tests (Optional)**

If the ComposeView delegates rendering to child composables (e.g., `OrderHistoryCard`, `RetryStateView`), consider generating a **separate test file** per child using the same structure. Use the same path derivation rules from Step 2.

Only generate child tests if:
- The child has its own TestTags
- The child has complex conditional logic
- The child handles its own click events

### Step 4: Code Style Rules

1. **Test naming:** `test_{element}_{condition}_{expected_result}` in snake_case
2. **Package:** backtick-escaped `in`: `` `in`.porter.customerapp.shared.{path} ``
3. **Indent:** 2 spaces
4. **Trailing commas:** Allowed
5. **One assertion focus per test** — a test can have multiple assert calls but they should verify one logical behavior
6. **No `runTest {}`** — ComposeTestRule handles coroutines internally
7. **No mocks** — Compose UI tests are pure VM-driven, no mockk needed
8. **Node finding priority:**
   - `onNodeWithTag(TestTags.CONSTANT)` (always preferred)
   - `onAllNodesWithTag(TestTags.CONSTANT)` for repeated elements
   - `onNodeWithText("text")` ONLY as fallback when no TestTag exists
9. **Event capture pattern:**
   ```kotlin
   var capturedEvent: UIEvents? = null
   setContent(onEvent = { capturedEvent = it })
   ```
   Never use mockk for event verification in Compose tests.
10. **Builder defaults** — every VM field must have a default in the builder so each test only specifies fields it cares about
11. **Realistic data** — use realistic placeholder text, not "foo", "bar", "test123"
12. **Import `testResourceId`** if test tags use it:
    ```kotlin
    import `in`.porter.potionui.utils.testResourceId
    ```
13. **End of file:** 1 blank line at the end

### Step 5: Validation

#### 5.1 Coverage Checklist

Before marking as done, verify the generated test covers:

- [ ] Screen root is displayed
- [ ] Every `TestTags.*` constant used in the ComposeView has at least one test
- [ ] Every `UIEvents.*` subclass has at least one test verifying emission
- [ ] Every conditional visibility branch has both show AND hide tests
- [ ] Every nullable VM field has null AND non-null tests
- [ ] Every sealed class variant has at least one rendering test
- [ ] Loading, empty, error/retry, success states are all tested (if they exist)
- [ ] List item count, list item content, and list item click are tested (if list exists)
- [ ] At least one edge case test (long text, all nulls, empty strings)
- [ ] No test uses `onNodeWithText()` when a `TestTags` constant is available for that element
- [ ] All builder functions have defaults for every field

**If any checkbox fails**, go back and add the missing tests before proceeding.

#### 5.2 Compile Check

```bash
./gradlew :{module}:compileDebugUnitTestKotlinAndroid
```

Replace `{module}` with the actual module name extracted in Step 2.

If compilation fails, fix errors and recompile. Retry up to 3 times. Common fixes:
- Missing imports — add the correct import
- Wrong TestTag name — check the actual TestTags object
- Wrong VM constructor — re-read the VM data class
- Package mismatch — verify the derived package matches

#### 5.3 Run Tests

```bash
./gradlew :{module}:testDebugUnitTest --tests "*{ClassName}Test*"
```

If tests fail:
- `NodeNotFound` — the element may not be rendered for the given VM state, adjust the VM builder call
- `AssertionError on text` — check exact text formatting in VMMapper
- `Multiple nodes found` — use `onAllNodesWithTag().onFirst()` instead of `onNodeWithTag()`

#### 5.4 Grep for Common Mistakes

```bash
# No runTest usage (will hang on CI)
grep -n "runTest" {test_file_path}

# No hardcoded tag strings (should use TestTags object)
grep -n 'onNodeWithTag("' {test_file_path}

# No mockk usage (Compose UI tests should be pure)
grep -n "mockk" {test_file_path}

# No unused imports
grep -n "^import" {test_file_path} | wc -l
```

### Step 6: Gap Report

After generating tests, identify and report any gaps:

1. **TestTags without tests** — list any TestTags constants not covered
2. **UIEvents without tests** — list any event subclasses not verified
3. **Missing TestTags** — if the ComposeView has clickable/visible elements WITHOUT a test tag, report them as:
   > "Element `{composable}` at line {N} has no TestTag. Add `Modifier.testResourceId(TestTags.{SUGGESTED_NAME})` to enable testing."

4. **Untestable scroll effects** — if the ComposeView uses `LaunchedEffect` with `snapshotFlow` for scroll detection, note that these require special handling (test via the child list composable directly to avoid `AppNotIdleException`)

### Step 7: Done

Print a summary:

```
Generated: {test_file_path}
Module: {module}
Test count: {N} tests across {M} categories

Coverage:
  TestTags: {covered}/{total} covered
  UIEvents: {covered}/{total} covered
  States: loading, empty, error, success
  Nullable fields: {count} tested
  Sealed variants: {count} tested

Gaps (if any):
  - {description of gap}

Run: ./gradlew :{module}:testDebugUnitTest --tests "*{ClassName}Test*"
```

Then tell the user:

> Tests generated. Run the command above to verify. If any tests fail due to missing test tags on composables, I can add them.

## Critical Rules Summary

- **ALWAYS** derive test file path from the source file's module — never hardcode a module path
- **ALWAYS** use `TestTags` constants for node finding — never hardcode tag strings
- **ALWAYS** generate show + hide test pairs for conditional visibility
- **ALWAYS** verify every UIEvent subclass is tested
- **ALWAYS** use builder functions with defaults for VM construction
- **NEVER** use `runTest {}` — it hangs on CI/CD
- **NEVER** use `mockk` in Compose UI tests — they are pure VM-driven
- **NEVER** use `@Preview` parameters (`name`, `showBackground`) in Compose Multiplatform
- **NEVER** skip the coverage checklist before marking as done
- **NEVER** use `onNodeWithText()` when a TestTag is available

## Example Usage

### Single file
```
/generate-compose-ui-tests /path/to/booking/src/commonMain/kotlin/.../compose/TripsComposeView.kt
```

Generates:
```
booking/src/androidUnitTest/kotlin/.../trips/TripsComposeViewTest.kt
```

### Multiple files
```
/generate-compose-ui-tests /path/to/TripsComposeView.kt /path/to/PaymentMainComposeView.kt
```

Generates tests for both files in parallel using separate agents, then prints a combined summary.
