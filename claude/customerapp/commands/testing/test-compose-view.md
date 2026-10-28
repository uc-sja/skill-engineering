# Test Compose View with Mocks
// turbo-all

This workflow guides comprehensive testing of Compose View files using:
- **Preview Testing** in Android Studio (visual verification)
- **Runtime Testing** on real devices (interaction verification)
- **Mock Data** covering all VM variants and edge cases
- **Test Documentation** for systematic verification

## Overview

This command creates a complete testing infrastructure for a ComposeView:
1. **Preview Testing**: 10+ preview configurations for Android Studio
2. **Runtime Testing**: Interactive test UI for device testing
3. **VM Test Builder**: Centralized mock data for all scenarios
4. **Test Documentation**: Comprehensive testing guides and checklists

**Note**: All test code is temporary and must be removed before production.

---

## Step 1: Request Inputs

**CRITICAL**: Ask the user for these inputs immediately. Do not proceed without them.

### Required Inputs:
1. **ComposeView File**: Select from recent files or enter path
   - Example: `AddStopComposeView.kt`
   - Location: `shared/src/commonMain/kotlin/.../compose/`

2. **Test Scenarios**: Which scenarios to test?
   - Standard states (Empty, Loading, Error, Success, Edge cases)
   - VM variants (all sealed class cases, nullable properties)
   - Both standard + VM variants

3. **Remote Config Flags**: Does this feature use remote config?
   - Yes → List flag names
   - No → Skip config mocking

4. **Service Dependencies**: Does this feature call services?
   - Yes → List service interfaces
   - No → Skip service mocking

### Optional Context:
5. **ViewModel File**: Auto-detect or specify path
6. **UI Events File**: Auto-detect or specify path

---

## Step 2: Analyze Implementation

### 2.1 Read ComposeView File
Read the ComposeView file and extract:
- All VM properties used in the UI
- All UI event handlers (`onEvent = { ... }`)
- Conditional rendering logic (if/when statements)
- Required theme/language parameters
- Compose resource references

### 2.2 Analyze ViewModel Structure
Read the ViewModel file and analyze:
- **Sealed classes**: All variants (e.g., `OrderLocationVM` → `PickUpLocationVM`, `StopLocationVM`, `EmptyStopLocationVM`)
- **Nullable properties**: Which properties can be null?
- **Default values**: What are sensible defaults?
- **Data classes**: What nested data structures exist?
- **Collections**: List/Set/Map types and their contents

**Example Analysis:**
```kotlin
// AddStopVM.kt analysis:
sealed class AddStopVM(
    val orderLocationVMs: List<OrderLocationVM>,  // List of sealed class variants
    val addStopCtaLabel: String?,                  // Nullable
    val bottomCtaLabel: String?,                   // Nullable
    val rentalCardVM: RentalCardVM?,              // Nullable sealed class
)

// Need to test:
// - Empty list, 1 item, 2 items, max items
// - All OrderLocationVM variants
// - With/without addStopCtaLabel
// - With/without bottomCtaLabel
// - With/without rentalCardVM
```

### 2.3 Identify Dependencies
Search for and document:
- Remote config flag references
- Service/repository method calls
- Navigation dependencies
- Resource dependencies

---

## Step 3: Create Preview Configurations

### 3.1 Important: Compose Multiplatform Preview Limitations

**CRITICAL**: In Compose Multiplatform, `@Preview` annotation does NOT support:
- ❌ `name` parameter
- ❌ `showBackground` parameter
- ❌ `widthDp` parameter
- ❌ `heightDp` parameter

**Correct approach**:
```kotlin
// ✅ CORRECT (Compose Multiplatform)
// Preview: Empty State - No stops added
@Preview
@Composable
private fun AddStopComposeViewPreview_Empty() { ... }

// ❌ INCORRECT (Android only)
@Preview(name = "Empty State", showBackground = true)
@Composable
private fun AddStopComposeViewPreview_Empty() { ... }
```

Use **comments above @Preview** to describe the scenario.

### 3.2 Add Preview Functions to ComposeView

Add **7-13 preview functions** at the end of the ComposeView file:

