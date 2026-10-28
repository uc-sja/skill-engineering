---
name: delete-rib
description: Remove RIB module with comprehensive dependency analysis and safety validation
---

You are deleting a RIB module. This is a DESTRUCTIVE operation requiring careful analysis and explicit confirmation.

## INPUTS REQUIRED

Ask the user for:
1. **RIB Name** - REQUIRED
2. **Confirmation Flag:** `--confirm` - REQUIRED to actually delete
3. **Options:**
    - `--soft-delete` - Comment out routing instead of full deletion
    - `--force` - Skip some safety checks (DANGEROUS, requires second confirmation)
    - `--analyze-only` - Show impact analysis without deleting

## EXECUTION PHASES

### PHASE 1: ANALYSIS (ALWAYS RUN FIRST)

#### Step 1: Locate RIB Files

Search for all RIB components across all three modules:
```
Locating RIB: {RibName}

APP Module (app/src/main/java/):
  ✓ {RibName}Builder.kt
  ✓ {RibName}Interactor.kt
  ✓ {RibName}Router.kt
  ✓ {RibName}Module.kt
  ✓ {RibName}Alias.kt

SHARED Module (shared/src/commonMain/kotlin/):
  ✓ {RibName}Builder.kt
  ✓ {RibName}Interactor.kt
  ✓ {RibName}Router.kt
  ✓ dependency/{RibName}Params.kt
  ✓ dependency/{RibName}Listener.kt (if exists)
  ✓ dependency/{RibName}Dependency.kt (if exists)
  ✓ state/{RibName}State.kt
  ✓ state/{RibName}StateReducer.kt
  ✓ view/{RibName}Presenter.kt
  ✓ view/{RibName}VM.kt
  ✓ view/{RibName}VMMapper.kt
  ✓ analytics/{RibName}Analytics.kt
  ✓ analytics/{RibName}EventIdentifiers.kt

UI Module (ui/src/main/java/):
  ✓ {RibName}ComposeBridge.kt
  ✓ {RibName}ComposeView.kt
  ✓ {RibName}VMFactory.kt

Test Files (shared/src/test/kotlin/):
  ✓ {RibName}InteractorTestHelper.kt
  ✓ {RibName}InteractorStepDefs.kt
```

#### Step 2: Find Parent RIB

Use the Grep tool to search for Router files that reference this RIB:
- Search pattern: `{RibName}Builder`
- Search path: `app/src/main/java/com/theporter/android/driverapp/ribs/`
- Output mode: `content` with line numbers

Output:
```
Parent RIB: PaymentPlatformRouter
  - Routing method: attachOrderSummary()
  - Line 45: private val orderSummaryBuilder: OrderSummaryBuilder
```

#### Step 3: Find Child RIBs

Parse Router (if exists) to find children:
```
Child RIBs (will become orphaned):
  ⚠️  OrderDetailsRIB
  ⚠️  PaymentMethodRIB
```

#### Step 4: Find Dagger References

Use the Grep tool to search for Component references:
- Search pattern: `{RibName}Component`
- Search path: `app/src/main/java/`
- Output mode: `content` with line numbers

Output:
```
Dagger References:
  - PaymentPlatformComponent.kt (line 12): @Subcomponent(modules = [OrderSummaryComponent::class])
  - AppComponent.kt (line 45): includes OrderSummaryComponent
```

#### Step 5: Find Code References

Use the Grep tool to search entire codebase for RIB class usages:
- Search pattern: `{RibName}Interactor|{RibName}Builder|{RibName}Router`
- Search paths: `app/src/main/java/`, `shared/src/`, `ui/src/`
- Output mode: `content` with line numbers

Output:
```
References found in 8 files:
  1. PaymentPlatformRouter.kt (3 references)
  2. CheckoutFlowInteractor.kt (1 reference)
  3. OrderSummaryInteractorTest.kt (12 references - test file)
  ...
```

#### Step 6: Check Git History

```bash
git log --oneline --all -- "*{RibName}*" | head -5
```

Output:
```
Recently modified:
  ⚠️  Modified 2 days ago by john.doe
  ⚠️  Commit: "Fix payment calculation in OrderSummary"
```

#### Step 7: Calculate Blast Radius

