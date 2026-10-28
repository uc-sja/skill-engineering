# Generate XML-to-Compose Migration Verification Checklist

Create a comprehensive release checklist to verify that all UI from an existing XML view has been correctly implemented in the new Compose view.

## Workflow

### Step 1: Gather Inputs

**Always ask the user for these three inputs using `AskUserQuestion` before proceeding:**

1. **XML View Path** — Path to the existing XML-based view file (the source of truth for UI elements). Example: `customerapp/app/src/main/java/com/theporter/android/customerapp/loggedin/booking/home/HomeView.kt`
2. **Compose View Path** — Path to the new Compose view file (the migration target). Example: `customerapp-shared/booking/src/commonMain/kotlin/in/porter/customerapp/shared/loggedin/home/compose/HomeLandingComposeView.kt`
3. **Feature Name** — Name for the checklist file and headers. Example: `Home`, `Checkout`, `VehicleSelection`

Do NOT proceed to Step 2 until all three inputs are provided by the user.

### Step 2: Analyze the Existing XML View

Read the existing view file and its associated files thoroughly:

1. **View file** — Identify every UI element: TextViews, Buttons, ImageViews, RecyclerViews, EditTexts, CheckBoxes, Switches, ProgressBars, custom views, containers, dividers, etc.
2. **ViewModel / VM** — Read the ViewModel or VM data class to understand all fields that drive the UI. Note every field, including nullable ones (these often map to visibility toggles).
3. **State / Reducer** — Read the State data class and Reducer to understand all possible state combinations.
4. **Presenter** — Read the Presenter interface to catalog all user interaction event streams.
5. **Router** — Read the Router to understand navigation targets (attach/detach child flows).
6. **Analytics** — Read the Analytics class to list every tracked event, its trigger, and properties.

### Step 3: Analyze the New Compose View

Read the Compose view file and note:
- All Composable functions and their parameters
- Test tags applied via `testResourceId()`
- Potion UI components used
- Conditional visibility logic (`if`, `when`, `AnimatedVisibility`)
- Click handlers and event callbacks
- Scroll behavior, lazy lists

### Step 4: Cross-Reference and Generate Checklist

Compare the XML view elements against the Compose implementation. Generate a checklist markdown file at:

```
{module}/src/commonMain/kotlin/in/porter/customerapp/shared/testchecklist/{feature_name_snake_case}_release_checklist.md
```

Use the exact format below.

---

## Checklist Template

