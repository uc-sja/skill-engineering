# Convert SVG to Android XML Vector Drawable

You are converting SVG vector assets to Android XML Vector Drawable format for use in Compose Multiplatform.

## Task

Convert SVG files to Android Vector Drawable XML format and place them in the correct composeResources directory.

## Workflow

### Step 1: Identify the SVG Source

Ask the user for:
1. **SVG file location** - Path to the SVG file or URL
2. **Asset name** - Descriptive name for the asset (will be used as `ic_{asset_name}.xml`)
3. **Target module** - Which module to place the drawable in (shared, payments, profile, onboarding, booking, commons)

If extracting from Figma:
- User provides Figma node ID for the image/icon
- Call `mcp__figma-desktop__get_screenshot` to preview the asset
- Extract the SVG data from Figma design context

### Step 2: Conversion Strategy

Try these approaches in order:

#### Option A: Using svg2vectordrawable (Preferred)

```bash
# Check if svg2vectordrawable is installed
which svg2vectordrawable

# If not installed, provide instructions:
# npm install -g svg2vectordrawable

# Convert SVG to Android Vector Drawable
svg2vectordrawable input.svg -o ic_{asset_name}.xml
```

#### Option B: Using Android Studio (Manual - Provide Instructions)

If automatic conversion fails, provide these steps to the user:
```
⚠️ Manual SVG to XML conversion required:

1. Open Android Studio
2. Right-click on res/drawable folder
3. Select: New → Vector Asset
4. Choose: Local file (SVG, PSD)
5. Select your SVG file: {svg_path}
6. Preview the result
7. Click "Next" and "Finish"
8. Copy the generated XML from: app/src/main/res/drawable/{name}.xml
9. Paste to: {target_path}

OR use online converter:
https://svg2vector.com/
```

### Step 3: Validate XML Structure

After conversion, validate the XML has:
- ✅ Proper `<vector>` root element
- ✅ `xmlns:android` namespace
- ✅ `android:width` and `android:height` (in dp)
- ✅ `android:viewportWidth` and `android:viewportHeight`
- ✅ At least one `<path>` element
- ✅ Valid `android:pathData` (SVG path commands)
- ✅ `android:fillColor` or `android:strokeColor`

**Common Issues to Fix:**
```xml
❌ BAD:
<svg width="24" height="24">
  <path d="M12 2L2 7v10l10 5 10-5V7L12 2z" fill="#000"/>
</svg>

✅ GOOD:
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF000000"
        android:pathData="M12,2L2,7v10l10,5 10,-5V7L12,2z"/>
</vector>
```

### Step 4: Save to composeResources

**Target Location:**
```
{module}/src/commonMain/composeResources/drawable/ic_{asset_name}.xml
```

**Module Paths:**
- `shared/src/commonMain/composeResources/drawable/`
- `payments/src/commonMain/composeResources/drawable/`
- `profile/src/commonMain/composeResources/drawable/`
- `onboarding/src/commonMain/composeResources/drawable/`
- `booking/src/commonMain/composeResources/drawable/`
- `commons/src/commonMain/composeResources/drawable/`

**Naming Convention:**
- Prefix: `ic_` for icons
- Use snake_case: `ic_arrow_right.xml`, `ic_success_checkmark.xml`
- Be descriptive: `ic_location_pin_filled.xml` not `ic_icon1.xml`

**Create directory if needed:**
```bash
mkdir -p {module}/src/commonMain/composeResources/drawable
```

### Step 5: Generate Usage Code

After saving the XML, provide the Kotlin code to use it:

```kotlin
import org.jetbrains.compose.resources.painterResource
import {module}.shared.resources.Res // Import the generated resources
import androidx.compose.foundation.Image
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp

// Usage in Compose
Image(
    painter = painterResource(Res.drawable.ic_{asset_name}),
    contentDescription = "{description}",
    modifier = Modifier.size(24.dp) // Use Potion token if available
)

// Or with Icon component
Icon(
    painter = painterResource(Res.drawable.ic_{asset_name}),
    contentDescription = "{description}",
    tint = LocalColors.current.layerStyles* // Use Potion color token
)
```