```kotlin
// =============================================================================
// PREVIEW TESTING - Remove all but one before production
// =============================================================================

// Preview: Default - Empty state
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview() {
    val mockVm = {FeatureName}VM(
        items = emptyList(),
        isLoading = false,
        errorMessage = null
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }  // ⚠️ Change back to {} before production
        )
    }
}

// Preview: Loading State
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview_Loading() {
    val mockVm = {FeatureName}VM(
        items = emptyList(),
        isLoading = true,
        errorMessage = null
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }
        )
    }
}

// Preview: Error State
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview_Error() {
    val mockVm = {FeatureName}VM(
        items = emptyList(),
        isLoading = false,
        errorMessage = "Unable to load data. Please try again."
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }
        )
    }
}

// Preview: Success - With Data
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview_Success() {
    val mockVm = {FeatureName}VM(
        items = listOf(
            Item(id = "1", name = "Sample Item 1", address = "123 Main St"),
            Item(id = "2", name = "Sample Item 2", address = "456 Oak Ave"),
        ),
        isLoading = false,
        errorMessage = null,
        buttonLabel = "Continue"
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }
        )
    }
}

// Preview: Edge Case - Very Long Text
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview_LongText() {
    val mockVm = {FeatureName}VM(
        items = listOf(
            Item(
                id = "1",
                name = "Very Long Name That Should Wrap To Multiple Lines And Test Text Overflow Handling In The UI Layout",
                address = "Very Long Address With Many Details: Building 123, Floor 4, Apartment 567, Street Name That Is Also Very Long, City, State, Country, Postal Code"
            )
        ),
        isLoading = false,
        errorMessage = null
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }
        )
    }
}

// Preview: Maximum Items
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview_MaxItems() {
    val mockVm = {FeatureName}VM(
        items = List(10) { index ->
            Item(id = "$index", name = "Item $index", address = "Address $index")
        },
        isLoading = false,
        errorMessage = null
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }
        )
    }
}

// =============================================================================
// VM VARIANT PREVIEWS - Test sealed class variants and nullable properties
// =============================================================================

// Preview: Nullable Properties - All Null
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview_AllNull() {
    val mockVm = {FeatureName}VM(
        items = listOf(
            Item(id = "1", name = "Item", address = "Address", extraInfo = null)
        ),
        optionalTitle = null,
        optionalSubtitle = null,
        buttonLabel = null,
        isLoading = false,
        errorMessage = null
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }
        )
    }
}

// Add more VM variant previews as needed...
```

### 3.3 Required Imports
```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.ui.tooling.preview.Preview
import `in`.porter.potionui.theme.PotionTheme
import `in`.porter.potionui.theme.PotionLanguage
```

### 3.4 Build and Verify Previews
```bash
# Build the module
./gradlew :booking:compileDebugKotlin

# If build fails, check:
# - @Preview has no parameters
# - PotionTheme is imported correctly
# - All VM properties are provided
# - No unresolved references
```

---

## Step 4: Create VM Test Builder

Create a **centralized test data builder** for all scenarios. This makes it easy to reuse test data in both previews and runtime testing.

### 4.1 Create {FeatureName}VMTestBuilder.kt

**Location**: Same directory as ComposeView

