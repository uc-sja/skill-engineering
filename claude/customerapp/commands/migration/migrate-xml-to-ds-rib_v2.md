# Implement RIB Feature with Compose
// turbo-all

This workflow guides the creation of a new Compose-based RIB feature, migrating or implementing parallel to an existing view.

> **Reference**: This workflow uses `/implement-screen` for Figma extraction, token mapping, and image asset conversion steps. Refer to `implement-screen.md` for detailed instructions on those shared steps.

---

## TOKEN RULES (Use ONLY valid names — no guessing)

All tokens live under `PotionDimensions.*`, `PotionTextStyles.*`, or `LocalColors.current.*`.
Use ONLY the suffixes listed below. If a name isn't formed from these patterns, it doesn't exist — stop and report.

### PotionDimensions

| Category | Pattern | Valid suffixes |
|----------|---------|----------------|
| Spacing (gaps) | `layerStylesSpacingLayout{X}` | `00` `050` `100` `200` `300` `400` `500` `600` `800` `Neg100` `Neg200` `Neg400` `Neg500` `Neg600` |
| Spacing (card) | `layerStylesSpacingCard{X}` | `100` `200` `300` `400` |
| Padding | `layerStylesPaddingLayout{X}` | `0` `050` `100` `150` `200` `300` `400` |
| Padding (page) | `layerStylesPaddingPage{X}` | `0` `400` |
| Icon size | `layerStylesIcon{X}` | `300` `400` `500` `600` `800` *(≈12 16 24 32 40dp)* |
| Border radius | `layerStylesRadiusDefault{X}` | `100` `200` `300` `400` `600` `1000` *(≈4 8 12 16 24dp)* |
| Stroke width | `strokeWidth{Nav\|Content\|Surface}{X}` | Nav: `0` `025` `050` `100` · Content/Surface: `025` |

### PotionTextStyles

Pattern: `layerStyles{Style}{Size}{Weight}`

| Style | Sizes | Weights |
|-------|-------|---------|
| `Heading` | `14` `16` `18` `20` `24` | `Bold` `Critical` |
| `Body` | `12` `14` `16` `20` | `Critical` `Normal` `Bold` |
| `Caption` | `12` | `Critical` `Normal` `Bold` |
| `Caption` | `10` | `Critical` `Bold` *(Normal does NOT exist)* |
| `Display` | `28` `32` | *(no weight suffix)* |

### LocalColors

Pattern: `layerStylesColor{Category}{Semantic}`

| Category | Semantic suffixes |
|----------|-------------------|
| `BgBase` | `Default` |
| `BgSurface` | `Default{Primary\|Secondary\|Tertiary\|Disabled}` · `DefaultInv{Primary\|Secondary\|Tertiary\|Disabled}` · `{Emphasis\|Positive\|Critical\|Caution\|Brand\|Decorative}{Dark\|Light}` · `RewardsLight` |
| `Type` | `{Primary\|Secondary\|Tertiary\|Disabled}` · `{Primary\|Secondary\|Tertiary}Inv` · `Focus` `Emphasis` · `{Positive\|Critical\|Caution}{Inv?}` · `Decorative{Light\|Dark}{Inv?}` · `Rewards` |
| `StrokeBorder` | `{Dark\|Light}{Inv?}` · `Disabled` `Focus` `Emphasis` · `{Positive\|Critical\|Caution}{Inv?}` · `Decorative{Inv?}` · `Rewards{Inv?}` |
| `StrokeDivider` | `{Dark\|Light}{Inv?}` |
| `Icon` | same semantic suffixes as `Type` + `RewardsInv` |

### ❌ DEPRECATED — Never Use
```
qpad*                →  use layerStylesPaddingLayout*
qspace*              →  use layerStylesSpacingLayout*
qradius*             →  use layerStylesRadiusDefault*
layerStylesSizingIcon*  →  use layerStylesIcon*
layerStylesCaption10Normal  →  use layerStylesCaption10Critical or layerStylesCaption10Bold
```

---

## Step 1: Request Inputs
**CRITICAL**: You must ask the user for the following inputs immediately. Do not proceed until you have them.

> **Do NOT ask for Figma URLs here.** Figma URLs are collected later in Step 3 after the XML audit identifies all UI cases.

1.  **Feature Name**: The name of the Feature (e.g., `ReviewCart`, `RateOrder`). Used as `{FeatureName}` throughout.

2.  **Shared Module Folder Path**: Absolute path to the folder in the shared module where the Compose UI will live.

3.  **Platform Module Existing View File Path**: Absolute path to the existing View file in the Android module.

---

## Step 2: Deep XML Audit (BEFORE any Figma work)

> **Purpose**: Discover every UI section, conditional block, and state variation in the existing XML so that Figma coverage gaps can be detected before code generation.

### 2.1 Read the Existing View & Linked Layouts