```
IMPACT ANALYSIS
═══════════════

RIB: OrderSummary
Locations:
  - app/src/main/java/.../ribs/root/payment_platform/order_summary/
  - shared/src/commonMain/kotlin/.../shared/root/payment_platform/order_summary/
  - ui/src/main/java/.../ui/driverapp/root/payment_platform/order_summary/

APP Module files to delete: 5
  - OrderSummaryBuilder.kt
  - OrderSummaryInteractor.kt
  - OrderSummaryRouter.kt
  - OrderSummaryModule.kt
  - OrderSummaryAlias.kt

SHARED Module files to delete: 13
  - OrderSummaryBuilder.kt
  - OrderSummaryInteractor.kt
  - OrderSummaryRouter.kt
  - dependency/OrderSummaryParams.kt
  - dependency/OrderSummaryListener.kt (if exists)
  - dependency/OrderSummaryDependency.kt (if exists)
  - state/OrderSummaryState.kt
  - state/OrderSummaryStateReducer.kt
  - view/OrderSummaryPresenter.kt
  - view/OrderSummaryVM.kt
  - view/OrderSummaryVMMapper.kt
  - analytics/OrderSummaryAnalytics.kt
  - analytics/OrderSummaryEventIdentifiers.kt

UI Module files to delete: 3
  - OrderSummaryComposeBridge.kt
  - OrderSummaryComposeView.kt
  - OrderSummaryVMFactory.kt

Test files to delete: 2
  - OrderSummaryInteractorTestHelper.kt
  - OrderSummaryInteractorStepDefs.kt

Parent RIB impact: 1
  ⚠️  PaymentPlatformRouter - must remove routing logic

Child RIBs (orphaned): 2
  🛑 OrderDetailsRIB - BLOCKER: delete or re-parent first
  🛑 PaymentMethodRIB - BLOCKER: delete or re-parent first

Code references: 8 files
  ⚠️  CheckoutFlowInteractor.kt - manual cleanup needed

Dagger cleanup needed: 2 files
  - PaymentPlatformComponent.kt
  - AppComponent.kt

Git activity: Modified 2 days ago
  ⚠️  Recently modified - verify with team

Total files affected: 18

RISK LEVEL: 🔴 HIGH (has child RIBs and external references)
```

### PHASE 2: DECISION & RECOMMENDATION

Based on analysis, provide recommendation:

#### BLOCKER CONDITIONS (cannot delete without --force):

1. **Has child RIBs:**
```
🛑 BLOCKED: Cannot delete RIB with children.

Child RIBs must be deleted or re-parented first:
  - Run: /delete-rib OrderDetailsRIB --confirm
  - Run: /delete-rib PaymentMethodRIB --confirm

Or re-parent children to different RIB first.

To override (DANGEROUS): --force
```

2. **Referenced in >5 non-test files:**
```
🛑 BLOCKED: RIB heavily used in codebase.

Found references in 8 files. Recommend refactoring first.

Files with references:
  1. CheckoutFlowInteractor.kt (line 45, 67, 89)
  2. PaymentValidator.kt (line 23)
  ...

Suggested approach:
  1. Refactor code to remove dependencies
  2. Run /delete-rib again when references < 5

To override (DANGEROUS): --force
```

3. **Modified in last 7 days:**
```
⚠️  WARNING: Recently modified (2 days ago)

Last commit: "Fix payment calculation in OrderSummary"
Author: john.doe

Recommend verifying with team before deletion.

To proceed: add --force flag
```

#### SOFT DELETE RECOMMENDATION:

```
💡 RECOMMENDATION: Consider soft-delete

This RIB has complex dependencies. Soft-delete will:
  ✓ Comment out routing in parent Router
  ✓ Keep files intact for reference
  ✓ Prevent accidental navigation
  ✓ Allow easy restoration

Run: /delete-rib OrderSummary --soft-delete --confirm
```

### PHASE 3: DELETION (only if --confirm provided)

If `--analyze-only` flag: STOP HERE and show analysis only.

If `--confirm` flag NOT provided:
```
❌ Deletion requires explicit confirmation.

To delete, run:
  /delete-rib {RibName} --confirm

To analyze only:
  /delete-rib {RibName} --analyze-only
```

#### SOFT DELETE (if --soft-delete)

1. **Find parent Router routing methods in APP module**

2. **Comment out methods in APP module Router:**
```kotlin
// SOFT DELETED: 2026-01-27
// Reason: No longer needed
// fun attachOrderSummary() {
//     if (orderSummaryChild == null) {
//         orderSummaryChild = orderSummaryBuilder.build()
//         orderSummaryChild?.onAttach()
//     }
// }
```

3. **Comment out builder dependency in APP module Router:**
```kotlin
class PaymentPlatformRouter @Inject constructor(
    private val interactor: PaymentPlatformInteractor,
    // SOFT DELETED: 2026-01-27
    // private val orderSummaryBuilder: OrderSummaryBuilder
) {
```

4. **Add marker comments to all three modules:**

**APP Module Interactor:**
```kotlin
// SOFT DELETED: 2026-01-27
// This RIB is no longer actively used but kept for reference
class OrderSummaryInteractor @Inject constructor(
```

