---
name: read-rib
description: Inspect RIB structure, dependencies, lifecycle, and architectural compliance
---

You are inspecting an existing RIB module to understand its structure, dependencies, and architectural compliance.

## INPUTS REQUIRED

Ask the user for:
1. **RIB Name** (e.g., "PaymentPlatform") - REQUIRED
2. **Analysis Options:**
    - `--show-dependencies` - Display Dagger dependency graph
    - `--show-children` - List child RIBs routed by this RIB
    - `--show-parents` - Find which RIBs route to this RIB (parent hierarchy)
    - `--show-usages` - Find all places where this RIB is referenced in code
    - `--show-responsibility` - Analyze what functionality this RIB handles
    - `--show-lifecycle` - Show Interactor lifecycle method implementations
    - `--show-all` - Display complete analysis (all options above)
    - `--validate` - Run architecture validation checks
    - `--format=json|text` - Output format (default: text)

## EXECUTION STEPS

### 1. Locate RIB Files

Search for RIB by name in `app/src/main/java/com/theporter/android/driverapp/ribs/`:
- `{RibName}Builder.kt`
- `{RibName}Component.kt`
- `{RibName}Interactor.kt`
- `{RibName}Router.kt` (optional)
- `{RibName}View.kt` (optional)

If not found, search recursively and report location.

### 2. Parse and Display Structure

**Basic Information:**
```
RIB: {RibName}
Location: {full_path}
Package: {package_name}
Components Present:
  ✓ Builder
  ✓ Component
  ✓ Interactor
  ✓ Router (or ✗ if missing)
  ✓ View (or ✗ if missing)
```

**Component Analysis:**
- Scope annotation: `@{RibName}Scope`
- Subcomponent annotation present: Yes/No
- ParentDependency interface methods
- Injected dependencies list

**Interactor Analysis:**
- Lifecycle methods implemented: onAttach(), onDetach()
- Listener interface defined: Yes/No with method count
- Injected dependencies (from constructor)
- Public methods exposed

**Builder Analysis:**
- Injection type: Constructor injection / Field injection
- Build method return type
- Dependencies required from parent

### 3. Show Dependencies (if --show-dependencies)

Display dependency tree:
```
{RibName}Interactor dependencies:
  ├─ SomeDependency (@Inject constructor)
  ├─ AnotherDependency (from ParentDependency)
  └─ ThirdDependency (@Provides from module)
```

Analyze:
- Where each dependency comes from
- Dagger qualifier annotations used
- Potential circular dependencies

### 4. Show Children (if --show-children)

Parse Router file to extract child RIBs:
```
Child RIBs routed by {RibName}:
  1. ChildRibA (attached via attachChildA())
  2. ChildRibB (attached via attachChildB())
```

Show routing logic and attachment points.

### 5. Show Lifecycle (if --show-lifecycle)

Display lifecycle methods in Interactor:
```kotlin
Lifecycle Methods:
  ✓ onAttach() - {line_count} lines
  ✓ onDetach() - {line_count} lines

Additional Methods:
  - methodA({params}) - {line_count} lines
  - methodB({params}) - {line_count} lines
```

### 6. Validate Architecture (if --validate)

Run checks using `ribs-architecture-validator` skill principles:

**Check 1: Interactor Purity**
- ✓ No Android framework imports (Activity, Context, View)
- ✗ Found import: android.content.Context in line 15

**Check 2: Dependency Direction**
- ✓ No parent Interactor references
- ✓ Communication via Listener interface

**Check 3: Scope Hygiene**
- ✓ Custom scope annotation defined
- ✓ Scope matches component hierarchy

**Check 4: Naming Consistency**
- ✓ File names match class names
- ✗ Expected {RibName}Builder.kt, found {RibName}Build.kt

**Check 5: Dagger Integration**
- ✓ Component is @Subcomponent
- ✗ Builder missing @Inject annotation

### 7. Show Parents (if --show-parents)

Use the Grep tool to find which RIBs route to this RIB:
- Search pattern: `{RibName}Builder`
- Search path: `app/src/main/java/com/theporter/android/driverapp/ribs/`
- Glob filter: `**/*Router.kt`
- Output mode: `content` with line numbers

Output:
```
Parent RIBs:
  1. PaymentPlatformRouter
     - File: ribs/payment_platform/PaymentPlatformRouter.kt:45
     - Routing method: attachOrderSummary()
     - Builder injection: private val orderSummaryBuilder: OrderSummaryBuilder

  2. CheckoutRouter (conditional)
     - File: ribs/checkout/CheckoutRouter.kt:78
     - Routing method: attachOrderSummaryIfNeeded()

Navigation Path from Root:
  RootRIB → LoggedInRIB → PaymentPlatformRIB → {RibName}
```

