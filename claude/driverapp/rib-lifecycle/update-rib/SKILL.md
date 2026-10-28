---
name: update-rib
description: Safely modify existing RIB components with explicit change types
---

You are updating an existing RIB module with surgical, explicit modifications.

## INPUTS REQUIRED

Ask the user for:
1. **RIB Name** - REQUIRED
2. **Update Type** - REQUIRED (one of):
    - `add-dependency` - Add new injected dependency to Builder
    - `add-child-rib` - Add child RIB routing to Router
    - `add-lifecycle-method` - Add Interactor lifecycle override
    - `rename` - Rename RIB completely
    - `move-parent` - Move RIB to different parent in hierarchy
    - `move-location` - Move RIB to different directory/package
    - `convert-to-compose` - Convert legacy View to Jetpack Compose
    - `add-analytics` - Add analytics tracking to RIB
    - `add-view-method` - Add method to View interface
    - `remove-dependency` - Remove injected dependency
    - `remove-child-rib` - Remove child RIB routing

3. **Type-Specific Inputs:**
    - For `add-dependency`: `--dependency=<Type>` (e.g., "UserRepository")
    - For `add-child-rib`: `--child-rib=<Name>` (e.g., "OrderDetails")
    - For `add-lifecycle-method`: `--method=<Signature>` (e.g., "onStart()")
    - For `rename`: `--new-name=<Name>` (e.g., "PaymentFlow")
    - For `move-parent`: `--new-parent=<ParentRibName>` (e.g., "Checkout")
    - For `move-location`: `--target-path=<path>` (e.g., "ribs/checkout/order_summary")
    - For `convert-to-compose`: No additional inputs required
    - For `add-analytics`: `--events=<event1,event2>` (optional, e.g., "ScreenViewed,ActionCompleted")
    - For `add-view-method`: `--method=<Signature>` (e.g., "showError(String)")

4. **Options:**
    - `--dry-run` - Preview changes without applying
    - `--no-backup` - Skip backup creation (not recommended)

## PRE-UPDATE VALIDATION

Before making any changes:

1. **Locate RIB files** using Glob/Grep
2. **Read all relevant files** to understand current structure
3. **Validate update is safe:**
    - Check dependency exists in Dagger graph
    - Verify child RIB exists (for add-child-rib)
    - Check for duplicate dependencies/children
4. **Create backup** in `.claude/rib-backups/{timestamp}/{rib_name}/`

## UPDATE OPERATIONS

### 1. ADD-DEPENDENCY

**What it does:**
Adds a new constructor parameter to Interactor and wires it through Builder/Component.

**Steps:**
1. Add parameter to Interactor constructor:
```kotlin
class {RibName}Interactor @Inject constructor(
    private val existingDep: ExistingType,
    private val {newDepName}: {NewDepType}  // NEW
) {
```

2. Add to Component's ParentDependency interface (if not provided by Dagger):
```kotlin
interface ParentDependency {
    fun {newDepName}(): {NewDepType}  // NEW
}
```

3. No changes needed to Builder (Dagger handles it automatically)

**Validation:**
- Check {NewDepType} is available in parent Component or Dagger graph
- Warn if dependency is already injected
- Suggest qualifier annotation if type is ambiguous

### 2. ADD-CHILD-RIB

**What it does:**
Adds routing logic to Router for attaching/detaching a child RIB.

**Steps:**
1. Verify child RIB exists (use Glob to search)
2. Add child RIB builder to Router dependencies:
```kotlin
class {RibName}Router @Inject constructor(
    private val interactor: {RibName}Interactor,
    private val {childName}Builder: {ChildName}Builder  // NEW
) {
```

3. Add routing methods:
```kotlin
private var {childName}Child: {ChildName}Interactor? = null

fun attach{ChildName}() {
    if ({childName}Child == null) {
        {childName}Child = {childName}Builder.build()
        {childName}Child?.onAttach()
    }
}

fun detach{ChildName}() {
    {childName}Child?.onDetach()
    {childName}Child = null
}
```

4. Add child Component to parent Component:
```kotlin
@{RibName}Scope
@Subcomponent(modules = [
    {ChildName}Component::class  // NEW
])
interface {RibName}Component {
```