**SHARED Module Interactor:**
```kotlin
// SOFT DELETED: 2026-01-27
// This RIB is no longer actively used but kept for reference
class OrderSummaryInteractor(
```

**UI Module ComposeBridge:**
```kotlin
// SOFT DELETED: 2026-01-27
// This RIB is no longer actively used but kept for reference
class OrderSummaryComposeBridge : KMPUpstreamBridge<OrderSummaryVM, OrderSummaryUIEvents>()
```

5. **Keep all RIB files intact in all three modules**

Output:
```
✅ Soft-delete completed

Routing disabled in parent Router:
  - PaymentPlatformRouter.attachOrderSummary() (commented out)

RIB files preserved for reference across all modules:
  - APP module: app/src/main/java/.../ribs/root/payment_platform/order_summary/
  - SHARED module: shared/src/commonMain/kotlin/.../shared/root/payment_platform/order_summary/
  - UI module: ui/src/main/java/.../ui/driverapp/root/payment_platform/order_summary/
  - All files marked with "SOFT DELETED: 2026-01-27" comments

To hard-delete later:
  /delete-rib OrderSummary --confirm

To restore:
  Uncomment routing code in PaymentPlatformRouter
```

#### HARD DELETE (default behavior)

1. **Create backup from all three modules:**
```bash
mkdir -p .claude/rib-trash/2026-01-27_14-30-00/{app,shared,ui}

# Backup APP module
cp -r app/src/main/java/com/theporter/android/driverapp/ribs/root/payment_platform/order_summary/ \
  .claude/rib-trash/2026-01-27_14-30-00/app/

# Backup SHARED module
cp -r shared/src/commonMain/kotlin/in/porter/driverapp/shared/root/payment_platform/order_summary/ \
  .claude/rib-trash/2026-01-27_14-30-00/shared/

# Backup UI module
cp -r ui/src/main/java/com/porter/ui/driverapp/root/payment_platform/order_summary/ \
  .claude/rib-trash/2026-01-27_14-30-00/ui/
```

2. **Update parent Router:**

Remove builder dependency:
```diff
  class PaymentPlatformRouter @Inject constructor(
      private val interactor: PaymentPlatformInteractor,
-     private val orderSummaryBuilder: OrderSummaryBuilder
  ) {
```

Remove routing methods:
```diff
- private var orderSummaryChild: OrderSummaryInteractor? = null
-
- fun attachOrderSummary() {
-     if (orderSummaryChild == null) {
-         orderSummaryChild = orderSummaryBuilder.build()
-         orderSummaryChild?.onAttach()
-     }
- }
-
- fun detachOrderSummary() {
-     orderSummaryChild?.onDetach()
-     orderSummaryChild = null
- }
```

3. **Update parent Component:**

Remove subcomponent:
```diff
  @Subcomponent(modules = [
-     OrderSummaryComponent::class,
      OtherComponent::class
  ])
```

4. **Delete RIB files from all three modules:**
```bash
# Delete APP module files
rm -rf app/src/main/java/com/theporter/android/driverapp/ribs/root/payment_platform/order_summary/

# Delete SHARED module files
rm -rf shared/src/commonMain/kotlin/in/porter/driverapp/shared/root/payment_platform/order_summary/

# Delete UI module files
rm -rf ui/src/main/java/com/porter/ui/driverapp/root/payment_platform/order_summary/
```

5. **Delete test files:**
```bash
# Find the exact path for the RIB's test directory
# Pattern: shared/src/test/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/
rm -f shared/src/test/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/{RibName}InteractorTestHelper.kt
rm -f shared/src/test/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/{RibName}InteractorStepDefs.kt

# Or delete the entire test directory for this RIB
rm -rf shared/src/test/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/
```

6. **Generate cleanup checklist:**
```
MANUAL CLEANUP REQUIRED
═══════════════════════

The following files reference the deleted RIB.
You must manually update them:

1. CheckoutFlowInteractor.kt
   Line 45: orderSummaryInteractor.calculate()
   Line 67: navigateToOrderSummary()
   → Remove or refactor these calls

2. PaymentValidator.kt
   Line 23: import ...OrderSummaryInteractor
   → Remove import

Use Grep tool to find remaining references:
  - Pattern: "OrderSummary"
  - Paths: app/src/main/java/, shared/src/, ui/src/

COMPILE WARNING: Code may not compile until manual cleanup is done.
```

### PHASE 4: OUTPUT & NEXT STEPS