**Template**:
```kotlin
package `in`.porter.customerapp.shared.{feature}.compose

/**
 * Test Data Builder for {FeatureName}VM
 *
 * ⚠️ WARNING: FOR TESTING ONLY - REMOVE BEFORE PRODUCTION
 *
 * Provides pre-configured VM scenarios for:
 * - Preview testing in Android Studio
 * - Runtime testing on real devices
 */
object {FeatureName}VMTestBuilder {

    /**
     * Test Scenarios
     */
    enum class TestScenario {
        // Basic States
        DEFAULT_EMPTY,
        LOADING,
        ERROR,
        SUCCESS_WITH_DATA,
        EDGE_CASE_LONG_TEXT,
        MAX_ITEMS,
        MIXED_STATE,

        // VM Variant Tests
        ALL_NULLABLE_NULL,
        VARIANT_A,
        VARIANT_B,
        CUSTOM_LABELS,
        DISABLED_STATE,
        // Add more scenarios as needed
    }

    /**
     * Get VM for a specific test scenario
     */
    fun getVMForScenario(scenario: TestScenario): {FeatureName}VM {
        return when (scenario) {
            TestScenario.DEFAULT_EMPTY -> createDefaultEmpty()
            TestScenario.LOADING -> createLoading()
            TestScenario.ERROR -> createError()
            TestScenario.SUCCESS_WITH_DATA -> createSuccess()
            TestScenario.EDGE_CASE_LONG_TEXT -> createLongText()
            TestScenario.MAX_ITEMS -> createMaxItems()
            TestScenario.MIXED_STATE -> createMixedState()
            TestScenario.ALL_NULLABLE_NULL -> createAllNullable()
            TestScenario.VARIANT_A -> createVariantA()
            TestScenario.VARIANT_B -> createVariantB()
            TestScenario.CUSTOM_LABELS -> createCustomLabels()
            TestScenario.DISABLED_STATE -> createDisabled()
        }
    }

    /**
     * Get human-readable name for scenario
     */
    fun getScenarioName(scenario: TestScenario): String {
        return when (scenario) {
            TestScenario.DEFAULT_EMPTY -> "1. Default - Empty State"
            TestScenario.LOADING -> "2. Loading State"
            TestScenario.ERROR -> "3. Error State"
            TestScenario.SUCCESS_WITH_DATA -> "4. Success - With Data"
            TestScenario.EDGE_CASE_LONG_TEXT -> "5. Edge Case - Very Long Text"
            TestScenario.MAX_ITEMS -> "6. Maximum Items"
            TestScenario.MIXED_STATE -> "7. Mixed State"
            TestScenario.ALL_NULLABLE_NULL -> "8. All Nullable Properties = Null"
            TestScenario.VARIANT_A -> "9. VM Variant A"
            TestScenario.VARIANT_B -> "10. VM Variant B"
            TestScenario.CUSTOM_LABELS -> "11. Custom Labels"
            TestScenario.DISABLED_STATE -> "12. Disabled State"
        }
    }

    /**
     * Get description for scenario
     */
    fun getScenarioDescription(scenario: TestScenario): String {
        return when (scenario) {
            TestScenario.DEFAULT_EMPTY -> "Empty state with no items"
            TestScenario.LOADING -> "Loading indicator visible"
            TestScenario.ERROR -> "Error message displayed"
            TestScenario.SUCCESS_WITH_DATA -> "Success state with sample data"
            TestScenario.EDGE_CASE_LONG_TEXT -> "Very long text to test wrapping"
            TestScenario.MAX_ITEMS -> "Maximum number of items"
            TestScenario.MIXED_STATE -> "Mix of different item states"
            TestScenario.ALL_NULLABLE_NULL -> "Tests nullable properties = null"
            TestScenario.VARIANT_A -> "Tests VM variant A"
            TestScenario.VARIANT_B -> "Tests VM variant B"
            TestScenario.CUSTOM_LABELS -> "Tests custom label text"
            TestScenario.DISABLED_STATE -> "Tests disabled/locked state"
        }
    }

    // =============================================================================
    // VM Creation Functions
    // =============================================================================

    private fun createDefaultEmpty() = {FeatureName}VM(
        items = emptyList(),
        isLoading = false,
        errorMessage = null,
        title = "Title",
        buttonLabel = "Continue"
    )

    private fun createLoading() = {FeatureName}VM(
        items = emptyList(),
        isLoading = true,
        errorMessage = null,
        title = "Title",
        buttonLabel = "Continue"
    )

    private fun createError() = {FeatureName}VM(
        items = emptyList(),
        isLoading = false,
        errorMessage = "Unable to load data. Please check your connection and try again.",
        title = "Title",
        buttonLabel = "Retry"
    )

    private fun createSuccess() = {FeatureName}VM(
        items = listOf(
            createMockItem(id = "1", name = "First Item", address = "123 Main Street"),
            createMockItem(id = "2", name = "Second Item", address = "456 Oak Avenue"),
            createMockItem(id = "3", name = "Third Item", address = "789 Pine Road"),
        ),
        isLoading = false,
        errorMessage = null,
        title = "Your Items",
        buttonLabel = "Continue"
    )

    private fun createLongText() = {FeatureName}VM(
        items = listOf(
            createMockItem(
                id = "1",
                name = "Very Long Name That Should Wrap To Multiple Lines And Test Text Overflow Handling Behavior In The User Interface Layout System",
                address = "Very Long Address With Many Details: Building 123, Floor 4, Apartment 567, Street Name That Is Also Very Long And Should Wrap, City Name, State, Country, Postal Code 123456"
            )
        ),
        isLoading = false,
        errorMessage = null,
        title = "Very Long Title That Should Also Test The Text Wrapping Behavior",
        buttonLabel = "Continue With Very Long Button Label Text"
    )

    private fun createMaxItems() = {FeatureName}VM(
        items = List(10) { index ->
            createMockItem(
                id = "item_$index",
                name = "Item ${index + 1}",
                address = "Address ${index + 1}"
            )
        },
        isLoading = false,
        errorMessage = null,
        title = "Maximum Items",
        buttonLabel = "Continue"
    )

    private fun createMixedState() = {FeatureName}VM(
        items = listOf(
            createMockItem(id = "1", name = "Completed Item", isComplete = true),
            createMockItem(id = "2", name = "Pending Item", isComplete = false),
            createMockItem(id = "3", name = "Error Item", hasError = true),
        ),
        isLoading = false,
        errorMessage = null,
        title = "Mixed States",
        buttonLabel = "Continue"
    )

    private fun createAllNullable() = {FeatureName}VM(
        items = listOf(
            createMockItem(id = "1", name = "Item", address = "Address", extraInfo = null)
        ),
        isLoading = false,
        errorMessage = null,
        title = null,  // Nullable
        subtitle = null,  // Nullable
        buttonLabel = null,  // Nullable
        optionalData = null  // Nullable
    )

    // Add more VM creation functions for each scenario...

    // =============================================================================
    // Mock Data Helpers
    // =============================================================================

    private fun createMockItem(
        id: String,
        name: String,
        address: String = "Default Address",
        isComplete: Boolean = false,
        hasError: Boolean = false,
        extraInfo: String? = "Extra info"
    ) = Item(
        id = id,
        name = name,
        address = address,
        isComplete = isComplete,
        hasError = hasError,
        extraInfo = extraInfo
    )
}
```