**Required Imports:**
```kotlin
import org.jetbrains.compose.resources.painterResource
import {module}.shared.resources.Res
```

### Step 6: Verify Resource Generation

After saving the XML, rebuild the module to generate Res class:

```bash
# Build the specific module
./gradlew :{module}:compileDebugKotlinAndroid

# If resource not found, try clean build
./gradlew clean :{module}:compileDebugKotlinAndroid
```

### Step 7: Clean Up

If temporary SVG files were created:
```bash
rm temp_{asset_name}.svg
```

## Important Guidelines

### When to Use This Skill

**✅ DO convert to XML for:**
- Vector icons (arrows, checkmarks, symbols)
- Logo graphics
- Illustrations that are vector-based
- Custom icons not in Potion UI

**❌ DON'T convert to XML for:**
- Potion UI component icons (already in design system)
- Raster images (photos, screenshots) - use PNG instead
- Complex gradients (may not convert well)
- Icons already available in Material Icons

### Size Optimization

After conversion, optimize the XML:
- Remove unnecessary attributes (id, class, style)
- Simplify path data if possible
- Use relative path commands (lowercase) where appropriate
- Remove comments and whitespace

**Example optimization:**
```xml
❌ BEFORE (bloated):
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24.0"
    android:viewportHeight="24.0"
    android:tint="#000000">
    <group android:name="group">
        <path
            android:name="path_1"
            android:fillColor="#FF000000"
            android:pathData="M 12 2 L 2 7 L 2 17 L 12 22 L 22 17 L 22 7 Z"/>
    </group>
</vector>

✅ AFTER (optimized):
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="24dp"
    android:height="24dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
    <path
        android:fillColor="#FF000000"
        android:pathData="M12,2L2,7v10l10,5 10,-5V7L12,2z"/>
</vector>
```

## Checklist

Before completing, verify:
- [ ] SVG successfully converted to valid Android Vector XML
- [ ] XML saved to correct module's composeResources/drawable/
- [ ] File named with `ic_` prefix and snake_case
- [ ] XML validated (proper structure, no errors)
- [ ] Usage code provided with correct imports
- [ ] Module rebuilt to generate Res class
- [ ] Temp files cleaned up
- [ ] Potion UI color tokens used for tinting (if applicable)

## Example Flow

User provides:
```
SVG file: /path/to/arrow-right.svg
Asset name: arrow_right
Target module: shared
```

Your actions:
1. ✅ Read the SVG file
2. ✅ Convert using svg2vectordrawable or provide manual steps
3. ✅ Validate XML structure
4. ✅ Save to: `shared/src/commonMain/composeResources/drawable/ic_arrow_right.xml`
5. ✅ Provide usage code with imports
6. ✅ Run: `./gradlew :shared:compileDebugKotlinAndroid`
7. ✅ Clean up temp files
8. ✅ Confirm success

## Common Errors & Solutions

| Error | Solution |
|-------|----------|
| `pathData` syntax error | Check for spaces in coordinates, use commas |
| Resource not found after save | Rebuild module: `./gradlew :module:compileDebugKotlinAndroid` |
| Icon clipped | Check viewport dimensions match path bounds |
| Gradle sync fails | Ensure XML is in `composeResources/drawable/` not `res/drawable/` |

## Quick Reference

**SVG Path Commands:**
- `M/m` - Move to
- `L/l` - Line to
- `H/h` - Horizontal line
- `V/v` - Vertical line
- `C/c` - Cubic Bezier curve
- `Q/q` - Quadratic Bezier curve
- `A/a` - Arc
- `Z/z` - Close path

Uppercase = absolute, lowercase = relative
