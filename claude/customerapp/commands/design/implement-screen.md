# Implement Screen from Figma

You are a specialized agent for implementing Compose screens from Figma designs using the Potion UI design system.

## Your Workflow

Follow these steps automatically:

### Step 1: Extract Design Information
1. Call `mcp__figma-desktop__get_screenshot` with the provided nodeId
2. Call `mcp__figma-desktop__get_variable_defs` with empty nodeId to get ALL tokens
3. Call `mcp__figma-desktop__get_design_context` with the provided nodeId

### Step 2: Create Token Mapping & Validate Coverage (BLOCKING)

Analyze Figma variables and create a complete mapping:
*   **Typography**: Map Figma text styles → `PotionTextStyles.layerStyles*`.
*   **Spacing**: Map pixels → `PotionDimensions.layerStylesSpacing*`.
*   **Padding**: Map pixels → `PotionDimensions.layerStylesPadding*`.
*   **Colors**: Map hex/names → `LocalColors.current.layerStyles*`.
*   **Sizing**: Map dimensions → `PotionDimensions.layerStylesSizing*` or `layerStylesIcon*`.
*   **Radius**: Map radius → `PotionDimensions.layerStylesRadius*` or `componentStyles*`.


**CRITICAL VALIDATION - NO HARDCODED VALUES ALLOWED**:

**Validate Coverage**:
*   If ANY value (color `#EF4444`, size `13px`) cannot be mapped to a Potion token → **STOP**.
*   Report the unmapped values to the user:
```
⚠️ UNMAPPED VALUES FOUND - BLOCKING IMPLEMENTATION:
- Spacing: 12dp (no matching token in PotionDimensions)
- Color: #FF5733 (no matching token in LocalColors)
- Font size: 13sp (no matching token in PotionTextStyles)
```
*   User must explicitly choose:
1. Contact design team to add missing tokens to Potion UI
2. Approve a specific token substitution (e.g., "use `layerStylesSpacing300` instead of 12dp")


**Only proceed to Step 3 when ALL values have confirmed token mappings or explicit user approval.**

### Step 3: Component Verification
Verify ALL design elements can be built with Potion UI:
- TextField.Default.Compact/Large/Medium
- Button.Primary/Secondary/Tertiary.Default*
- Chip.Small
- Checkbox.Small/Large
- StickyCta.Default
- Text, Card, etc.

**CRITICAL**: If ANY element cannot be built with Potion UI:
- STOP implementation
- Report missing components to user
- Ask if they want to report to design team or proceed with approval

### Step 4: Image Assets (SVG → XML CONVERSION)

If design contains images, extract and convert them:

1. **Identify Image Nodes**: From design context, find all image/icon nodes (type="IMAGE" or icon references)
   - Skip Potion UI component icons (already in the design system)
   - Only extract custom icons/illustrations not in design system

2. **For Each Image Asset**:
   1. **Download SVG from Figma**:
      - Call `mcp__figma-desktop__get_image` with the specific image node ID
      - Save temporarily as `temp_{asset_name}.svg`

   2. **Convert and Save**:
      - **Use `/convert-svg-to-xml` slash command** with:
        - SVG file: `temp_{asset_name}.svg`
        - Asset name: `{descriptive_name}` (e.g., `success_illustration`)
        - Target module: Extract from target path (e.g., `payments`, `shared`, `booking`)
      - The command handles: conversion, validation, saving to composeResources, and module rebuild

   3. **Generate code** using proper resource reference:
      ```kotlin
      // Auto-extracted from Figma and converted to Vector Drawable
      // Node ID: {node_id}
      // Asset: ic_{asset_name}.xml
      Image(
          painter = painterResource(Res.drawable.ic_{asset_name}),
          contentDescription = "{description from Figma}",
          modifier = Modifier.size({width}.dp, {height}.dp)
      )
      ```
      - Add required import: `import {module}.shared.resources.Res`

**Important Notes**:
- Format: SVG → Android Vector Drawable XML (NOT PNG)
- For raster images (photos), use PNG format instead
- All conversion details handled by `/convert-svg-to-xml` command

### Step 5: Implement Screen
Generate Kotlin Compose code using:
- **ONLY** Potion UI components
- **ONLY** design system tokens
- Use extracted resources: `painterResource(Res.drawable.ic_your_asset)`
- Add comments documenting Figma token mappings and asset sources

### Step 6: Add Test Tags for UI Testing

**CRITICAL**: Every screen MUST include test tags for UI automation testing.

1. **Create a TestTags object** at the top of the file (after imports):
   ```kotlin
   object {ScreenName}TestTags {
       const val SCREEN_ROOT = "{screen_name}_root"
       const val {ELEMENT_NAME} = "{element_name}"
       // Add a constant for each interactive/important element
   }
   ```

2. **Naming Convention for Test Tags**:
   - Use `snake_case` for tag values
   - Use `SCREAMING_SNAKE_CASE` for constant names
   - Prefix with screen/component name for uniqueness
   - Examples:
     - `const val PICKUP_CARD = "pickup_card"`
     - `const val SUBMIT_BUTTON = "submit_button"`
     - `const val ADDRESS_INPUT = "address_input"`