### 4.2 Update Preview Functions to Use Test Builder

Simplify preview functions by using the test builder:

```kotlin
// Preview: Default - Empty State
@Preview
@Composable
private fun {FeatureName}ComposeViewPreview() {
    val mockVm = {FeatureName}VMTestBuilder.getVMForScenario(
        {FeatureName}VMTestBuilder.TestScenario.DEFAULT_EMPTY
    )

    PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
        {FeatureName}ComposeView(
            vm = mockVm,
            language = PotionLanguage.ENGLISH,
            onEvent = { println("Event: $it") }
        )
    }
}

// Repeat for other scenarios...
```

---

## Step 5: Create Runtime Test Screen

Create an **interactive test UI** for runtime testing on real devices.

### 5.1 Create {FeatureName}TestScreen.kt

**Location**: Same directory as ComposeView

**Template**:
```kotlin
package `in`.porter.customerapp.shared.{feature}.compose

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import `in`.porter.potionui.components.IconButton
import `in`.porter.potionui.theme.LocalColors
import `in`.porter.potionui.theme.PotionDimensions
import `in`.porter.potionui.theme.PotionLanguage
import `in`.porter.potionui.theme.PotionTextStyles
import org.jetbrains.compose.resources.painterResource
import `in`.porter.customerapp.shared.booking.generated.resources.Res
import `in`.porter.customerapp.shared.booking.generated.resources.ic_cross_circle

/**
 * Test Screen for {FeatureName} VM Scenarios
 *
 * ⚠️ WARNING: FOR TESTING ONLY - REMOVE BEFORE PRODUCTION
 *
 * This screen allows you to test all VM scenarios on a real device.
 * Select a scenario from the list to see it rendered with {FeatureName}ComposeView.
 */
@Composable
fun {FeatureName}TestScreen(
    onBack: () -> Unit = {},
) {
    var selectedScenario by remember {
        mutableStateOf<{FeatureName}VMTestBuilder.TestScenario?>(null)
    }

    if (selectedScenario == null) {
        ScenarioListScreen(
            onScenarioSelected = { selectedScenario = it },
            onBack = onBack,
        )
    } else {
        ScenarioDetailScreen(
            scenario = selectedScenario!!,
            onBack = { selectedScenario = null },
        )
    }
}

@Composable
private fun ScenarioListScreen(
    onScenarioSelected: ({FeatureName}VMTestBuilder.TestScenario) -> Unit,
    onBack: () -> Unit,
) {
    val scenarios = {FeatureName}VMTestBuilder.TestScenario.entries

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(LocalColors.current.layerStylesColorBgBaseDefault),
    ) {
        // Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(LocalColors.current.layerStylesColorBgSurfaceDefaultPrimary)
                .padding(
                    horizontal = PotionDimensions.layerStylesPaddingLayout300,
                    vertical = PotionDimensions.layerStylesPaddingLayout200
                ),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton.Tertiary.Small(
                iconPainter = painterResource(Res.drawable.ic_cross_circle),
                iconDescription = "Back",
                onClick = onBack,
            )
            Text(
                text = "{FeatureName} Test Scenarios (${scenarios.size})",
                style = PotionTextStyles.layerStylesHeading16Bold,
                color = LocalColors.current.layerStylesColorTypePrimary,
                modifier = Modifier.padding(start = 12.dp),
            )
        }

        // Scenario List
        LazyColumn(
            modifier = Modifier.fillMaxSize(),
        ) {
            items(scenarios) { scenario ->
                ScenarioListItem(
                    scenario = scenario,
                    onClick = { onScenarioSelected(scenario) },
                )
            }
        }
    }
}

@Composable
private fun ScenarioListItem(
    scenario: {FeatureName}VMTestBuilder.TestScenario,
    onClick: () -> Unit,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .background(LocalColors.current.layerStylesColorBgSurfaceDefaultPrimary)
            .padding(
                horizontal = PotionDimensions.layerStylesPaddingLayout400,
                vertical = PotionDimensions.layerStylesPaddingLayout300,
            ),
    ) {
        // Scenario Name
        Text(
            text = {FeatureName}VMTestBuilder.getScenarioName(scenario),
            style = PotionTextStyles.layerStylesBody14Bold,
            color = LocalColors.current.layerStylesColorTypePrimary,
        )

        // Scenario Description
        Text(
            text = {FeatureName}VMTestBuilder.getScenarioDescription(scenario),
            style = PotionTextStyles.layerStylesCaption12Normal,
            color = LocalColors.current.layerStylesColorTypeSecondary,
            modifier = Modifier.padding(top = 4.dp),
        )

        // Divider
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .padding(top = PotionDimensions.layerStylesSpacingLayout200)
                .background(LocalColors.current.layerStylesColorTypeSecondary.copy(alpha = 0.2f))
                .padding(vertical = 0.5.dp),
        )
    }
}

@Composable
private fun ScenarioDetailScreen(
    scenario: {FeatureName}VMTestBuilder.TestScenario,
    onBack: () -> Unit,
) {
    val vm = {FeatureName}VMTestBuilder.getVMForScenario(scenario)

    Column(
        modifier = Modifier.fillMaxSize(),
    ) {
        // Header with back button
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .background(LocalColors.current.layerStylesColorBgSurfaceDefaultPrimary)
                .padding(
                    horizontal = PotionDimensions.layerStylesPaddingLayout300,
                    vertical = PotionDimensions.layerStylesPaddingLayout200
                ),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton.Tertiary.Small(
                iconPainter = painterResource(Res.drawable.ic_cross_circle),
                iconDescription = "Back",
                onClick = onBack,
            )
            Column(
                modifier = Modifier.padding(start = 12.dp),
            ) {
                Text(
                    text = {FeatureName}VMTestBuilder.getScenarioName(scenario),
                    style = PotionTextStyles.layerStylesHeading16Bold,
                    color = LocalColors.current.layerStylesColorTypePrimary,
                )
                Text(
                    text = {FeatureName}VMTestBuilder.getScenarioDescription(scenario),
                    style = PotionTextStyles.layerStylesCaption12Normal,
                    color = LocalColors.current.layerStylesColorTypeSecondary,
                    modifier = Modifier.padding(top = 2.dp),
                )
            }
        }

        // {FeatureName}ComposeView with test VM
        {FeatureName}ComposeView(
            vm = vm,
            language = PotionLanguage.ENGLISH,
            onEvent = { event ->
                // Log events for debugging
                println("🧪 TEST EVENT: $event")
                // In a real test, you might want to show a toast or log to screen
            },
        )
    }
}
```