1.  Read the Platform Module Existing View File (Input 3).
2.  Find **every XML layout** referenced by the View:
    - Direct `setContentView` / `inflate` calls
    - `<include layout="@layout/...">` tags (recursively — includes within includes)
    - `ViewStub` layouts
    - Adapter/ViewHolder item layouts (RecyclerView, ListView)
    - Any `LayoutInflater.inflate(R.layout.*)` calls in the View code
3.  Read **all** discovered XML layout files in full.

```bash
# Find all layout references in the View file
grep -E "R\.layout\.|@layout/" {platform_view_file}
# Then read each referenced layout under res/layout/
```

### 2.2 Catalog Every UI Section & Conditional Block

Walk through the XML(s) and the View/Presenter code to produce a **Section Inventory** — every distinct visual section and the condition that controls it.

**What to look for:**

| Signal in XML/Code | What it means |
|---------------------|---------------|
| `android:visibility="gone"` + code sets `VISIBLE` | Conditional section |
| `if (x) view.visible() else view.gone()` | Conditional section |
| `ViewStub` | Lazy-inflated section (always conditional) |
| `<include>` used multiple times | Reusable section with different data |
| RecyclerView adapter with multiple `viewType` | Multiple row/card variants |
| `when(state)` / `sealed class` in View | Multiple full-screen states |
| Different data populates same container | Same layout, different content states |

**Output format** — present this table to the user:

```markdown
## XML Section Inventory — {FeatureName}

| # | Section Name | XML ID / Layout | Condition / When Visible | Description |
|---|-------------|----------------|--------------------------|-------------|
| 1 | Toolbar | toolbar_root | Always | Back button + title + share |
| 2 | Trip Info | info_section | Always | Pickup time, fare, order ID |
| 3 | Cancelled Tag | cancelled_lyt | Trip status = CANCELLED | Red cancelled badge |
| 4 | Completed Tag | completed_lyt | Trip status = COMPLETED | Green completed badge |
| 5 | Vehicle Details | vehicle_section | Always | Vehicle image, name, plate |
| 6 | Rate Driver | rate_driver_section | Trip completed + NOT yet rated | Star rating bar |
| 7 | Rated Badge | rated_badge | Trip completed + already rated | Shows existing rating |
| 8 | Delivery Note | delivery_note_lyt | POD/delivery note exists | Download link + status tag |
| 9 | Cancellation Feedback | cancel_feedback | Trip cancelled + feedback available | Agree/disagree buttons |
| 10 | Fare Breakup | fare_section | Always | Fare rows + total |
| 11 | Payment Section | payment_section | Payment data exists | Payment mode rows |
| 12 | Bottom Actions | bottom_cta | Always (buttons vary) | Mail Invoice + Book Again |
| ... | ... | ... | ... | ... |
```

### 2.3 Analyze Existing VM

1.  **Extract VM File Path**:
    - Find the VM import statement in the existing View
    - Convert import to file path: replace dots with slashes, find in `shared/src/commonMain/kotlin/`
    - Read the VM file and list every `vm.property` and action
2.  **Identify XML IDs**: List all `R.id.*` for test tag generation
3.  **Map VM properties to sections**: For each section in the inventory, note which VM properties control its visibility and data

---

## Step 3: Figma Coverage Check (BLOCKING — Must Complete Before Code)

> **Purpose**: Collect Figma designs for ALL sections. The user provides a primary Figma URL first, then the skill identifies which sections are missing and asks for per-section Figma URLs.

### 3.1 Request Primary Figma URL

Ask: *"Please share the primary Figma URL for this screen."*

### 3.2 Extract Figma Data — Screenshot First

1. **Screenshot first** (primary source of truth for layout):
   ```
   mcp__figma-desktop__get_screenshot(nodeId)
   ```

2. **Design context** (secondary — for component names and hints):
   ```
   mcp__figma-desktop__get_design_context(nodeId)
   ```