```markdown
# {FeatureName} — XML-to-Compose Migration Release Checklist

> **Scope:** Verify that every UI element, interaction, state, and edge case from the original XML view
> is correctly implemented in the new Compose view.
>
> **Every item below is mandatory** unless marked N/A with justification.

---

## How to Use

1. Go through each section and test every scenario.
2. Mark the **Result** column:
   - `[PASS]` — Works as expected
   - `[FAIL]` — Broken or missing (file a bug)
   - `[N/A]` — Not applicable (add reason)
3. A single unresolved `[FAIL]` blocks release.

---

## 1. View Element Parity

> Verify every UI element from the XML view exists in the Compose view.

| # | XML Element | Type | Compose Equivalent | Present | Result |
|---|-------------|------|--------------------|---------|--------|
<!-- One row per UI element found in the XML view. -->
<!-- Type = TextView, Button, ImageView, EditText, RecyclerView, CheckBox, Switch, Divider, Container, Custom, etc. -->
<!-- Compose Equivalent = Text, Button.Primary, Image, TextField, LazyColumn, Checkbox, Switch, HorizontalDivider, Column/Row, etc. -->
<!-- Present = Yes / No / Partial -->

---

## 2. Visibility & Conditional Rendering

> Verify all visibility toggles (VISIBLE/GONE/INVISIBLE) are correctly mapped to Compose conditional rendering.

| # | Scenario | XML Visibility Logic | Expected Compose Behavior | Result |
|---|----------|---------------------|--------------------------|--------|
<!-- One row per conditional visibility case from the VM/State. -->
<!-- Include: null checks, boolean flags, enum states, list empty/non-empty, loading states. -->

---

## 3. Functional Scenarios — Happy Path

> Core user flows that must work identically to the XML version.

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
<!-- Derive from Presenter event streams and Router navigation. -->
<!-- E.g., "User taps confirm button", "User scrolls list", "User selects item", "Screen loads with data". -->

---

## 4. User Interaction Parity

> Verify every user interaction from the Presenter interface is wired in Compose.

| # | Presenter Method | Interaction Type | Compose Handler | Result |
|---|-----------------|-----------------|-----------------|--------|
<!-- One row per method in the Presenter interface. -->
<!-- Interaction Type = Tap, LongPress, Scroll, TextInput, Toggle, Swipe, etc. -->
<!-- Compose Handler = onClick, onValueChange, onScrolled, etc. -->

---

## 5. Error States & Empty States

> Verify all error and empty state UI renders correctly.

| # | Scenario | Expected UI | Result |
|---|----------|-------------|--------|
<!-- Derive from State fields: errorMessage, isError, isEmpty, failureReason, etc. -->
<!-- Include: API failure, network error, empty list, invalid input, timeout. -->

---

## 6. Loading & Skeleton States

> Verify loading indicators and skeleton screens.

| # | Scenario | Expected UI | Result |
|---|----------|-------------|--------|
<!-- Derive from State fields: isLoading, isRefreshing, isLoadingMore, etc. -->

---

## 7. Text & Content Rendering

> Verify all text content, formatting, and dynamic values display correctly.

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
<!-- Include: currency formatting, pluralization, date/time, HTML text, truncation, max lines. -->

---

## 8. Navigation & Back Stack

> Verify navigation behavior matches the XML version.

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
<!-- Derive from Router methods: attach*, detach*, goBack, etc. -->

---

## 9. State Retention

> Verify state is preserved across configuration changes and navigation.

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | Rotate device / config change | State fully preserved | |
| 2 | Navigate to child and return | Parent state preserved | |
| 3 | Background and resume app | State fully restored | |

---

## 10. Analytics Events

> Verify every analytics event fires with correct properties.

| # | Event Name | Fires When | Properties to Verify | Result |
|---|-----------|-----------|---------------------|--------|
<!-- One row per event from the Analytics class. -->

---

## 11. Design System Compliance (Compose-Specific)

> Verify Potion UI tokens are used correctly — no hardcoded values.

| # | Check | Expected | Result |
|---|-------|----------|--------|
| 1 | No hardcoded `dp` values | All sizing via `PotionDimensions.layerStyles*` | |
| 2 | No hardcoded colors | All colors via `LocalColors.current.layerStyles*` | |
| 3 | No hardcoded font sizes | All typography via `PotionTextStyles.layerStyles*` | |
| 4 | No hardcoded padding | All padding via `PotionDimensions.layerStylesPadding*` | |
| 5 | No hardcoded spacing | All spacing via `PotionDimensions.layerStylesSpacing*` | |
| 6 | Test tags on all interactive elements | `testResourceId()` applied | |
| 7 | Test tags on all screen roots | Root composable tagged | |

---

## 12. Performance & Memory (Compose-Specific)

> Compose-specific performance verification.

| # | Scenario | Tool/Method | Threshold | Result |
|---|----------|-------------|-----------|--------|
| 1 | No unnecessary recompositions | Layout Inspector / recomposition counter | 0 unnecessary recomps on static state | |
| 2 | LazyColumn/LazyRow uses `key` | Code review | All lazy items have stable keys | |
| 3 | Heavy computations use `remember` | Code review | No computation in composable body without remember | |
| 4 | Image loading uses proper caching | Code review | AsyncImage or equivalent with caching | |
| 5 | No state hoisting violations | Code review | State owned at correct level | |
| 6 | Animations don't cause frame drops | Profiler | < 16ms frame time during animation | |
| 7 | Scroll performance is smooth | Manual test + Profiler | 60fps during fast scroll | |
| 8 | Memory footprint comparable to XML | Android Profiler | Within 10% of XML version | |

---

## 13. Accessibility & UI Edge Cases

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | Content descriptions on images/icons | Proper `contentDescription` set | |
| 2 | Long text wraps correctly | No text clipping or overlap | |
| 3 | RTL layout support | Mirrored layout in RTL locales | |
| 4 | Large font / display scaling | UI adapts without clipping | |
| 5 | Dark mode (if supported) | Colors from theme, no hardcoded | |
| 6 | Keyboard overlaps input fields | Scroll/resize handles keyboard | |
| 7 | Empty string vs null rendering | Correct behavior for both cases | |

---

## 14. Platform-Specific (iOS Compatibility)

> Verify Compose Multiplatform renders correctly on iOS.

| # | Scenario | Expected | Result |
|---|----------|----------|--------|
| 1 | Screen renders on iOS simulator | Visual parity with Android | |
| 2 | Touch interactions work on iOS | All taps/gestures functional | |
| 3 | Scroll behavior on iOS | Native-feeling momentum scroll | |
| 4 | Keyboard handling on iOS | Proper keyboard avoidance | |
| 5 | No Android-specific API usage | Code compiles for iOS target | |

---

## Pre-Release Sign-Off

| Field | Value |
|-------|-------|
| PR / Version | |
| Tested By | |
| Date | |

### Section Completion

- [ ] 1. View Element Parity
- [ ] 2. Visibility & Conditional Rendering
- [ ] 3. Functional Scenarios — Happy Path
- [ ] 4. User Interaction Parity
- [ ] 5. Error States & Empty States
- [ ] 6. Loading & Skeleton States
- [ ] 7. Text & Content Rendering
- [ ] 8. Navigation & Back Stack
- [ ] 9. State Retention
- [ ] 10. Analytics Events
- [ ] 11. Design System Compliance
- [ ] 12. Performance & Memory
- [ ] 13. Accessibility & UI Edge Cases
- [ ] 14. Platform-Specific (iOS Compatibility)

### Release Decision

- Total FAIL count: ___
- Risk-accepted FAILs (with justification): ___
- **APPROVED / BLOCKED**

---

## Known High-Risk Areas

<!-- List areas that historically cause issues during XML-to-Compose migration. -->
<!-- E.g., "RecyclerView to LazyColumn item animations", "Custom drawable to Compose Canvas". -->
```