### 5.2 Create Standalone Test Activity (Recommended)

**Location**: `customerApp/app/src/main/java/com/theporter/android/customerapp/`

**File**: `{FeatureName}TestActivity.kt`

```kotlin
package com.theporter.android.customerapp

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import `in`.porter.customerapp.shared.{feature}.compose.{FeatureName}TestScreen
import `in`.porter.potionui.theme.PotionLanguage
import `in`.porter.potionui.theme.PotionTheme

/**
 * Test Activity for {FeatureName} VM Scenarios
 *
 * ⚠️ WARNING: FOR TESTING ONLY - REMOVE BEFORE PRODUCTION
 *
 * This activity provides an easy way to test all {FeatureName} VM scenarios
 * on a real device without modifying the complex RIB architecture.
 *
 * To launch:
 * adb shell am start -n com.theporter.android.customerapp/.{FeatureName}TestActivity
 */
class {FeatureName}TestActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        setContent {
            PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
                {FeatureName}TestScreen(
                    onBack = { finish() }
                )
            }
        }
    }
}
```

### 5.3 Add Activity to AndroidManifest.xml

**Location**: `customerApp/app/src/main/AndroidManifest.xml`

Add after the main activity:

```xml
<!-- ⚠️ TESTING ONLY - REMOVE BEFORE PRODUCTION -->
<activity
  android:name="com.theporter.android.customerapp.{FeatureName}TestActivity"
  android:theme="@style/AppTheme"
  android:exported="true"
  android:screenOrientation="portrait">
</activity>
```

### 5.4 Add Required Dependency

**Location**: `customerApp/app/build.gradle.kts`

Add in dependencies section:

```kotlin
// ⚠️ TESTING ONLY - Compose Activity for {FeatureName}TestActivity
implementation("androidx.activity:activity-compose:1.9.0")
```

### 5.5 Build and Install

```bash
# Build the app
cd /path/to/customerApp
./gradlew :app:assembleDebug

# Install on device
adb install -r app/build/outputs/apk/staging/debug/customerApp-V{version}-staging-debug.apk

# Launch test activity
adb shell am start -n com.theporter.android.customerapp/.{FeatureName}TestActivity
```

### 5.6 Monitor Events

In a separate terminal:

```bash
adb logcat | grep "TEST EVENT"
```

You'll see events like:
```
🧪 TEST EVENT: OnItemClick(id=item_1)
🧪 TEST EVENT: OnButtonClick
🧪 TEST EVENT: OnBackClick
```

---

## Step 6: Common Build Issues and Fixes

### Issue 1: @Preview Parameters Not Supported

**Error**: `No parameter with name 'name' found`

**Cause**: Compose Multiplatform doesn't support `name`, `showBackground` parameters

**Fix**:
```kotlin
// ❌ Wrong
@Preview(name = "Empty State", showBackground = true)

// ✅ Correct
// Preview: Empty State
@Preview
```

### Issue 2: Color Reference Not Found

**Error**: `Unresolved reference 'layerStylesColorBorderDefault'`