3. **Validate the MCP response**: The design context returned must match the feature you're building. If it returns a component name that doesn't match (e.g., returns "BottomSheet" when you're building a "PaymentMode" card), **ignore the code and rely only on the screenshot**.

### 3.3 Cross-Reference Figma vs XML Inventory (CRITICAL)

Compare the Figma screenshot against the Section Inventory from Step 2.2. For **each section**, determine:

- **Covered**: The section is clearly visible in the Figma screenshot
- **Missing**: The section exists in XML but is NOT visible in the Figma screenshot (e.g., it's a different state, conditional block, alternate layout)

**Output format** — present this coverage report to the user:

```markdown
## Figma Coverage Report — {FeatureName}

### Covered by Primary Figma
| # | Section Name | Status |
|---|-------------|--------|
| 1 | Toolbar | Covered |
| 2 | Trip Info | Covered |
| 5 | Vehicle Details | Covered |
| 10 | Fare Breakup | Covered |
| 12 | Bottom Actions | Covered |

### Missing from Figma (need input)
| # | Section Name | Condition | What's Needed |
|---|-------------|-----------|---------------|
| 3 | Cancelled Tag | Trip = CANCELLED | Figma URL showing cancelled state |
| 6 | Rate Driver | Completed + unrated | Figma URL showing rating bar |
| 8 | Delivery Note | POD exists | Figma URL showing delivery note section |
| 9 | Cancellation Feedback | Cancelled + feedback | Figma URL showing feedback card |

Please provide Figma URLs for the missing sections above.
For each, you can share:
- A Figma URL for that specific section/state
- Or reply "use XML" if that section should follow the existing XML design
```

### 3.4 Collect Missing Figma URLs

Wait for the user to provide URLs for missing sections. Accept responses in this format:

```
Section 3 (Cancelled Tag): https://figma.com/design/FILE?node-id=123-456
Section 6 (Rate Driver): use XML
Section 8 (Delivery Note): https://figma.com/design/FILE?node-id=123-789
Section 9 (Cancellation Feedback): use XML
```

For each additional Figma URL provided, call `get_screenshot` and `get_design_context` (same as Step 3.2).

**Do NOT proceed to Step 4 until every section has either a Figma URL or an explicit "use XML" confirmation.**

### 3.5 Final Section Design Source Map

After collecting all inputs, produce the definitive source map:

```markdown
## Design Source Map — {FeatureName}

| # | Section Name | Design Source | Figma URL / Note |
|---|-------------|--------------|------------------|
| 1 | Toolbar | Figma (primary) | — |
| 2 | Trip Info | Figma (primary) | — |
| 3 | Cancelled Tag | Figma (secondary) | node-id=123-456 |
| 5 | Vehicle Details | Figma (primary) | — |
| 6 | Rate Driver | XML fallback | User confirmed |
| 8 | Delivery Note | Figma (secondary) | node-id=123-789 |
| 9 | Cancel Feedback | XML fallback | User confirmed |
| 10 | Fare Breakup | Figma (primary) | — |
| 12 | Bottom Actions | Figma (primary) | — |
```

---

## Step 4: Understand Design + Codebase (BEFORE generating any code)

### 4.0 Read Similar Existing ComposeViews (MANDATORY — Prevents Pattern Mismatches)

**Before writing code**, search the booking/payments module for 2 existing ComposeView files that are structurally similar to this feature (e.g., same layout pattern: card with list, form with inputs, etc.).

```bash
# Find ComposeViews in the same module
find {shared_module_root} -name "*ComposeView.kt" | head -20
```

**Read these 2 files in full** and note:
- How they structure `Card.OnSurface` (do they use `buildList {}` or `listOf {}`?)
- How they handle conditional rendering (`?.let`, `if`, `when`)
- What padding pattern they use (inner Row vs outer Column)
- How they apply `testResourceId`
- Import patterns (backtick imports for `in.porter.*`)

**This step prevents the most common structural mismatches.**

### 4.1 Layout Analysis from Screenshots (CRITICAL)

For **each Figma screenshot** (primary + all secondary URLs from Step 3.4), identify and document:

```markdown
## Layout Analysis — [Section/Case Name]

### Container
- Shape: [rounded corners / full-width / etc.]
- Background: [white / surface / brand / etc.]
- Border: [present / absent, color]
- Padding: [estimate in rough groups: tight ≈ 8dp, medium ≈ 12-16dp, loose ≈ 20-24dp]

### Elements (in order, top to bottom / left to right)
1. [Element type]: [content description, alignment, size estimate]
2. [Element type]: [content description, alignment, size estimate]
...

### Spacing between elements
- Between [A] and [B]: [tight/medium/loose]
```

For **"use XML" sections**: skip layout analysis — these will be implemented by reading the XML layout and translating to Compose directly.

### 4.2 Map Layout → Potion Tokens (LOOKUP, not guess)

For each visual property observed in the screenshots, select the matching token from the **AUTHORITATIVE TOKEN REFERENCE** at the top of this document:

| Visual Property | Observed Value | Mapped Token |
|----------------|---------------|--------------|
| Container background | White surface | `layerStylesColorBgSurfaceDefaultPrimary` |
| Container radius | ~8dp | `layerStylesRadiusDefault200` |
| Inner padding | ~16dp | `layerStylesPaddingLayout400` |
| Gap between icon and text | ~8dp | `layerStylesSpacingLayout200` |
| Title text | Bold 14sp | `layerStylesBody14Bold` |
| Subtitle text | Regular 12sp | `layerStylesCaption12Normal` |
| Icon size | ~24dp | `layerStylesIcon500` |
| ... | ... | ... |

**Token selection rules**:
- Spacing/gap between elements → `layerStylesSpacingLayout*`
- Padding inside a container → `layerStylesPaddingLayout*`
- Icon dimensions → `layerStylesIcon*` (300=12dp, 400=16dp, 500=24dp, 600=32dp, 800=40dp)
- Border radius → `layerStylesRadiusDefault*` (100≈4dp, 200≈8dp, 300≈12dp, 400≈16dp)
- Background of a Card/Surface → `layerStylesColorBgSurfaceDefaultPrimary` (NOT `layerStylesColorBgBaseDefault`)
- Background of a page/screen → `layerStylesColorBgBaseDefault`
- Regular body text color → `layerStylesColorTypePrimary`
- Secondary/hint text color → `layerStylesColorTypeSecondary`
- Borders → `layerStylesColorStrokeBorderLight` (light border) or `layerStylesColorStrokeBorderDark`

**STOP if a token mapping is uncertain.** Report it to the user before proceeding.

### 4.3 Compare All Cases (Multiple Figma URLs)

Create a comparison matrix across primary + all secondary Figma screenshots:

```markdown
| UI Element    | Primary | Secondary 1 | Secondary 2 | Pattern     | VM Property |
|---------------|---------|-------------|-------------|-------------|-------------|
| Element A     | ✅      | ✅          | ✅          | Always      | —           |
| Element B     | ✅      | ❌          | ✅          | Conditional | vm.propB    |
| Element C     | ❌      | ❌          | ✅          | Conditional | vm.propC    |
```

---

## Step 5: Create Token Mapping & Validate (BLOCKING)

Before writing any code, present the full token mapping table to confirm:

```markdown
## Token Mapping — {FeatureName}

| Design Element | Source | Figma Value | Potion Token | Token Exists? |
|---------------|--------|-------------|--------------|---------------|
| Card bg       | Figma  | #FFFFFF     | layerStylesColorBgSurfaceDefaultPrimary | ✅ |
| Card radius   | Figma  | 8dp         | layerStylesRadiusDefault200 | ✅ |
| Title font    | Figma  | Bold/14sp   | layerStylesBody14Bold | ✅ |
| Cancel icon   | XML    | —           | (from existing XML) | ✅ |
| ...           | ...    | ...         | ... | ... |

⚠️ UNCERTAIN MAPPINGS (need approval):
- [List any values you couldn't confidently map]
```

The **Source** column indicates whether the token was derived from a Figma screenshot or from the XML fallback.

**Only proceed to Step 6 when all mappings have ✅ confirmation.**

---

## Step 6: Create Shared Compose UI

### 6.1 Target Directory
Use the "Shared Module Folder Path" (Input 2). Create directory if needed.

### 6.2 Create Test Tags Object: `{FeatureName}TestTags.kt`

- Tag string values MUST be the **exact** `android:id` string from the XML layout — copy verbatim, no reformatting
  - XML: `android:id="@+id/deliveryTimeRoot"` → value: `"deliveryTimeRoot"` ✅
  - XML: `android:id="@+id/bookButton"` → value: `"bookButton"` ✅
  - ❌ Do NOT convert camelCase to snake_case (e.g. `"book_button"` is wrong if XML says `bookButton`)
- Always add `SCREEN_ROOT` first
- `SCREAMING_SNAKE_CASE` constant names, exact XML ID string values
- **Shared/included layouts**: If the same XML layout is `<include>`d multiple times (e.g. an option tile layout used for both standard and grouped), the inner IDs are identical. Consolidate into a single shared constant (not duplicated with prefixes):
  ```kotlin
  // ✅ CORRECT — shared layout IDs consolidated
  const val OPTION_TITLE = "title"        // same ID in both standard and grouped include
  const val TIME_ESTIMATE = "tvTimeEstimate"

  // ❌ WRONG — invented prefixes not in XML
  const val STANDARD_OPTION_TITLE = "standard_title"
  const val GROUPED_OPTION_TITLE = "grouped_title"
  ```

```kotlin
object {FeatureName}TestTags {
  const val SCREEN_ROOT = "featureNameRoot"       // from R.id.featureNameRoot
  const val SUBMIT_BUTTON = "submitButton"        // from R.id.submitButton
}
```

### 6.3 Create UI Events: `{FeatureName}UIEvents.kt`

```kotlin
sealed class {FeatureName}UIEvents {
  data object OnSubmitClick : {FeatureName}UIEvents()
  data class OnInputChange(val value: String) : {FeatureName}UIEvents()
}
```

### 6.4 Create Compose Files

**File structure** — one composable per file, all with `ComposeView` suffix:
```
compose/
├── {FeatureName}ComposeView.kt          ← root + @Preview only
├── {FeatureName}BottomSheetComposeView.kt
├── {FeatureName}ContentComposeView.kt
├── {FeatureName}HeaderComposeView.kt
├── SomeRowComposeView.kt                ← every sub-composable gets its own file
└── ...
```

> **⚠️ NO private sub-composables inside a file.** If you need a helper composable (e.g. `ConsentRowComposeView`, `SomeItemComposeView`), it MUST be a separate file with `internal` visibility — never a `private fun` inside another file. One `@Composable` function per file, no exceptions.

**CRITICAL implementation rules**:

#### Card Usage
```kotlin
// ✅ CORRECT
Card.OnSurface(
  modifier = Modifier.fillMaxWidth(),
  background = Card.Background.Color(
    value = LocalColors.current.layerStylesColorBgSurfaceDefaultPrimary,
  ),
  items = buildList {
    add { YourContent() }
    if (condition) add { ConditionalContent() }
  },
)

// ❌ WRONG — listOf with filterNotNull
items = listOf(
  { Content() },
  if (vm.x != null) { { ConditionalContent() } } else null,
).filterNotNull()
```

#### Text binding (STRICT)
```kotlin
// ✅ CORRECT
Text(text = vm.title, ...)

// ❌ WRONG — hardcoded string
Text(text = "Submit", ...)
```

#### Conditional rendering
```kotlin
// Nullable property
vm.badge?.let { badge -> BadgeView(badge) }

// Boolean flag
if (vm.showDivider) { Divider() }

// Sealed class variant
when (vm.state) {
  is State.Loading -> LoadingView()
  is State.Content -> ContentView(vm.state)
  is State.Error -> ErrorView(vm.state)
}
```

#### Test tags
```kotlin
import `in`.porter.potionui.utils.testResourceId

modifier = Modifier.testResourceId({FeatureName}TestTags.ELEMENT)
```

#### Imports (backtick required for `in.porter.*`)
```kotlin
import `in`.porter.customerapp.shared.loggedin.feature.compose.{FeatureName}UIEvents
import `in`.porter.potionui.components.Card
import `in`.porter.potionui.theme.LocalColors
import `in`.porter.potionui.theme.PotionDimensions
import `in`.porter.potionui.theme.PotionTextStyles
import `in`.porter.potionui.utils.testResourceId
```

#### Preview functions (MANDATORY — at least 2)
```kotlin
@Composable
@Preview
private fun Preview{FeatureName}ComposeView() {
  PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
    {FeatureName}ComposeView(vm = /* full sample data */, onEvent = {})
  }
}

@Composable
@Preview
private fun Preview{FeatureName}EmptyState() {
  PotionTheme(appLanguage = PotionLanguage.ENGLISH) {
    {FeatureName}ComposeView(vm = /* edge case data */, onEvent = {})
  }
}
```

### 6.5 Token Self-Validation (MANDATORY before compilation)

After writing each file, scan it and cross-check every token against the AUTHORITATIVE TOKEN REFERENCE:

```markdown
## Self-Validation — {FileName}

PotionDimensions tokens used:
- [ ] layerStylesPaddingLayout400 → ✅ exists in reference
- [ ] layerStylesSpacingLayout200 → ✅ exists in reference
- [ ] layerStylesIcon500 → ✅ exists in reference

PotionTextStyles tokens used:
- [ ] layerStylesBody14Bold → ✅ exists in reference
- [ ] layerStylesCaption12Normal → ✅ exists in reference

LocalColors tokens used:
- [ ] layerStylesColorBgSurfaceDefaultPrimary → ✅ exists in reference
- [ ] layerStylesColorTypePrimary → ✅ exists in reference
```

**Fix any token not found in the reference before proceeding.**

### 6.6 VM Movement (CRITICAL)

- Source: extracted from VM import in existing View (Step 2.3)
- Target: `view/` folder sibling to `compose/` (Input 2 parent + `/view/`)

```bash
mkdir -p {feature_root}/view
git mv {current_vm_path} {feature_root}/view/{FeatureName}VM.kt
```

Update package declaration in moved VM to match new location.

### 6.7 Image Assets

If design contains images/icons (not Potion built-in icons):
- Follow the SVG → XML conversion step from `/implement-screen`
- Save to `{module}/composeResources/drawable/`

---

## Step 6.8: Compile Shared Module & Auto-Fix (CRITICAL — Must Not Skip)

1.  **Extract module** from shared path (`booking`, `shared`, `payments`, etc.)

2.  **Run**:
    ```bash
    ./gradlew :{module}:compileDebugKotlinAndroid
    ```

3.  **Auto-fix patterns** (attempt up to 3 times):

    | Error | Fix |
    |-------|-----|
    | `layerStylesSizingIcon*` | → `layerStylesIcon*` |
    | `qpad*` | → `layerStylesPaddingLayout*` |
    | `qspace*` | → `layerStylesSpacingLayout*` |
    | `qradius*` | → `layerStylesRadiusDefault*` |
    | `layerStylesCaption10Normal` (doesn't exist) | → `layerStylesCaption10Critical` |
    | `optionalText` param | → `isOptional` |
    | `Button.Tertiary.Medium` | → `Button.Tertiary.DefaultMedium` |
    | `StickyCtaButtonStack` | → `StickyCta.StickyCtaButtonStack` |
    | Missing `import testResourceId` | Add: `import \`in\`.porter.potionui.utils.testResourceId` |
    | Missing `import painterResource` | Add: `import org.jetbrains.compose.resources.painterResource` |
    | VM import path (after move) | Update old path → new shared path |
    | `listOf(...).filterNotNull()` in Card | → `buildList { ... }` |
    | Missing Figma section designed from XML | Verify with Design Source Map (Step 3.5) |

4.  **Report**: ✅ success → Step 6.9 | ❌ after 3 attempts → report full errors + suggested fixes

---

## Step 6.9: Detekt & Brand-Name Linter Self-Review (CRITICAL — Must Not Skip)

> **Why**: `linter_run_action.yml` runs detekt and brand-name-linter only on PR — there is no local Gradle task for these. Violations found post-PR require extra fix commits. Catch them here first.

Scan every file written in Step 6.4. For each rule below, find and fix ALL violations before proceeding.

---

### Rule 1 — Brand Name Linter: No hardcoded "Porter" in strings

Check all `@Preview` functions and any hardcoded string literals.

```kotlin
// ❌ FAILS linter
title = "Porter Assist"
title = "Join Porter Gold & save more!"
title = "Porter Credits"

// ✅ PASS
title = "Assist"
title = "Join Gold & save more!"
title = "Credits"
```

**Scan**: grep every `"Porter` occurrence in new files. Remove the brand prefix.

---

### Rule 2 — OptionalWhenBraces: No braces on single-expression `when` branches

```kotlin
// ❌ FAILS detekt
when (vm) {
  is FooVM -> {
    SomeComposable(vm)   // single expression — braces not needed
  }
}

// ✅ PASS
when (vm) {
  is FooVM ->
    SomeComposable(vm)
}
```

**Exception**: braces are required when the branch has multiple statements (e.g., `val x = ...; Composable(x)`).

---

### Rule 3 — UseIfInsteadOfWhen: Two-branch `when` must be `if/else`

```kotlin
// ❌ FAILS detekt
val x = when (vm) {
  is FooVM -> valueA
  else -> valueB
}

// ✅ PASS
val x = if (vm is FooVM) valueA else valueB
```

---

### Rule 4 — MaxLineLength: No line > 120 characters

After writing each file, mentally scan for long lines. Common offenders:
- Inline `if/else` on a single line with long token names
- Chained `.modifier` calls

```kotlin
// ❌ FAILS detekt (> 120 chars)
gapLength = if (sectionIndex == vm.billItemVMs.lastIndex) PotionDimensions.spacingInputs0 else PotionDimensions.layerStylesSpacingLayout100,

// ✅ PASS
gapLength = if (sectionIndex == vm.billItemVMs.lastIndex) {
  PotionDimensions.spacingInputs0
} else {
  PotionDimensions.layerStylesSpacingLayout100
},
```

---

### Rule 5 — CyclomaticComplexMethod / CognitiveComplexMethod: Threshold is 15

Functions in Compose files that use `when` + nested `if` + lambdas accumulate complexity fast.

**Warning signs in a single function**:
- `when` with 3+ branches AND each branch has its own `if`
- `buildAnnotatedString { withStyle { } withStyle { } withStyle { } }`
- `?.let { }` blocks nested inside `when` branches

**Fix**: extract each `when` branch into a private `@Composable` function.

```kotlin
// ❌ Complex — everything inline
@Composable
fun MyView(vm: MyVM, onEvent: ...) {
  when (vm) {
    is MyVM.StateA -> {
      if (vm.showContainer) {
        Box(...) {
          Row(...) {
            buildAnnotatedString { ... }
            if (vm.enabled) Button(...) else Button(...)
          }
        }
      }
    }
    is MyVM.StateB -> { ... }
    is MyVM.StateC -> { ... }
  }
}

// ✅ Extracted — each branch is a separate file with internal visibility
@Composable
fun MyView(vm: MyVM, onEvent: ...) {
  when (vm) {
    is MyVM.StateA -> if (vm.showContainer) StateAComposeView(vm, onEvent)
    is MyVM.StateB -> if (vm.showContainer) StateBComposeView(vm, onEvent)
    is MyVM.StateC -> if (vm.showIneligible) StateCComposeView(vm)
  }
}

// StateAComposeView.kt  →  internal fun StateAComposeView(...)
// StateBComposeView.kt  →  internal fun StateBComposeView(...)
// StateCComposeView.kt  →  internal fun StateCComposeView(...)
```

---

### Self-Review Checklist (complete before Step 7)

For each file written:
- [ ] No `"Porter ..."` hardcoded strings anywhere
- [ ] All single-expression `when` branches use arrow syntax (no braces)
- [ ] All two-branch `when` expressions use `if/else`
- [ ] No line exceeds 120 characters
- [ ] No `@Composable` function has cyclomatic/cognitive complexity > 15
  - If a function has a `when` with 3+ branches AND nested `if`s → extract branches

---

## Step 7: Create Platform Compose RIB

### 7.1 Target Directory
`{platform_view_directory}/compose/`

### 7.2 Create `{FeatureName}ViewCompose.kt`
```kotlin
package {package_path}.compose

import android.content.Context
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import com.theporter.android.customerapp.loggedin.tripsflow.trips.v2.BaseComposeFrameLayout
import `in`.porter.customerapp.shared.applanguage.repo.AppLanguageRepo
import `in`.porter.customerapp.shared.{module_path}.{FeatureName}ComposeView
import `in`.porter.customerapp.shared.{module_path}.{FeatureName}UIEvents
import `in`.porter.customerapp.shared.{module_path}.view.{FeatureName}Presenter
import `in`.porter.customerapp.shared.{module_path}.view.{FeatureName}VM
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.filterIsInstance
import kotlinx.coroutines.flow.map

class {FeatureName}ViewCompose(
  context: Context,
  appLanguageRepo: AppLanguageRepo,
) : BaseComposeFrameLayout<{FeatureName}VM, {FeatureName}UIEvents>(
  context = context,
  appLanguageRepo = appLanguageRepo,
),
  {FeatureName}Presenter {

  @Composable
  override fun Content(vm: {FeatureName}VM, modifier: Modifier) {
    {FeatureName}ComposeView(
      vm = vm,
      onEvent = { event -> mutableUIEvents.tryEmit(event) },
    )
  }

  override fun render(vm: {FeatureName}VM) { updateVMStream(vm) }

  override fun onSubmit(): Flow<Unit> =
    uiEvents.filterIsInstance<{FeatureName}UIEvents.OnSubmitClick>().map { Unit }
}
```

### 7.3 Create `{FeatureName}BuilderCompose.kt`
```kotlin
class {FeatureName}BuilderCompose(dependency: ParentComponent) :
  ViewBuilder<{FeatureName}ViewCompose, {FeatureName}RouterCompose, {FeatureName}BuilderCompose.ParentComponent>(dependency) {

  fun build(
    parentViewGroup: ViewGroup,
    params: {FeatureName}Params,
    listener: {FeatureName}Listener,
  ): {FeatureName}RouterCompose {
    val view = createView(parentViewGroup)
    val interactorMP = {FeatureName}InteractorMPFactoryCompose.build(dependency, view, params, listener)
    val interactor = {FeatureName}InteractorCompose(interactorMP)
    val component = Dagger{FeatureName}BuilderCompose_Component.builder()
      .parentComponent(dependency)
      .view(view)
      .interactor(interactor)
      .interactorMP(interactorMP)
      .build()
    return component.{featureName}Router()
    // NOTE: Check XML builder — if it sets interactorMP.router = router, include it here
  }

  override fun inflateView(inflater: LayoutInflater, parentViewGroup: ViewGroup): {FeatureName}ViewCompose =
    {FeatureName}ViewCompose(
      context = parentViewGroup.context,
      appLanguageRepo = dependency.appLanguageRepo(),
    )

  interface ParentComponent : BaseRootComponent {
    fun appLanguageRepo(): AppLanguageRepo
  }
}
```

### 7.4 Create Router, Interactor, Factory

Follow existing XML-based counterparts. Copy and rename class suffix to `Compose`.

---

## Step 7.5: Compile Platform Module & Auto-Fix

```bash
./gradlew :app:compileDebugKotlin
```

Auto-fix same patterns as Step 6.8. Report after 3 attempts max.

---

## Step 8: Update Platform Dependencies (After VM Move)

```bash
grep -r "import.*{FeatureName}VM" {platform_module_path}
```

Update VM import path in every file found: VMMapper, Presenter, tests, old View.

Verify: `./gradlew :app:compileDebugKotlin`

---

## Step 9: Final Self-Review Checklist

Run through this checklist and report each item:

```markdown
### Data Binding
- [ ] All Text values bound to vm.property (no hardcoded strings)
- [ ] All visibility controlled by VM state
- [ ] All conditional elements have corresponding VM property mapping

### Design System Tokens
- [ ] Zero hardcoded dp/sp values
- [ ] Zero hardcoded colors (#hex or Color(...))
- [ ] All tokens confirmed in AUTHORITATIVE TOKEN REFERENCE above
- [ ] No deprecated tokens: qpad*, qradius*, qspace*, layerStylesSizingIcon*

### Structure
- [ ] One composable per file (ComposeView suffix)
- [ ] Root file contains only entry-point + @Preview
- [ ] VM in view/ folder (sibling to compose/)
- [ ] @Preview functions exist (min 2: normal + edge state)
- [ ] Test tags applied with testResourceId

### Platform Integration
- [ ] ViewCompose extends BaseComposeFrameLayout
- [ ] All UI events mapped in ViewCompose
- [ ] VM imports updated in VMMapper and Presenter

### Compilation
- [ ] Shared module: PASS
- [ ] Platform module: PASS
```

---

## Step 10: Generate Summary

```markdown
## ✅ RIB Feature Implementation Complete: {FeatureName}

### XML Sections Audited
- Total Sections: {n}
- Sections from Figma (primary): {count}
- Sections from Figma (secondary): {count}
- Sections from XML fallback: {count}

### Design Source Map
| Section | Source | Status |
|---------|--------|--------|
| Toolbar | Figma (primary) | ✅ implemented |
| Rate Driver | XML fallback | ✅ implemented |
| ... | ... | ... |

### Token Mapping Used
| Element | Source | Token |
|---------|--------|-------|
| Card bg | Figma | layerStylesColorBgSurfaceDefaultPrimary |
| ... | ... | ... |

### Conditional Rendering
| Element | Design Source | VM Property | Pattern |
|---------|-------------|-------------|---------|
| Element B | Figma | vm.propB | vm.propB?.let { } |

### Files Created
**Shared ({module})**
- {FeatureName}TestTags.kt
- {FeatureName}UIEvents.kt
- {FeatureName}ComposeView.kt
- view/{FeatureName}VM.kt (moved)

**Platform (app)**
- {FeatureName}ViewCompose.kt
- {FeatureName}BuilderCompose.kt
- {FeatureName}RouterCompose.kt
- {FeatureName}InteractorCompose.kt
- {FeatureName}InteractorMPFactoryCompose.kt

### Compilation
- Shared :{module}: ✅
- Platform :app: ✅
```

---

## Error Handling

| Situation | Action |
|-----------|--------|
| Figma MCP returns wrong component name | Ignore code output, use screenshot only |
| Token not found in reference | STOP, report to user, do not guess |
| Compilation fails after 3 attempts | Report full error log + file location + suggested manual fix |
| VM move fails | Fall back to `mv`, ensure target dir exists |
| Design gap / unmapped value | STOP, request user or designer input |
| Figma missing sections for XML cases | Present coverage report (Step 3.3), ask for per-section URLs |
| Figma Desktop not running | Instruct user to open Figma Desktop app |

---

## Critical Rules Summary

### Token Rules (Enforced by Reference Table)
- ✅ ALL tokens must exist in the AUTHORITATIVE TOKEN REFERENCE above
- ✅ Run token self-validation (Step 4.5) before compilation
- ❌ NEVER guess a token name — look it up in the reference
- ❌ NEVER use: qpad*, qradius*, qspace*, layerStylesSizingIcon*
- ❌ NEVER use layerStylesCaption10Normal (doesn't exist)

### XML Audit Rules
- ✅ Deep-dive XML BEFORE asking for any Figma URL (Step 2)
- ✅ Catalog every section, conditional block, and state variation (Step 2.2)
- ✅ Cross-reference Figma screenshot against XML section inventory (Step 3.3)
- ✅ Ask user for missing section Figma URLs — do NOT silently fall back to XML (Step 3.4)
- ✅ Only proceed to code after every section has a design source (Figma or explicit "use XML") (Step 3.5)

### Figma Rules
- ✅ Screenshot is primary source of truth (not React code from get_design_context)
- ✅ Validate that get_design_context response matches expected feature
- ✅ Extract ALL Figma cases before writing any code

### Code Rules
- ✅ Read 2 similar existing ComposeViews before writing (Step 4.0)
- ✅ One composable per file with ComposeView suffix — NO `private fun` sub-composables inside another file
- ✅ Sub-composables extracted to their own file with `internal` visibility
- ✅ Root file = entry point + @Preview only
- ✅ Use buildList {} for Card items (not listOf + filterNotNull)
- ✅ All Text bound to vm.property
- ✅ VM in view/ sibling folder (not inside compose/)
- ✅ Test tag string values are exact XML `android:id` strings (no reformatting, no invented prefixes)
- ✅ Minimum 2 @Preview functions
- ✅ Run compilation after shared AND platform modules
- ✅ Auto-fix up to 3 attempts before escalating

### Design Source Rules
- ✅ Track design source (Figma primary / Figma secondary / XML fallback) for every section
- ✅ Include source column in token mapping table (Step 5)
- ✅ Include source in final summary (Step 10)
- ❌ NEVER silently use XML design when Figma was expected — always ask

Now implement the RIB feature following all steps above automatically.