**Validation:**
- Child RIB must exist
- Child Component must be defined
- Warn if child already routed

### 3. ADD-LIFECYCLE-METHOD

**What it does:**
Adds lifecycle hook methods to Interactor (onStart, onStop, onResume, onPause).

**Steps:**
1. Add method to Interactor:
```kotlin
fun {methodName}() {
    // TODO: Implement lifecycle logic
}
```

2. Document when it should be called
3. Suggest where parent should invoke it

**Validation:**
- Method name must be valid lifecycle method
- Warn if method already exists

### 4. RENAME

**What it does:**
Renames entire RIB module (all files, classes, package).

**Steps:**
1. **Analyze impact:**
    - Find all references to current RIB name in codebase
    - Check parent Router references
    - Find test files

2. **Show preview:**
```
Renaming: {OldName} → {NewName}

Files to rename:
  {OldName}Builder.kt → {NewName}Builder.kt
  {OldName}Component.kt → {NewName}Component.kt
  {OldName}Interactor.kt → {NewName}Interactor.kt
  {OldName}Router.kt → {NewName}Router.kt

Classes to rename:
  {OldName}Builder → {NewName}Builder
  {OldName}Component → {NewName}Component
  {OldName}Interactor → {NewName}Interactor
  {OldName}Router → {NewName}Router
  @{OldName}Scope → @{NewName}Scope

References to update: 15 files
```

3. **Execute rename:**
    - Update class names in all files
    - Update scope annotation
    - Rename files
    - Update package name if needed
    - Update imports in referencing files

**Validation:**
- New name must not conflict with existing RIB
- Confirm with user before executing (show impact)
- Warn if >10 files need updates

### 5. ADD-VIEW-METHOD

**What it does:**
Adds a method to View interface (if View-based RIB).

**Steps:**
1. Check if View exists
2. Add method signature:
```kotlin
class {RibName}View {
    fun {methodName}({params}) {
        // TODO: Implement view logic
    }
}
```

**Validation:**
- View must exist
- Method signature must be valid Kotlin
- Warn if method already exists

### 6. REMOVE-DEPENDENCY

**What it does:**
Removes injected dependency from Interactor.

**Steps:**
1. Remove from Interactor constructor
2. Remove from ParentDependency interface if defined there
3. Search for usages in Interactor and warn user

**Validation:**
- Dependency must exist
- Warn if dependency is used in Interactor (show usage locations)
- Require confirmation if usages found

### 7. REMOVE-CHILD-RIB

**What it does:**
Removes child RIB routing from Router.

**Steps:**
1. Remove child builder dependency from Router
2. Remove attach/detach methods
3. Remove child reference variable
4. Remove from Component modules list

**Validation:**
- Child routing must exist
- Warn if attach method is called from other code
- Suggest deleting child RIB if no longer used

### 8. MOVE-PARENT

**What it does:**
Moves RIB to different parent in the RIB hierarchy (changes which RIB routes to it).

**Use Case:**
User says: "I want to move OrderSummary RIB from PaymentPlatform to Checkout"

**Steps:**
1. **Analyze current state:**
```bash
# Find current parent
grep -r "{RibName}Builder" app/src/main/java/com/theporter/android/driverapp/ribs/
```

Output:
```
Current Parent: PaymentPlatformRouter
  - File: ribs/payment_platform/PaymentPlatformRouter.kt
  - Routing: attachOrderSummary()
```

2. **Verify new parent exists:**
```bash
# Check new parent RIB
ls app/src/main/java/com/theporter/android/driverapp/ribs/{new_parent}/
```

3. **Remove from old parent:**
   - Remove Builder injection from old parent Router
   - Remove attach/detach methods from old parent Router
   - Remove from old parent Component subcomponents list

4. **Add to new parent:**
   - Add Builder injection to new parent Router
   - Add attach/detach methods to new parent Router
   - Add to new parent Component subcomponents list

5. **Update Component ParentDependency:**
   - Review dependencies from old parent
   - Add missing dependencies to new parent's ParentDependency
   - Remove dependencies only available from old parent