**Cause**: Color might not exist in your theme

**Fix**: Check `LocalColors.current` available properties
```kotlin
// ❌ Might not exist
LocalColors.current.layerStylesColorBorderDefault

// ✅ Use available colors
LocalColors.current.layerStylesColorTypeSecondary.copy(alpha = 0.2f)
```

### Issue 3: setContent Not Found

**Error**: `Unresolved reference 'setContent'`

**Cause**: Missing activity-compose dependency

**Fix**: Add to app/build.gradle.kts:
```kotlin
implementation("androidx.activity:activity-compose:1.9.0")
```

### Issue 4: AWS Token Expiration

**Error**: `ExpiredToken when calling ListObjectsV2 operation`

**Cause**: Infrastructure issue, not code issue

**Fix**: Wait for token refresh or contact DevOps

---

## Step 7: Create Test Documentation

### 7.1 Test Scenarios Document

Create `{FeatureName}TestScenarios.md` in the same directory:

```markdown
# {FeatureName} Test Scenarios

## Preview Testing (Android Studio)

### Visual Verification

For each preview, verify:
- [ ] Layout renders correctly
- [ ] Spacing and padding match design
- [ ] Colors are correct
- [ ] Typography is correct
- [ ] Icons are present and correct
- [ ] Text wraps properly
- [ ] No overflow or clipping

### Scenario 1: Default Empty State
- [ ] Empty state message displays
- [ ] Layout is centered/aligned correctly
- **Preview**: `{FeatureName}ComposeViewPreview`

### Scenario 2: Loading State
- [ ] Loading indicator shows
- [ ] Content is hidden
- **Preview**: `{FeatureName}ComposeViewPreview_Loading`

### Scenario 3: Error State
- [ ] Error message displays
- [ ] Error color is red/error theme
- [ ] Retry button shows (if applicable)
- **Preview**: `{FeatureName}ComposeViewPreview_Error`

### Scenario 4: Success with Data
- [ ] All items render correctly
- [ ] Data displays properly
- [ ] Buttons are enabled
- **Preview**: `{FeatureName}ComposeViewPreview_Success`

### Scenario 5: Edge Case - Long Text
- [ ] Text wraps correctly
- [ ] No overflow
- [ ] Layout doesn't break
- **Preview**: `{FeatureName}ComposeViewPreview_LongText`

### Scenario 6: Maximum Items
- [ ] List scrolls properly
- [ ] All items visible
- [ ] Performance is acceptable
- **Preview**: `{FeatureName}ComposeViewPreview_MaxItems`

## Runtime Testing (Real Device)

### Interaction Verification

### Scenario 1: Button Clicks
- [ ] Buttons respond to taps
- [ ] Correct events are triggered
- [ ] Events logged in logcat
- **Monitor**: `adb logcat | grep "TEST EVENT"`

### Scenario 2: Item Interactions
- [ ] Item taps work
- [ ] Correct item ID in event
- [ ] Visual feedback on tap
- **Monitor**: `adb logcat | grep "TEST EVENT"`

### Scenario 3: Navigation
- [ ] Back button works
- [ ] Navigation events trigger
- [ ] Screen transitions smoothly
- **Monitor**: `adb logcat | grep "TEST EVENT"`

### Scenario 4: Scrolling
- [ ] List scrolls smoothly
- [ ] Scroll position maintained
- [ ] No performance issues
- **Test**: Use device gestures

### Scenario 5: Different Scenarios
- [ ] All scenarios load correctly
- [ ] Switching between scenarios works
- [ ] No crashes or errors
- **Test**: Tap through all 12 scenarios

## Test Data

All test data is in `{FeatureName}VMTestBuilder.kt`

## Cleanup Checklist

Before production:
- [ ] Remove {FeatureName}TestActivity.kt
- [ ] Remove {FeatureName}TestScreen.kt
- [ ] Remove {FeatureName}VMTestBuilder.kt
- [ ] Remove activity from AndroidManifest.xml
- [ ] Remove activity-compose dependency
- [ ] Remove extra preview functions (keep 1)
- [ ] Change `println("Event: $it")` to `{}`
- [ ] Remove all test documentation files
- [ ] Verify build succeeds
- [ ] Test with real data
```

---

## Step 8: Execute Testing

### 8.1 Preview Testing in Android Studio

1. **Open ComposeView file** in Android Studio
2. **Open Preview panel** (View → Tool Windows → Compose Preview)
3. **Click "Build & Refresh"**
4. **Test each preview**:
   - Select from dropdown (13 previews)
   - Verify visual appearance
   - Screenshot for documentation
   - Mark scenarios as ✅ or ❌ in test document

### 8.2 Runtime Testing on Device

1. **Launch test activity**:
   ```bash
   adb shell am start -n com.theporter.android.customerapp/.{FeatureName}TestActivity
   ```

