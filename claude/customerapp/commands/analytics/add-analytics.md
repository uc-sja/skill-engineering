# Add Analytics Event

You are adding analytics tracking to a feature in the Porter Customer App shared library.

## Task

Add analytics event tracking following the established patterns in this codebase.

## CRITICAL: Privacy & PII Protection

**NEVER include Personally Identifiable Information (PII) in event attributes.**

**Prohibited:**
- ❌ Email addresses
- ❌ Phone numbers
- ❌ Full names
- ❌ Street addresses

**Allowed:**
- ✅ User IDs (anonymized)
- ✅ Generic flags (is_first_login, login_method)
- ✅ Counts and metrics
- ✅ Screen names and navigation paths

## Steps to Add Analytics

### 1. Create Event Identifiers (if new feature)

If the feature doesn't have analytics yet, create event identifiers:

**Location:** `shared/src/commonMain/kotlin/in/porter/customerapp/shared/{module}/{feature}/analytics/{Feature}AnalyticsEventIdentifier.kt`

**Template:**
```kotlin
package `in`.porter.customerapp.shared.{module}.{feature}.analytics

import `in`.porter.customerapp.shared.analytics.centralanalytics.CustomerAppFlow
import `in`.porter.kmputils.analytics.events.EventIdentifiers
import `in`.porter.kmputils.analytics.events.ProductFlow

sealed class {Feature}AnalyticsEventIdentifier(
  override val isEnabled: Boolean = true,
  override val isDebug: Boolean = true,
  override val eventName: String,
  override val productFlow: ProductFlow = CustomerAppFlow.APP_LAUNCH,
) : EventIdentifiers {
  data object ScreenOpened : {Feature}AnalyticsEventIdentifier(eventName = "{feature}_screen_opened")
  data object ButtonClicked : {Feature}AnalyticsEventIdentifier(eventName = "{feature}_button_clicked")
  // Add more event identifiers as needed
}
```

### 2. Create or Update Analytics Class

**Location:** `shared/src/commonMain/kotlin/in/porter/customerapp/shared/{module}/{feature}/{Feature}Analytics.kt`

**Template:**
```kotlin
package `in`.porter.customerapp.shared.{module}.{feature}

import `in`.porter.customerapp.shared.analytics.Constants.EventAttrName.DESIGN_SYSTEM_POWERED
import `in`.porter.customerapp.shared.analytics.Constants.EventAttrName.SCREEN_NAME
import `in`.porter.customerapp.shared.analytics.FeatureAnalytics
import `in`.porter.kmputils.analytics.EventRecorder
import `in`.porter.kmputils.analytics.events.ActionEvent
import `in`.porter.kmputils.analytics.events.ImpressionEvent

class {Feature}Analytics(
  eventRecorder: EventRecorder,
) : FeatureAnalytics(eventRecorder) {

  private val commonAttr = mapOf(SCREEN_NAME to "{feature}_screen")

  fun trackScreenLoaded(isDesignSystemPowered: Boolean) {
    val attributes = buildMap {
      putAll(commonAttr)
      put(DESIGN_SYSTEM_POWERED, isDesignSystemPowered)
      // Add feature-specific attributes (NO PII!)
    }
    val event = ImpressionEvent.Launch(
      attributes = attributes,
      itemLaunched = "{Feature}",
      eventIdentifiers = {Feature}AnalyticsEventIdentifier.ScreenOpened,
    )
    recordEvent(event)
  }

  fun trackButtonClicked(buttonName: String) {
    val attributes = buildMap {
      putAll(commonAttr)
      put("button_name", buttonName)
    }
    val event = ActionEvent.Click(
      attributes = attributes,
      itemClicked = buttonName,
      eventIdentifiers = {Feature}AnalyticsEventIdentifier.ButtonClicked,
    )
    recordEvent(event)
  }
}
```

### 3. Wire Analytics in Builder

**Update:** `{Feature}Builder.kt`

```kotlin
fun build(...): {Feature}Interactor {
  return {Feature}Interactor(
    // ... other params
    analytics = {Feature}Analytics(
      eventRecorder = eventRecorder,
    ),
  )
}
```

### 4. Call Analytics from Interactor

**Update:** `{Feature}Interactor.kt`

```kotlin
class {Feature}Interactor(
  // ... other params
  private val analytics: {Feature}Analytics,
) : BaseStateVMInteractor<{Feature}Params, {Feature}State, {Feature}VM>(...) {

  override fun didBecomeActive() {
    super.didBecomeActive()
    analytics.trackScreenLoaded(isDesignSystemPowered = true)
    launch { ButtonClickHandler().invoke() }
  }

  inner class ButtonClickHandler {
    suspend fun invoke() {
      presenter.didTapButton()
        .collectSafeForeground {
          analytics.trackButtonClicked("submit_button")
          // Handle button click logic
        }
    }
  }
}
```

### 5. Add Tests for Analytics

**Update:** `{Feature}StepDefs.kt`

```kotlin
@Then("analytics should track screen loaded")
fun verifyScreenLoadedTracked() {
  verify { testHelper.analytics.trackScreenLoaded(isDesignSystemPowered = true) }
}

@And("analytics should track button clicked")
fun verifyButtonClickTracked() {
  verify { testHelper.analytics.trackButtonClicked("submit_button") }
}
```

**Update:** `{Feature}TestHelper.kt`

```kotlin
val analytics: {Feature}Analytics = mockk(relaxed = true)

fun build{Feature}Interactor(...): {Feature}Interactor {
  return {Feature}Interactor(
    // ... other params
    analytics = analytics,
  )
}
```

## Event Types Reference

| Type | Class | Use Case | Example |
|------|-------|----------|---------|
| Screen load | `ImpressionEvent.Launch` | Screen opened/loaded | `trackScreenLoaded()` |
| View shown | `ImpressionEvent.ViewShown` | Component becomes visible | `trackBannerShown()` |
| Click | `ActionEvent.Click` | Button/item tapped | `trackButtonClicked()` |
| Scroll | `ActionEvent.Scroll` | User scrolled | `trackScreenScrolled()` |
| State | `StateEvent.State` | Record current state/data | `trackPaymentModeSelected()` |

## Common Attribute Constants

Import from `in.porter.customerapp.shared.analytics.Constants.EventAttrName`:

- `SCREEN_NAME` - Name of the screen
- `DESIGN_SYSTEM_POWERED` - Whether using Potion UI
- `TYPE` - Type classification
- `CODE` - Error/response codes
- `FAILURE_REASON` - Why something failed
- `IS_SUCCESS` - Success boolean
- `IS_GRANTED` - Permission granted
- `LATITUDE` / `LONGITUDE` - Location data

## Checklist

Before completing, verify:
- [ ] No email addresses in attributes
- [ ] No phone numbers in attributes
- [ ] Event identifiers follow naming convention
- [ ] Analytics class extends `FeatureAnalytics`
- [ ] Analytics wired in Builder
- [ ] Analytics called from Interactor
- [ ] Tests added for analytics calls
- [ ] CommonAttr includes SCREEN_NAME

## Questions to Ask User

1. **Feature/Module name?** (e.g., "home", "payment", "profile")
2. **What event to track?** (screen load, button click, scroll, etc.)
3. **Event-specific attributes?** (any contextual data - ensure NO PII)
4. **ProductFlow to use?** (default: `CustomerAppFlow.APP_LAUNCH`)