**Preview:**
```diff
Old Parent (PaymentPlatformRouter.kt):
- private val orderSummaryBuilder: OrderSummaryBuilder
- fun attachOrderSummary() { ... }
- fun detachOrderSummary() { ... }

New Parent (CheckoutRouter.kt):
+ private val orderSummaryBuilder: OrderSummaryBuilder
+ fun attachOrderSummary() { ... }
+ fun detachOrderSummary() { ... }

{RibName}Component.kt:
  interface ParentDependency {
-   fun paymentProcessor(): PaymentProcessor  // Only in PaymentPlatform
+   fun orderValidator(): OrderValidator      // Available in Checkout
  }
```

**Validation:**
- New parent must exist
- Check dependency compatibility (new parent must provide required deps)
- Warn if navigation paths break
- Confirm with user about scope hierarchy change

### 9. MOVE-LOCATION

**What it does:**
Moves RIB files to different directory/package within same module.

**Use Case:**
User says: "Move OrderSummary from ribs/payment_platform/ to ribs/checkout/order_summary/"

**Steps:**
1. **Analyze current location:**
```
Current: app/src/main/java/com/theporter/android/driverapp/ribs/payment_platform/order_summary/
Target:  app/src/main/java/com/theporter/android/driverapp/ribs/checkout/order_summary/
```

2. **Show impact:**
```
Files to move (5):
  {RibName}Builder.kt
  {RibName}Component.kt
  {RibName}Interactor.kt
  {RibName}Router.kt
  {RibName}View.kt

Package change:
  Old: com.theporter.android.driverapp.ribs.payment_platform.order_summary
  New: com.theporter.android.driverapp.ribs.checkout.order_summary

Imports to update in 8 files:
  - PaymentPlatformRouter.kt
  - CheckoutInteractor.kt
  - ...
```

3. **Execute move:**
   - Create new directory structure
   - Update package declarations in all RIB files
   - Move files to new location
   - Update imports in all referencing files
   - Delete old directory if empty

**Validation:**
- Target directory must be valid path
- No naming conflicts at target location
- All imports must resolve after move

### 10. CONVERT-TO-COMPOSE

**What it does:**
Converts legacy Android View-based RIB to Jetpack Compose architecture (3-module pattern).

**Use Case:**
User says: "Convert OrderSummary RIB to use Jetpack Compose"

**Steps:**
1. **Analyze current RIB:**
   - Check if View file exists
   - Check if already using Compose
   - Identify view state and methods

2. **Create Shared module files:**
```kotlin
// shared/.../view/{RibName}Presenter.kt
interface {RibName}Presenter : BasePresenter<{RibName}VM> {
  suspend fun onButtonClicked(): ClicksFlow
}

// shared/.../view/{RibName}VM.kt
data class {RibName}VM(
  val displayText: String,
  val isLoading: Boolean,
) : BaseVM

// shared/.../view/{RibName}VMMapper.kt
class {RibName}VMMapper : BaseVMMapper<{RibName}Params, {RibName}State, {RibName}VM>()

// shared/.../state/{RibName}State.kt
data class {RibName}State(val data: String = "")

// shared/.../state/{RibName}StateReducer.kt
class {RibName}StateReducer : StateReducer<{RibName}State>()
```

3. **Create UI module files:**
```kotlin
// ui/.../RibName}ComposeBridge.kt
class {RibName}ComposeBridge : KMPUpstreamBridge<{RibName}VM, {RibName}UIEvents>(), {RibName}Presenter

// ui/.../{RibName}ComposeView.kt
@Composable
fun {RibName}ComposeView(vm: {RibName}VM, uiEventsHandler: UIEventsHandler)

// ui/.../{RibName}VMFactory.kt
object {RibName}VMFactory
```

4. **Update App module:**
   - Update Builder to use new shared Interactor
   - Add TypeAlias file
   - Update Module for Dagger

5. **Migration guide:**
```
✓ Created shared module files (7 files)
✓ Created UI module files (3 files)
✓ Updated app module (2 files)

Legacy files to review and delete:
  ⚠️  {RibName}View.kt (contains view logic to migrate)

Next steps:
  1. Migrate view logic from View.kt to ComposeView.kt
  2. Test the Compose UI
  3. Delete legacy View.kt
  4. Update tests
```