2. **Start event monitoring** (separate terminal):
   ```bash
   adb logcat | grep "TEST EVENT"
   ```

3. **Test each scenario**:
   - Tap scenario from list
   - View UI appearance
   - Test all interactions
   - Verify events in logcat
   - Go back and try next scenario

4. **Document results** in test scenarios file

---

## Step 9: Cleanup (CRITICAL)

**⚠️ ALL TEST CODE MUST BE REMOVED BEFORE PRODUCTION**

### 9.1 Cleanup Checklist

```markdown
## Cleanup Checklist for {FeatureName}

### Files to DELETE:
- [ ] {FeatureName}TestActivity.kt
- [ ] {FeatureName}TestScreen.kt
- [ ] {FeatureName}VMTestBuilder.kt
- [ ] {FeatureName}TestScenarios.md
- [ ] Any other test documentation

### Code to REMOVE:

#### AndroidManifest.xml
- [ ] Remove {FeatureName}TestActivity declaration

#### app/build.gradle.kts
- [ ] Remove: `implementation("androidx.activity:activity-compose:1.9.0")`

#### {FeatureName}ComposeView.kt
- [ ] Remove preview functions 2-13 (keep only 1)
- [ ] Change `onEvent = { println("Event: $it") }` to `onEvent = {}`
- [ ] Remove test-related comments

### Verification:
```bash
# Build succeeds
./gradlew :booking:compileDebugKotlin
./gradlew :app:compileDebugKotlin

# No mock/test references
grep -r "{FeatureName}VMTestBuilder" .
grep -r "{FeatureName}TestScreen" .
grep -r "{FeatureName}TestActivity" .
grep -r "TEST EVENT" .

# Git status clean
git status
```

### Final Check:
- [ ] Build successful
- [ ] No test files found
- [ ] Feature works with real data
- [ ] Ready for PR
```

### 9.2 Execute Cleanup

```bash
# Navigate to project root
cd /path/to/customerapp-shared

# Delete test files
rm booking/src/commonMain/kotlin/.../compose/{FeatureName}VMTestBuilder.kt
rm booking/src/commonMain/kotlin/.../compose/{FeatureName}TestScreen.kt
rm booking/src/commonMain/kotlin/.../compose/{FeatureName}TestScenarios.md

# Navigate to app module
cd ../customerApp

# Delete test activity
rm app/src/main/java/com/theporter/android/customerapp/{FeatureName}TestActivity.kt

# Edit files (use Edit tool):
# - Remove activity from AndroidManifest.xml
# - Remove dependency from app/build.gradle.kts
# - Clean up {FeatureName}ComposeView.kt

# Verify
./gradlew :app:compileDebugKotlin
```

---

## Step 10: Generate Testing Summary

Create `/tmp/{feature_name}_testing_summary.txt`:

```markdown
═══════════════════════════════════════════════════════════════════════════════
✅ COMPLETE: {FeatureName} Compose View Testing
═══════════════════════════════════════════════════════════════════════════════

📊 TESTING SUMMARY
═══════════════════

Preview Testing: ✅ Complete
Runtime Testing: ✅ Complete
VM Variant Coverage: 100%
Build Status: ✅ Successful
Cleanup Status: ✅ Complete

═══════════════════════════════════════════════════════════════════════════════
📋 TEST RESULTS
═══════════════════════════════════════════════════════════════════════════════

## Preview Testing (Android Studio)
✅ Default Empty State - Layout correct
✅ Loading State - Indicator shows
✅ Error State - Error message displays
✅ Success with Data - Data renders correctly
✅ Long Text - Text wraps properly
✅ Maximum Items - Scrolling works

## VM Variant Testing
✅ All Nullable Properties = Null - UI handles correctly
✅ Variant A - Displays correctly
✅ Variant B - Displays correctly
✅ Custom Labels - Labels show correctly
✅ Disabled State - UI shows disabled state

## Runtime Testing (Real Device)
✅ Button Clicks - Events triggered
✅ Item Interactions - Correct event data
✅ Navigation - Back button works
✅ Scenario Switching - All scenarios work
✅ Event Logging - All events logged

═══════════════════════════════════════════════════════════════════════════════
🗂️ FILES CREATED/MODIFIED
═══════════════════════════════════════════════════════════════════════════════

**CREATED (All removed after testing):**
- {FeatureName}VMTestBuilder.kt (~800 lines)
- {FeatureName}TestScreen.kt (~200 lines)
- {FeatureName}TestActivity.kt (~30 lines)
- {FeatureName}TestScenarios.md (~400 lines)

**MODIFIED (Reverted after testing):**
- {FeatureName}ComposeView.kt - Added/removed test previews
- AndroidManifest.xml - Added/removed test activity
- app/build.gradle.kts - Added/removed dependency

**FINAL STATE (Production-ready):**
✅ {FeatureName}ComposeView.kt - Clean, 1 preview only
✅ All test files removed
✅ Build successful
✅ Feature tested and verified

═══════════════════════════════════════════════════════════════════════════════
🎯 SUCCESS CRITERIA MET
═══════════════════════════════════════════════════════════════════════════════

✅ All visual states tested
✅ All interactions tested
✅ All VM variants tested
✅ Edge cases tested
✅ Events verified
✅ Cleanup completed
✅ Build successful
✅ Ready for production

═══════════════════════════════════════════════════════════════════════════════
```