3. **Apply test tags using `testResourceId` modifier**:
   ```kotlin
   import `in`.porter.potionui.utils.testResourceId

   Box(
       modifier = Modifier
           .testResourceId({ScreenName}TestTags.ELEMENT_NAME)
           // ... other modifiers
   )
   ```

4. **Elements that MUST have test tags**:
   - Root container of the screen/component
   - All clickable elements (buttons, cards, list items)
   - All input fields (text fields, checkboxes, toggles)
   - Important icons that convey state
   - Text elements that display dynamic data
   - Navigation elements (back buttons, tabs)

5. **Example Implementation**:
   ```kotlin
   object PaymentScreenTestTags {
       const val SCREEN_ROOT = "payment_screen_root"
       const val BALANCE_TEXT = "balance_text"
       const val ADD_MONEY_BUTTON = "add_money_button"
       const val CREDIT_CARD_ICON = "credit_card_icon"
   }

   @Composable
   fun PaymentScreen() {
       Column(
           modifier = Modifier
               .testResourceId(PaymentScreenTestTags.SCREEN_ROOT)
               .fillMaxSize()
       ) {
           Text(
               modifier = Modifier.testResourceId(PaymentScreenTestTags.BALANCE_TEXT),
               text = balance
           )
           Button.Primary.DefaultMedium(
               modifier = Modifier.testResourceId(PaymentScreenTestTags.ADD_MONEY_BUTTON),
               title = "Add Money",
               onClick = { }
           )
       }
   }
   ```

### Step 7: Automatic Review & Fix
After generating code:

1. **Read the generated file** to verify it was created
2. **Run compilation check**:
   - Extract module name from target path (e.g., `payments`, `shared`, `onboarding`)
   - Run: `./gradlew :{module}:compileDebugKotlinAndroid 2>&1 | grep -E "(error:|\.kt:)" | head -50`
3. **Fix compilation errors** automatically:
   - Check token names (e.g., `layerStylesSizingIcon500` → `layerStylesIcon500`)
   - Check component names (e.g., `Button.Tertiary.Medium` → `Button.Tertiary.DefaultMedium`)
   - Check parameter names (e.g., `optionalText` → `isOptional`)
   - Fix nested object references (e.g., `StickyCtaButtonStack` → `StickyCta.StickyCtaButtonStack`)
   - Check resource references (e.g., ensure Res.drawable imports exist)
   - Remove unused imports
4. **Re-run compilation** to verify fixes
5. **Repeat** until compilation succeeds or max 3 attempts

### Step 8: Generate Summary
Create a summary report:
```markdown
## ✅ Implementation Complete: [Screen Name]

### Token Mapping
- Typography: [list mapped tokens]
- Spacing: [list mapped tokens]
- Colors: [list mapped tokens]
- ⚠️ Mismatches: [list any tokens that had to be substituted]

### Components Used
- [List all Potion UI components]

### Test Tags Added
- [List all test tags with their purposes]
- Example: `PICKUP_CARD` - Main card container
- Example: `SUBMIT_BUTTON` - Submit action button

### Image Assets
- [List each asset extracted with name, size, and status]
- [Example: ✅ ic_{asset_name}.xml ({width}x{height}) → Converted via /convert-svg-to-xml]
- [Or: ✅ No custom image assets found (Potion UI icons used)]

### Compilation Status
- ✅ Compiles successfully
- OR ❌ [List remaining errors]

### File Locations
- Screen: [Full path to generated .kt file]
- Assets: [List paths to extracted drawables]

### Design System Compliance
- ✅ Zero hardcoded values
- ✅ Only Potion UI components
- ✅ Only design tokens
- ✅ Image assets converted via /convert-svg-to-xml (if applicable)
- ✅ Test tags added for UI testing
- ✅ Preview function created
```

## Input Format
When invoked, expect:
```
Figma URL: [url with node-id]
Target path: [absolute path to .kt file]
```

## Critical Rules
- ❌ NO custom composables without explicit user approval
- ❌ NO hardcoded dp values
- ❌ NO hardcoded colors
- ❌ NO raw TextStyle constructors
- ❌ NO screens without test tags
- ✅ ONLY Potion UI components
- ✅ ONLY design system tokens
- ✅ Use /convert-svg-to-xml for image asset conversion
- ✅ Always add test tags using `testResourceId` modifier
- ✅ Always run compilation check
- ✅ Auto-fix common errors

## Error Handling
If you encounter:
- **Design gaps**: Report to user, suggest contacting design team
- **Image asset conversion fails**: Escalate to user, /convert-svg-to-xml will handle error reporting
- **Compilation errors after 3 fix attempts**: Report to user with details
- **Figma MCP not connected**: Instruct user to start Figma Desktop app

## Example Invocation
```
Figma URL: https://www.figma.com/design/FILE_ID/FILE_NAME?node-id=1500-22432
Target path: {project_root}/payments/src/commonMain/kotlin/in/porter/customerapp/payments/main/OnboardingScreen.kt
```

Now implement the screen following all steps above automatically.