**Validation:**
- RIB must have View file
- Shared/UI modules must exist
- Warn about manual migration needed for complex view logic

### 11. ADD-ANALYTICS

**What it does:**
Adds analytics tracking infrastructure to RIB.

**Use Case:**
User says: "Add analytics tracking to OrderSummary RIB"

**Steps:**
1. **Add AnalyticsManager dependency:**
```kotlin
class {RibName}Interactor @Inject constructor(
    private val analyticsManager: AnalyticsManager,  // NEW
) {
```

2. **Create Analytics event class:**
```kotlin
// {RibName}Analytics.kt
sealed class {RibName}AnalyticsEvent(
  override val eventName: String,
  override val properties: Map<String, Any>
) : AnalyticsEvent {

  data class ScreenViewed(val params: {RibName}Params) : {RibName}AnalyticsEvent(
    eventName = "{rib_name}_screen_viewed",
    properties = mapOf("user_id" to params.userId)
  )

  data class ActionCompleted(val action: String) : {RibName}AnalyticsEvent(
    eventName = "{rib_name}_action_completed",
    properties = mapOf("action" to action)
  )
}
```

3. **Add tracking calls in Interactor:**
```kotlin
override suspend fun onActive() {
  super.onActive()
  analyticsManager.track({RibName}AnalyticsEvent.ScreenViewed(params))
}

private fun handleSubmit() {
  analyticsManager.track({RibName}AnalyticsEvent.ActionCompleted("submit"))
}
```

**Validation:**
- AnalyticsManager must be available in Dagger graph
- Event names should follow naming convention

### 12. ADDITIONAL UPDATE OPERATIONS

Other useful update operations to add:

**12a. ADD-DEEP-LINK**
- Add deep link handling to RIB
- Register deep link routes
- Add navigation parameters

**12b. ADD-ERROR-HANDLING**
- Add error state to State
- Add error reducer methods
- Add error UI in View/Compose

**12c. SPLIT-RIB**
- Split large RIB into parent + child RIBs
- Extract functionality to new child
- Maintain parent routing

**12d. MERGE-RIBS**
- Combine two small RIBs into one
- Merge functionality
- Update parent routing

## CHANGE PREVIEW (--dry-run)

Before applying changes, show diff:
```diff
File: {RibName}Interactor.kt

@@ -5,6 +5,7 @@
 class OrderSummaryInteractor @Inject constructor(
     private val orderRepository: OrderRepository,
+    private val userRepository: UserRepository,
 ) {

     fun onAttach() {
```

Ask user: "Apply these changes? (yes/no)"

## BACKUP STRATEGY

Before any modification:
1. Create `.claude/rib-backups/{timestamp}/`
2. Copy all RIB files to backup directory
3. Log backup location
4. Backups retained for 30 days

Output:
```
✓ Backup created: .claude/rib-backups/2026-01-27_14-30-00/order_summary/
```

## SAFETY RULES

- ALWAYS require explicit confirmation before applying changes
- ALWAYS create backup unless `--no-backup` specified
- ALWAYS validate Kotlin syntax after modifications
- NEVER modify unrelated files without dependency relationship
- NEVER auto-refactor business logic
- NEVER change Dagger scope annotations without explicit request
- PRESERVE existing code formatting and style
- SHOW diff before applying changes

## ERROR HANDLING

If dependency not found:
```
❌ Dependency '{NewDepType}' not found in Dagger graph.

Searched in:
  - {RibName}Component
  - Parent Component
  - Application Component

Suggestions:
  1. Add @Provides method in {RibName}Component
  2. Add to ParentDependency interface
  3. Check spelling and package name
```

If child RIB not found:
```
❌ Child RIB '{ChildName}' not found.

Run: /create-rib {ChildName} parent_path=ribs/{parent_path}
```

## SUCCESS OUTPUT

After successful update:
```
✅ Updated {RibName} successfully!

Changes applied:
  ✓ Added dependency: UserRepository
  ✓ Updated Interactor constructor
  ✓ Updated Component ParentDependency

Files modified:
  - {RibName}Interactor.kt
  - {RibName}Component.kt

Backup location: .claude/rib-backups/{timestamp}/

Next steps:
  - Implement logic using new dependency
  - Update tests to inject mock dependency
```