---

## Best Practices

### ✅ DO:
- Create 10+ preview functions for comprehensive visual testing
- Use realistic mock data (not "foo", "bar", "test")
- Test all sealed class variants
- Test all nullable properties (null and non-null)
- Create standalone TestActivity for device testing
- Monitor events with `adb logcat | grep "TEST EVENT"`
- Document all scenarios with checklists
- Screenshot all preview states
- Remove ALL test code before production
- Verify build after cleanup

### ❌ DON'T:
- Don't use `@Preview(name = "...", showBackground = true)` in KMP
- Don't use unrealistic test data
- Don't skip VM variant testing
- Don't skip runtime device testing
- Don't commit test files to production
- Don't leave `println("Event: $it")` in production
- Don't skip cleanup verification
- Don't assume cleanup worked - verify with grep

---

## Real-World Example: Complete Testing Workflow

This workflow was successfully validated with a complex ComposeView containing:
- Sealed class ViewModels with 3+ variants
- Nullable properties across 10+ fields
- List-based UI with dynamic item counts
- Multiple conditional rendering paths

### Typical Results:
- **Files Created**: 4 test files (~1500 lines total)
- **Preview Functions**: 10-13 scenarios
- **VM Coverage**: 100% of all variants and nullable properties
- **Build Time**: 8-10 minutes
- **Testing Time**: 30-45 minutes (thorough testing of all scenarios)
- **Cleanup Time**: 5-10 minutes

### Key Learnings from Production Usage:

1. **Compose Multiplatform Preview Limitations**
   - `@Preview` annotation accepts NO parameters in KMP
   - Use comments above `@Preview` for scenario descriptions
   - This is the #1 blocker if not understood upfront

2. **Standalone TestActivity Pattern**
   - Much simpler than integrating with RIB architecture
   - Can be launched directly via ADB
   - Easy to add/remove for testing cycles
   - No complex dependency injection needed

3. **VM Test Builder Pattern**
   - Centralized test data is highly maintainable
   - Easy to update all scenarios when VM changes
   - Reusable across preview and runtime testing
   - Enum-based scenario selection is intuitive

4. **Interactive Test Screen Value**
   - Systematic testing of all scenarios
   - Easy scenario switching without rebuilding
   - Visual comparison between scenarios
   - Event logging for behavior verification

5. **Event Logging is Essential**
   - `println("🧪 TEST EVENT: $event")` in onEvent handler
   - Monitor with `adb logcat | grep "TEST EVENT"`
   - Verifies all interactions trigger correct events
   - Catches event data issues early

6. **Cleanup Verification is Critical**
   - Always use `grep` to verify test code removal
   - Build verification catches compilation issues
   - Test with real data before submitting PR
   - Git status check prevents accidental commits

### Common Pitfalls Encountered:

1. **Forgetting to remove test event logging**
   - `println("Event: $it")` left in production → Fixed
   - Always change back to `{}` before cleanup

2. **Missing activity-compose dependency**
   - TestActivity won't compile → Add dependency
   - Remember to remove dependency during cleanup

3. **Using unavailable theme colors**
   - Some colors don't exist in LocalColors → Check available properties
   - Use `.copy(alpha = 0.2f)` for semi-transparent colors

4. **Not testing all VM variants**
   - Initially created only 5 previews → Missed edge cases
   - Expanded to 13 previews → Caught UI bugs

5. **Assuming cleanup worked**
   - Didn't verify with grep → Test files committed
   - Now always verify with multiple grep searches

### Success Metrics:

When properly executed, this workflow achieves:
- ✅ 100% VM variant coverage
- ✅ All edge cases identified and tested
- ✅ All interactions verified with event logging
- ✅ Zero test code in production
- ✅ Clean build after cleanup
- ✅ Feature works with real data
- ✅ Ready for code review within 1-2 hours

---

## Critical Rules Summary

- ✅ ALWAYS create multiple preview functions (10+)
- ✅ ALWAYS test all VM variants and nullable properties
- ✅ ALWAYS create runtime test infrastructure
- ✅ ALWAYS monitor events with adb logcat
- ✅ ALWAYS remove all test code before production
- ✅ ALWAYS verify cleanup with grep and build
- ❌ NO `@Preview(name = ...)` in Compose Multiplatform
- ❌ NO test files in production commits
- ❌ NO skipping cleanup verification
- ❌ NO unrealistic test data

Now test the ComposeView following all steps above.