### 8. Show Usages (if --show-usages)

Use the Grep tool to find ALL references to this RIB in the codebase:
- Search pattern: `{RibName}Interactor|{RibName}Builder|{RibName}Router|{RibName}Component`
- Search paths: `app/src/main/java/`, `shared/src/`, `ui/src/`
- Output mode: `content` with line numbers

Output:
```
References found in 12 files:

Production Code (8 files):
  1. PaymentPlatformRouter.kt (3 references)
     - Line 23: private val orderSummaryBuilder: OrderSummaryBuilder
     - Line 45: fun attachOrderSummary()
     - Line 52: orderSummaryBuilder.build()

  2. CheckoutInteractor.kt (1 reference)
     - Line 89: // Navigate to OrderSummary after validation

  3. PaymentPlatformComponent.kt (1 reference)
     - Line 15: @Subcomponent(modules = [OrderSummaryComponent::class])

Test Files (4 files):
  4. OrderSummaryInteractorTest.kt (12 references)
  5. PaymentPlatformRouterTest.kt (2 references)
  ...

Summary:
  - Used by: 2 parent RIBs
  - Referenced in: 8 production files, 4 test files
  - Total references: 18
```

### 9. Show Responsibility (if --show-responsibility)

Analyze what this RIB is responsible for by reading Interactor code:

**Analysis Steps:**
1. Read Interactor file completely
2. Extract public methods (functionality exposed to parent)
3. Extract Listener methods (events sent to parent)
4. Analyze business logic and state management
5. Identify API calls, repositories, and data sources used

Output:
```
{RibName} Responsibilities:

Primary Function:
  Display order summary and handle user confirmation for payment flow

Public API (exposed to parent):
  - refreshOrderDetails() - Reloads order data from backend
  - applyPromoCode(code: String) - Validates and applies promo code
  - proceedToPayment() - Initiates payment flow

Events to Parent (Listener):
  - onOrderConfirmed(orderId: String) - User confirmed the order
  - onOrderCancelled() - User cancelled from order summary
  - onPaymentInitiated(amount: Double) - Payment flow started

State Management:
  - OrderSummaryState (data class)
  - Loading, Error, Success states
  - Handles: order details, promo codes, pricing breakdown

Dependencies Used:
  - OrderRepository - Fetch order details
  - PromoCodeValidator - Validate promo codes
  - AnalyticsManager - Track user actions
  - UserPreferences - Get user settings

Key Business Logic:
  1. Load order details on attach
  2. Calculate total with taxes and discounts
  3. Validate promo codes with backend
  4. Handle payment initiation
  5. Track analytics events

Complexity Score: Medium (150 lines, 3 dependencies, 2 child RIBs)
```

### 10. Show Navigation Path

Trace how user reaches this RIB from Root:
```
Navigation Path:
  RootRIB → LoggedInRIB → PaymentPlatformRIB → OrderSummaryRIB
```

### 11. Output Format

**Text Format (default):**
Human-readable with colors and symbols (✓ ✗ ⚠)

**JSON Format:**
```json
{
  "ribName": "OrderSummary",
  "location": "...",
  "components": {
    "builder": true,
    "component": true,
    "interactor": true,
    "router": true,
    "view": false
  },
  "dependencies": [...],
  "children": [...],
  "validation": {
    "interactorPurity": true,
    "scopeHygiene": true,
    "namingConsistency": false,
    "issues": [...]
  }
}
```

## SAFETY RULES

- This is READ-ONLY - never modify files
- Handle missing files gracefully
- Report incomplete RIBs (missing components)
- Validate Kotlin syntax before parsing
- Never execute code or trigger side effects
- Never access runtime state or logs

## ERROR HANDLING

If RIB not found:
```
❌ RIB '{RibName}' not found in ribs/ directory.

Searching entire codebase...
Found similar names:
  - PaymentPlatformRib (ribs/payment_platform/)
  - PaymentSelection (ribs/payment_platform/payment_selection/)

Did you mean one of these?
```

If RIB incomplete:
```
⚠️  RIB '{RibName}' is incomplete. Found:
  ✓ Interactor
  ✓ Component
  ✗ Builder (missing)
  ✗ Router (missing)
```