```
✅ DELETED: {RibName}

Deleted APP module files (5):
  ✓ OrderSummaryBuilder.kt
  ✓ OrderSummaryInteractor.kt
  ✓ OrderSummaryRouter.kt
  ✓ OrderSummaryModule.kt
  ✓ OrderSummaryAlias.kt

Deleted SHARED module files (13):
  ✓ OrderSummaryBuilder.kt
  ✓ OrderSummaryInteractor.kt
  ✓ OrderSummaryRouter.kt
  ✓ dependency/OrderSummaryParams.kt
  ✓ dependency/OrderSummaryListener.kt (if existed)
  ✓ dependency/OrderSummaryDependency.kt (if existed)
  ✓ state/OrderSummaryState.kt
  ✓ state/OrderSummaryStateReducer.kt
  ✓ view/OrderSummaryPresenter.kt
  ✓ view/OrderSummaryVM.kt
  ✓ view/OrderSummaryVMMapper.kt
  ✓ analytics/OrderSummaryAnalytics.kt
  ✓ analytics/OrderSummaryEventIdentifiers.kt

Deleted UI module files (3):
  ✓ OrderSummaryComposeBridge.kt
  ✓ OrderSummaryComposeView.kt
  ✓ OrderSummaryVMFactory.kt

Deleted test files (2):
  ✓ OrderSummaryInteractorTestHelper.kt
  ✓ OrderSummaryInteractorStepDefs.kt

Updated files (2):
  ✓ PaymentPlatformRouter.kt (removed routing)
  ✓ PaymentPlatformComponent.kt (removed subcomponent)

Backup location:
  📁 .claude/rib-trash/2026-01-27_14-30-00/order_summary/
  (Retained for 30 days)

⚠️  MANUAL CLEANUP NEEDED:
  8 files still reference this RIB - see checklist above

Next steps:
  1. Fix compilation errors in referencing files
  2. Run tests: ./gradlew test
  3. Verify app builds: ./gradlew assembleStagingDebug
  4. Create PR with deletion

To restore (within 30 days):
  # Restore APP module
  cp -r .claude/rib-trash/2026-01-27_14-30-00/app/order_summary/ app/src/main/java/.../ribs/root/payment_platform/
  # Restore SHARED module
  cp -r .claude/rib-trash/2026-01-27_14-30-00/shared/order_summary/ shared/src/commonMain/kotlin/.../shared/root/payment_platform/
  # Restore UI module
  cp -r .claude/rib-trash/2026-01-27_14-30-00/ui/order_summary/ ui/src/main/java/.../ui/driverapp/root/payment_platform/
```

## SAFETY RULES

### BLOCKS (cannot proceed without --force):
- Child RIBs exist → must delete children first
- >5 non-test file references → must refactor first
- Modified in last 7 days → team verification needed

### WARNINGS (proceed with caution):
- 2-5 file references → show manual cleanup checklist
- No test files found → may indicate incomplete RIB

### CONFIRMATIONS REQUIRED:
1. First confirmation: `--confirm` flag
2. Second confirmation if `--force`: ask "Are you absolutely sure? (type 'DELETE' to confirm)"

### NEVER:
- Delete without `--confirm` flag
- Skip backup creation
- Auto-fix code references (only show checklist)
- Delete parent RIB
- Delete shared utilities referenced elsewhere
- Permanently delete (always move to trash)

## ERROR HANDLING

RIB not found:
```
❌ RIB '{RibName}' not found.

Run: /read-rib {RibName}
     to verify RIB exists
```

Force required:
```
❌ Deletion blocked due to safety checks.

Add --force to override (not recommended):
  /delete-rib {RibName} --confirm --force

This will bypass:
  - Child RIB existence check
  - Reference count check
  - Recent modification check

⚠️  WARNING: --force may break compilation
```

## RESTORATION PROCEDURE

If user wants to restore deleted RIB:
```
To restore deleted RIB from trash:

1. Find backup:
   ls -la .claude/rib-trash/

2. Copy back files from all three modules:
   # APP module
   cp -r .claude/rib-trash/{timestamp}/app/order_summary/ \
     app/src/main/java/com/theporter/android/driverapp/ribs/root/payment_platform/

   # SHARED module
   cp -r .claude/rib-trash/{timestamp}/shared/order_summary/ \
     shared/src/commonMain/kotlin/in/porter/driverapp/shared/root/payment_platform/

   # UI module
   cp -r .claude/rib-trash/{timestamp}/ui/order_summary/ \
     ui/src/main/java/com/porter/ui/driverapp/root/payment_platform/

3. Restore routing in parent:
   - Uncomment builder dependency
   - Uncomment routing methods
   - Add back to Component subcomponents

4. Verify:
   ./gradlew assembleStagingDebug
```
