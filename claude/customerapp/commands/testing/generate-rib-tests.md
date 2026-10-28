# Generate Test Suite for RIB

Generate a comprehensive UI-focused test suite in Gherkin format for a RIB component. **Focus on testing UI behavior and visibility conditions after view layer changes.**

## Instructions

1. **Analyze the RIB structure** at the provided path:
   - Read the Interactor, Presenter, Router, State, and Reducer files
   - Read the XML/Older UI file to understand all UI components
   - Identify all user interactions from the Presenter interface
   - Identify all state properties and their types
   - **Analyze VMMapper to understand UI visibility conditions**
   - Map state properties to UI components

2. **Generate comprehensive UI test scenarios** covering:

   ### UI Visibility & State Conditions ⭐ (PRIMARY FOCUS)
   - Component visibility based on state (if state.X then show/hide component Y)
   - Loading states (show spinner, hide content, disable buttons)
   - Error states (show error message, show retry button)
   - Empty states (show empty view, hide list)
   - Success states (show confirmation, hide form)
   - Button enabled/disabled states based on validation
   - Text field visibility and enabled states
   - Bottom sheet/dialog visibility triggers
   - Banner/alert visibility conditions
   - List item visibility based on data
   - Conditional sections (if premium then show feature X)

   ### User Interactions & UI Response
   - Button clicks → UI changes
   - Text input → validation messages visibility
   - Selection changes → dependent UI updates
   - Scroll → sticky header visibility, load more
   - Toggle switches → conditional UI visibility
   - Checkbox → form field visibility

   ### Navigation & Screen Transitions
   - Navigation flows (which screen appears after action)
   - Back button → previous screen visible
   - Dismiss → parent screen visible
   - Deep link → specific screen visible

   ### Form Validation & UI Feedback
   - Invalid input → error text visible
   - Valid input → error text hidden, submit enabled
   - Required fields → submit button disabled
   - All fields valid → submit button enabled

   ### Data Loading & UI States
   - Initial load → loading spinner visible
   - Data loaded → content visible, spinner hidden
   - Refresh → content visible + loading indicator
   - Load more → existing content visible + bottom loader

   ### Error Handling & UI
   - API error → error message visible, content hidden
   - Network error → offline banner visible
   - Validation error → inline error message visible
   - Empty result → empty state view visible

   ### Edge Cases & UI Behavior
   - Rapid clicks → button remains disabled until complete
   - Concurrent actions → correct loading state
   - State conflicts → correct UI priority

3. **Follow the AAA pattern** (Arrange-Act-Assert):
   - **Given** steps = Setup (mocks, test helpers, initial state)
   - **When/And** steps = Actions (user interactions, state changes)
   - **Then/And** steps = UI Assertions (component visibility, text content, enabled state)

4. **Output format**:
   - Feature file in Gherkin format
   - Background section for common setup
   - Scenarios organized by UI concern
   - **Focus on ViewModel assertions** (what the UI should render)
   - One UI assertion per Then step

5. **Provide**:
   - Complete Gherkin feature file
   - Test helper structure
   - Mock requirements
   - ViewModel assertion examples

## Example Format

```gherkin
Feature: [Feature Name] UI
  Test UI visibility and behavior for [Feature]

  Background:
    Given [Feature] screen is setup with [params]

  # UI Visibility - Loading States
  Scenario: Show loading spinner when data is being fetched
    Given data is loading
    When screen is visible
    Then loading spinner should be visible
    And content section should be hidden
    And submit button should be disabled

  # UI Visibility - Error States
  Scenario: Show error message when API fails
    Given API returns error "Network timeout"
    When screen loads data
    Then error message "Network timeout" should be visible
    And retry button should be visible
    And content section should be hidden

  # UI Visibility - Success States
  Scenario: Show content when data loads successfully
    Given API returns valid data
    When screen loads data
    Then content section should be visible
    And loading spinner should be hidden
    And submit button should be enabled

  # User Interaction → UI Change
  Scenario: Enable submit button when form is valid
    Given form fields are empty
    When user enters valid name "John"
    And user enters valid email "john@example.com"
    Then submit button should be enabled
    And error messages should be hidden

  Scenario: Show error message on invalid input
    Given form is empty
    When user enters invalid email "notanemail"
    Then error message "Invalid email format" should be visible
    And submit button should be disabled

  # Conditional UI Visibility
  Scenario: Show premium features section for premium users
    Given user is premium subscriber
    When screen is visible
    Then premium features section should be visible
    And upgrade banner should be hidden

  Scenario: Show upgrade banner for non-premium users
    Given user is not premium subscriber
    When screen is visible
    Then premium features section should be hidden
    And upgrade banner should be visible

  # Navigation & Screen Visibility
  Scenario: Navigate to details screen on item click
    When user taps on item "Order #123"
    Then order details screen should be visible
    And order ID "123" should be displayed

  Scenario: Return to previous screen on back button
    Given details screen is visible
    When user taps back button
    Then list screen should be visible
    And details screen should be dismissed
```

## Example Usage

```bash
/generate-test-suite /path/to/rib/directory
```

## Arguments

- **RIB Directory Path** (required): Absolute path to the RIB directory

## Critical Focus Areas

**Every test should verify UI visibility/behavior:**
- ✅ "submit button should be enabled"
- ✅ "error message should be visible"
- ✅ "loading spinner should be hidden"
- ✅ "content section should be visible"
- ❌ NOT: "analytics event should be tracked" (ignore analytics)

**Test the View Layer changes:**
- State changes → Which UI components appear/disappear?
- User actions → How does the UI respond?
- Data loading → What loading/error/success UI is shown?
- Validation → What error messages/states are shown?