---

### Step 5: Fill In the Checklist

Using the analysis from Steps 2 and 3, populate every table row:

1. **View Element Parity** — One row per UI element from the XML view. Mark "Present = No" for any element missing in Compose.
2. **Visibility & Conditional Rendering** — One row per nullable or boolean field in the VM/State that controls visibility.
3. **Functional Scenarios** — Derive from Presenter methods (each event stream = one scenario).
4. **User Interaction Parity** — One row per Presenter method.
5. **Error States** — Derive from State fields containing error/failure/empty concepts.
6. **Loading States** — Derive from State fields containing loading/refreshing concepts.
7. **Text & Content** — Identify dynamic text formatting (currency, dates, HTML, plurals).
8. **Navigation** — One row per Router method.
9. **Analytics Events** — One row per event in the Analytics class, with properties.
10. **Known High-Risk Areas** — Call out complex migrations (RecyclerView→LazyColumn, custom views→Canvas, animations, etc.).

### Step 6: Compile and Verify

Run compilation check on the module:
```bash
./gradlew :{module}:compileDebugKotlinAndroid
```

Ensure no compilation issues were introduced.

### Step 7: Report Summary

Print a summary:
```
Migration Checklist Created:
  File: {path_to_checklist}
  Sections: 14
  View Elements: {count}
  Interactions: {count}
  Analytics Events: {count}
  Error Scenarios: {count}

⚠ Elements NOT found in Compose view: {list or "None"}
```

## Critical Rules

1. **XML view is the source of truth** — Every element in the XML view must have a corresponding entry in the checklist.
2. **Mark missing items explicitly** — If a UI element exists in XML but not in Compose, set Present = "No" and Result is pre-filled as `[FAIL]`.
3. **Performance section is Compose-specific** — Use Compose-specific checks (recomposition, remember, keys) not XML-specific ones.
4. **Design System compliance is mandatory** — No hardcoded dp, colors, or fonts.
5. **Do not skip analytics** — Every event from the Analytics class must appear in Section 10.
6. **Platform section is required** — This is Compose Multiplatform; iOS compatibility must be verified.
