---
name: create-rib
description: Create a new RIB module with Jetpack Compose following the three-module architecture (shared, ui, app)
---

You are creating a new RIB (Router, Interactor, Builder) module following DriverAppV3 architectural conventions with Jetpack Compose.

## ARCHITECTURAL OVERVIEW

DriverAppV3 uses a **three-module architecture** for RIBs with Jetpack Compose:

### **SHARED Module** - Platform-agnostic business logic (KMP)
- Location: `shared/src/commonMain/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/`
- Contains: Builder, Interactor, Router, Analytics, Dependency interfaces, State management, View contracts (Presenter, VM, VMMapper)

### **UI Module** - Jetpack Compose UI components (Android-specific)
- Location: `ui/src/main/java/com/porter/ui/driverapp/root/{parent_path}/{ribname}/`
- Contains: ComposeBridge, ComposeView, VMFactory, UI components

### **APP Module** - Android RIB orchestration (Dagger + RIBs framework)
- Location: `app/src/main/java/com/theporter/android/driverapp/ribs/root/{parent_path}/{ribname}/`
- Contains: Builder, Interactor, Router, Module, TypeAlias

## INPUTS REQUIRED

Ask the user for:
1. **RIB Name** (PascalCase, e.g., "OrderSummary", "ContactDetails") - REQUIRED
2. **Parent Path** (e.g., "loggedin/home/contactselection", "paymentplatform", "root") - REQUIRED
3. **UI Type** (page/bottomsheet/dialog, default: page) - OPTIONAL
4. **Parent Communication** - Ask: "Does this RIB need to communicate with its parent?" (yes/no) - REQUIRED

## VALIDATION STEPS

Before creating files, you MUST:

1. **Validate RIB Name:**
    - Must be PascalCase
    - Must NOT end with "RIB" suffix
    - Must NOT conflict with existing RIB names

2. **Validate Parent Path:**
    - Verify parent path exists in app module: `app/src/main/java/com/theporter/android/driverapp/ribs/root/{parent_path}/`
    - Verify parent has Component definition for subcomponent linkage

3. **Check for Conflicts:**
    - Search for existing RIB with same name across all three modules
    - Check Dagger scope `@{RibName}Scope` doesn't conflict

4. **Directory Structure:**
    Create directories in all three modules:
    - **Shared**: `shared/src/commonMain/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/`
      - ALWAYS create subdirectories: `dependency/`, `state/`, `view/`, `analytics/`
    - **UI**: `ui/src/main/java/com/porter/ui/driverapp/root/{parent_path}/{ribname}/`
    - **App**: `app/src/main/java/com/theporter/android/driverapp/ribs/root/{parent_path}/{ribname}/`
    - **Tests**: `shared/src/test/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/`

## FILES TO GENERATE

For a RIB named `{RibName}`:

---

## SHARED MODULE FILES

Package: `in.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}`

### 1. Dependency Files

**`dependency/{RibName}Params.kt`** (ALWAYS CREATED)
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency

data class {RibName}Params(
  val userId: String = "user_123",
  val featureFlag: Boolean = true,
  val configValue: String = "default",
)
```

**`dependency/{RibName}Listener.kt`** (CREATED ONLY IF USER ANSWERED YES TO "Does this RIB need to communicate with its parent?")
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency

interface {RibName}Listener {
  fun on{RibName}Completed(result: String)
  fun on{RibName}Cancelled()
  fun on{RibName}Error(error: String)
}
```

**`dependency/{RibName}Dependency.kt`** (CREATED ONLY IF LISTENER EXISTS - wraps Params + Listener)
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency

data class {RibName}Dependency(
  val params: {RibName}Params,
  val listener: {RibName}Listener,
)
```

**IMPORTANT:** If Listener is NOT needed, pass only `{RibName}Params` directly to Builder (no Dependency wrapper).

### 2. State Management Files

**`state/{RibName}State.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state

data class {RibName}State(
  val isLoading: Boolean = false,
  val data: String = "",
  val errorMessage: String? = null,
  val counter: Int = 0,
)
```

**`state/{RibName}StateReducer.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state

import `in`.porter.kmputils.flux.base.StateReducer
import kotlinx.coroutines.CoroutineDispatcher

class {RibName}StateReducer(
  stateDispatcher: CoroutineDispatcher,
) : StateReducer<{RibName}State>(stateDispatcher) {

  override val initState: {RibName}State = {RibName}State()

  suspend fun setLoading(isLoading: Boolean) = updateState { state ->
    state.copy(isLoading = isLoading)
  }

  suspend fun updateData(data: String) = updateState { state ->
    state.copy(data = data, isLoading = false, errorMessage = null)
  }

  suspend fun setError(error: String) = updateState { state ->
    state.copy(errorMessage = error, isLoading = false)
  }

  suspend fun incrementCounter() = updateState { state ->
    state.copy(counter = state.counter + 1)
  }
}
```

### 3. View Layer Files

**`view/{RibName}Presenter.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view

import `in`.porter.kmputils.commons.ui.ClicksFlow
import `in`.porter.kmputils.flux.base.BasePresenter
import kotlinx.coroutines.flow.Flow

interface {RibName}Presenter : BasePresenter<{RibName}VM> {
  suspend fun onBackPressed(): ClicksFlow
  suspend fun onSubmitClicked(): ClicksFlow
  suspend fun onCancelClicked(): ClicksFlow
}
```

**`view/{RibName}VM.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view

import `in`.porter.kmputils.flux.base.BaseVM

data class {RibName}VM(
  val isLoading: Boolean = false,
  val displayText: String = "",
  val showError: Boolean = false,
  val errorMessage: String = "",
  val buttonEnabled: Boolean = true,
) : BaseVM
```

**`view/{RibName}VMMapper.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Params
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}State
import `in`.porter.kmputils.flux.base.BaseVMMapper

class {RibName}VMMapper : BaseVMMapper<{RibName}Params, {RibName}State, {RibName}VM>() {
  override fun map(params: {RibName}Params, state: {RibName}State): {RibName}VM {
    return {RibName}VM(
      isLoading = state.isLoading,
      displayText = state.data.ifEmpty { "No data available" },
      showError = state.errorMessage != null,
      errorMessage = state.errorMessage ?: "",
      buttonEnabled = !state.isLoading,
    )
  }
}
```

### 4. Analytics Files (MANDATORY)

**`analytics/{RibName}Analytics.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.analytics

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Params

interface {RibName}Analytics {
  suspend fun recordActive(params: {RibName}Params)
  fun recordBackTap()
  fun recordSubmitTap()
  fun recordCancelTap()
}
```

**`analytics/{RibName}EventIdentifiers.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.analytics

object {RibName}EventIdentifiers {
  const val SCREEN_VIEWED = "{ribname}_screen_viewed"
  const val BACK_TAPPED = "{ribname}_back_tapped"
  const val SUBMIT_TAPPED = "{ribname}_submit_tapped"
  const val CANCEL_TAPPED = "{ribname}_cancel_tapped"
}
```

### 5. Core Shared Files

**`{RibName}Builder.kt`**

**Version A - WITH Listener (if user answered YES to parent communication):**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Dependency
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}StateReducer
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VMMapper
import `in`.porter.kmputils.commons.localization.Locale
import `in`.porter.kmputils.flux.base.interactor.InteractorDispatchersFactory
import `in`.porter.kmputils.flux.base.interactorv2.InteractorCoroutineExceptionHandler
import kotlinx.coroutines.flow.Flow

class {RibName}Builder {

  fun build(
    coroutineExceptionHandler: InteractorCoroutineExceptionHandler,
    localeStream: Flow<Locale>,
    presenter: {RibName}Presenter,
    dependency: {RibName}Dependency,
  ): {RibName}Interactor {
    val dispatchers = InteractorDispatchersFactory.createStateVMInteractorDispatcher()

    return {RibName}Interactor(
      dispatchers = dispatchers,
      coroutineExceptionHandler = coroutineExceptionHandler,
      localeStream = localeStream,
      reducer = {RibName}StateReducer(dispatchers.stateDispatcher),
      vmMapper = {RibName}VMMapper(),
      presenter = presenter,
      params = dependency.params,
      listener = dependency.listener,
    )
  }
}
```

**Version B - WITHOUT Listener (if user answered NO to parent communication):**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Params
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}StateReducer
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VMMapper
import `in`.porter.kmputils.commons.localization.Locale
import `in`.porter.kmputils.flux.base.interactor.InteractorDispatchersFactory
import `in`.porter.kmputils.flux.base.interactorv2.InteractorCoroutineExceptionHandler
import kotlinx.coroutines.flow.Flow

class {RibName}Builder {

  fun build(
    coroutineExceptionHandler: InteractorCoroutineExceptionHandler,
    localeStream: Flow<Locale>,
    presenter: {RibName}Presenter,
    params: {RibName}Params,
  ): {RibName}Interactor {
    val dispatchers = InteractorDispatchersFactory.createStateVMInteractorDispatcher()

    return {RibName}Interactor(
      dispatchers = dispatchers,
      coroutineExceptionHandler = coroutineExceptionHandler,
      localeStream = localeStream,
      reducer = {RibName}StateReducer(dispatchers.stateDispatcher),
      vmMapper = {RibName}VMMapper(),
      presenter = presenter,
      params = params,
    )
  }
}
```

**`{RibName}Interactor.kt`**

**Version A - WITH Listener:**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Listener
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Params
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}State
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}StateReducer
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VM
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VMMapper
import `in`.porter.kmputils.commons.localization.Locale
import `in`.porter.kmputils.flux.base.interactor.StateVMInteractorDispatchers
import `in`.porter.kmputils.flux.base.interactorv2.BaseStateVMInteractor
import `in`.porter.kmputils.flux.base.interactorv2.InteractorCoroutineExceptionHandler
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.launch

class {RibName}Interactor(
  dispatchers: StateVMInteractorDispatchers,
  coroutineExceptionHandler: InteractorCoroutineExceptionHandler,
  localeStream: Flow<Locale>,
  private val reducer: {RibName}StateReducer,
  vmMapper: {RibName}VMMapper,
  private val presenter: {RibName}Presenter,
  private val params: {RibName}Params,
  private val listener: {RibName}Listener,
) : BaseStateVMInteractor<{RibName}Params, {RibName}State, {RibName}VM>(
  dispatchers,
  coroutineExceptionHandler,
  reducer,
  vmMapper,
  localeStream,
  presenter,
  params,
) {

  lateinit var router: {RibName}Router

  override suspend fun onActive() {
    super.onActive()
    loadInitialData()
    observeUIEvents()
  }

  private suspend fun loadInitialData() {
    reducer.setLoading(true)
    reducer.updateData("{RibName} initialized")
  }

  private fun observeUIEvents() {
    launch {
      presenter.onSubmitClicked().collect {
        handleSubmit()
      }
    }

    launch {
      presenter.onCancelClicked().collect {
        handleCancel()
      }
    }

    launch {
      presenter.onBackPressed().collect {
        handleCancel()
      }
    }
  }

  private suspend fun handleSubmit() {
    reducer.setLoading(true)
    try {
      val result = "Completed successfully"
      reducer.updateData(result)
      listener.on{RibName}Completed(result)
    } catch (e: Exception) {
      val error = e.message ?: "Unknown error"
      reducer.setError(error)
      listener.on{RibName}Error(error)
    }
  }

  private fun handleCancel() {
    listener.on{RibName}Cancelled()
  }
}
```

**Version B - WITHOUT Listener:**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Params
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}State
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}StateReducer
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VM
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VMMapper
import `in`.porter.kmputils.commons.localization.Locale
import `in`.porter.kmputils.flux.base.interactor.StateVMInteractorDispatchers
import `in`.porter.kmputils.flux.base.interactorv2.BaseStateVMInteractor
import `in`.porter.kmputils.flux.base.interactorv2.InteractorCoroutineExceptionHandler
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.launch

class {RibName}Interactor(
  dispatchers: StateVMInteractorDispatchers,
  coroutineExceptionHandler: InteractorCoroutineExceptionHandler,
  localeStream: Flow<Locale>,
  private val reducer: {RibName}StateReducer,
  vmMapper: {RibName}VMMapper,
  private val presenter: {RibName}Presenter,
  private val params: {RibName}Params,
) : BaseStateVMInteractor<{RibName}Params, {RibName}State, {RibName}VM>(
  dispatchers,
  coroutineExceptionHandler,
  reducer,
  vmMapper,
  localeStream,
  presenter,
  params,
) {

  lateinit var router: {RibName}Router

  override suspend fun onActive() {
    super.onActive()
    loadInitialData()
    observeUIEvents()
  }

  private suspend fun loadInitialData() {
    reducer.setLoading(true)
    reducer.updateData("{RibName} initialized")
  }

  private fun observeUIEvents() {
    launch {
      presenter.onSubmitClicked().collect {
        handleSubmit()
      }
    }

    launch {
      presenter.onCancelClicked().collect {
        handleCancel()
      }
    }

    launch {
      presenter.onBackPressed().collect {
        handleCancel()
      }
    }
  }

  private suspend fun handleSubmit() {
    reducer.setLoading(true)
    try {
      val result = "Completed successfully"
      reducer.updateData(result)
      // No listener - handle result internally
    } catch (e: Exception) {
      val error = e.message ?: "Unknown error"
      reducer.setError(error)
    }
  }

  private fun handleCancel() {
    // No listener - handle cancel internally
  }
}
```

**`{RibName}Router.kt`**
```kotlin
package `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}

class {RibName}Router {

  private var currentChildRouter: Any? = null

  suspend fun attachChild(childRouter: Any) {
    detachCurrentChild()
    currentChildRouter = childRouter
  }

  suspend fun detachCurrentChild() {
    currentChildRouter = null
  }

  fun hasAttachedChild(): Boolean = currentChildRouter != null
}
```

---

## UI MODULE FILES

Package: `com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}`

### 1. ComposeBridge

**`{RibName}ComposeBridge.kt`**
```kotlin
package com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}

import com.porter.ui.KMPUpstreamBridge
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VM
import `in`.porter.kmputils.commons.ui.ClicksFlow
import kotlinx.coroutines.flow.filterIsInstance
import kotlinx.coroutines.flow.map

sealed class {RibName}UIEvents {
  object BackButtonClicks : {RibName}UIEvents()
  object SubmitButtonClicks : {RibName}UIEvents()
  object CancelButtonClicks : {RibName}UIEvents()
}

class {RibName}ComposeBridge : KMPUpstreamBridge<{RibName}VM, {RibName}UIEvents>(), {RibName}Presenter {
  override suspend fun onBackPressed(): ClicksFlow =
    events.filterIsInstance<{RibName}UIEvents.BackButtonClicks>().map { }

  override suspend fun onSubmitClicked(): ClicksFlow =
    events.filterIsInstance<{RibName}UIEvents.SubmitButtonClicks>().map { }

  override suspend fun onCancelClicked(): ClicksFlow =
    events.filterIsInstance<{RibName}UIEvents.CancelButtonClicks>().map { }
}
```

### 2. ComposeView

**`{RibName}ComposeView.kt`**
```kotlin
package com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.porter.ui.UIEventsHandler
import com.porter.ui.UIEventsHandlerAsUnifiedFlow
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VM

@Composable
fun {RibName}ComposeView(
  vm: {RibName}VM,
  uiEventsHandler: UIEventsHandler<{RibName}UIEvents>,
  modifier: Modifier,
) {
  Column(
    modifier = modifier
      .fillMaxSize()
      .padding(16.dp),
    verticalArrangement = Arrangement.spacedBy(16.dp),
  ) {
    Text(
      text = "{RibName} Screen",
      style = MaterialTheme.typography.headlineMedium,
    )

    Text(text = vm.displayText)

    if (vm.showError) {
      Text(
        text = "Error: ${vm.errorMessage}",
        color = Color.Red,
      )
    }

    if (vm.isLoading) {
      CircularProgressIndicator(
        modifier = Modifier.align(Alignment.CenterHorizontally),
      )
    }

    Spacer(modifier = Modifier.weight(1f))

    Row(
      modifier = Modifier.fillMaxWidth(),
      horizontalArrangement = Arrangement.spacedBy(8.dp),
    ) {
      OutlinedButton(
        onClick = { uiEventsHandler.send({RibName}UIEvents.CancelButtonClicks) },
        modifier = Modifier.weight(1f),
        enabled = vm.buttonEnabled,
      ) {
        Text("Cancel")
      }
      Button(
        onClick = { uiEventsHandler.send({RibName}UIEvents.SubmitButtonClicks) },
        modifier = Modifier.weight(1f),
        enabled = vm.buttonEnabled,
      ) {
        Text("Submit")
      }
    }
  }
}

@Composable
@Preview
fun Preview{RibName}ComposeView() {
  {RibName}ComposeView(
    vm = {RibName}VMFactory.get{RibName}VM(),
    uiEventsHandler = UIEventsHandlerAsUnifiedFlow(),
    modifier = Modifier,
  )
}
```

### 3. VMFactory

**`{RibName}VMFactory.kt`**
```kotlin
package com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VM

object {RibName}VMFactory {
  fun get{RibName}VM() = {RibName}VM(
    isLoading = false,
    displayText = "Sample data for preview",
    showError = false,
    errorMessage = "",
    buttonEnabled = true,
  )
}
```

---

## APP MODULE FILES

Package: `com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}`

### 1. TypeAlias

**`{RibName}Alias.kt`**
```kotlin
package com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.{RibName}Builder
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.{RibName}Interactor
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.{RibName}Router

typealias {RibName}InteractorMP = {RibName}Interactor
typealias {RibName}BuilderMP = {RibName}Builder
typealias {RibName}RouterMP = {RibName}Router
```

### 2. Builder

**`{RibName}Builder.kt`**
```kotlin
package com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}

import android.view.LayoutInflater
import android.view.ViewGroup
import com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}.{RibName}ComposeBridge
import com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}.{RibName}ComposeView
import com.theporter.android.driverapp.R
import com.theporter.android.driverapp.ribs.base.BaseRibComponent
import com.theporter.android.driverapp.ui.base.ComposeFrameLayoutContainer
import com.uber.rib.core.InteractorBaseComponent
import com.uber.rib.core.ViewBuilder
import dagger.BindsInstance
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Dependency
import javax.inject.Scope

class {RibName}Builder(dependency: ParentComponent) :
  ViewBuilder<ComposeFrameLayoutContainer, {RibName}Router, {RibName}Builder.ParentComponent>(
    dependency,
  ) {

  // WITH Listener: fun build(parentViewGroup: ViewGroup, sharedDependency: {RibName}Dependency): {RibName}Router
  // WITHOUT Listener: fun build(parentViewGroup: ViewGroup, params: {RibName}Params): {RibName}Router
  fun build(parentViewGroup: ViewGroup, sharedDependency: {RibName}Dependency): {RibName}Router {
    val view = createView(parentViewGroup)
    val composeBridge = {RibName}ComposeBridge()

    val component = Dagger{RibName}Builder_Component.builder()
      .parentComponent(dependency)
      .view(view)
      .composeUpstreamBridge(composeBridge)
      .sharedDependency(sharedDependency)
      .build()

    val uiStateFlow = component.interactorMP().vmStream
    view.initialize(uiStateFlow, composeBridge.uiEventsHandler) { vm, uiEventsHandler, modifier ->
      {RibName}ComposeView(vm, uiEventsHandler, modifier)
    }

    component.interactorMP().router = component.router()
    return component.router()
  }

  override fun inflateView(inflater: LayoutInflater, parentViewGroup: ViewGroup) =
    inflater.inflate(
      R.layout.rib_compose_scroll_layout_container,
      parentViewGroup,
      false,
    ) as ComposeFrameLayoutContainer

  interface ParentComponent : BaseRibComponent {
    // Define dependencies from parent here
  }

  @{RibName}Scope
  @dagger.Component(
    modules = [{RibName}Module::class],
    dependencies = [ParentComponent::class],
  )
  interface Component :
    InteractorBaseComponent<{RibName}Interactor>,
    BuilderComponent {

    @dagger.Component.Builder
    interface Builder {
      @BindsInstance
      fun sharedDependency(sharedDependency: {RibName}Dependency): Builder

      @BindsInstance
      fun view(view: ComposeFrameLayoutContainer): Builder

      @BindsInstance
      fun composeUpstreamBridge(composeBridge: {RibName}ComposeBridge): Builder

      fun parentComponent(component: ParentComponent): Builder

      fun build(): Component
    }
  }

  interface BuilderComponent {
    fun router(): {RibName}Router
    fun interactorMP(): {RibName}InteractorMP
  }

  @Scope
  @Retention(AnnotationRetention.BINARY)
  internal annotation class {RibName}Scope
}
```

### 3. Interactor

**`{RibName}Interactor.kt`**
```kotlin
package com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}

import com.theporter.android.driverapp.ribs.base.AndroidRibInteractor
import com.uber.rib.core.Bundle
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter
import javax.inject.Inject

@{RibName}Builder.{RibName}Scope
class {RibName}Interactor @Inject constructor(
  interactorMP: {RibName}InteractorMP,
) : AndroidRibInteractor<{RibName}InteractorMP, {RibName}Presenter, {RibName}Router>(interactorMP) {

  override fun didBecomeActive(savedInstanceState: Bundle?) {
    super.didBecomeActive(savedInstanceState)
  }

  override fun handleBackPress(): Boolean {
    // Handle back press
    return false
  }
}
```

### 4. Router

**`{RibName}Router.kt`**
```kotlin
package com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}

import com.theporter.android.driverapp.ribs.root.BaseViewRouterV2
import com.theporter.android.driverapp.ui.base.ComposeFrameLayoutContainer
import kotlinx.coroutines.Dispatchers
import javax.inject.Inject

@{RibName}Builder.{RibName}Scope
class {RibName}Router @Inject constructor(
  view: ComposeFrameLayoutContainer,
  interactor: {RibName}Interactor,
  component: {RibName}Builder.Component,
) : BaseViewRouterV2<ComposeFrameLayoutContainer, {RibName}Interactor, {RibName}Builder.Component>(
  view,
  interactor,
  component,
  Dispatchers.Main,
),
  {RibName}RouterMP {

  // Android-specific router logic for child RIBs
}
```

### 5. Module

**`{RibName}Module.kt`**

**Version A - WITH Listener:**
```kotlin
package com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}

import com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}.{RibName}ComposeBridge
import com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}.{RibName}Builder.{RibName}Scope
import com.theporter.android.driverapp.ui.base.ComposeFrameLayoutContainer
import dagger.Binds
import dagger.Module
import dagger.Provides
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Dependency
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter

@Module
abstract class {RibName}Module {

  @{RibName}Scope
  @Binds
  internal abstract fun presenter(composeBridge: {RibName}ComposeBridge): {RibName}Presenter

  @Module
  companion object {

    @{RibName}Scope
    @Provides
    @JvmStatic
    fun router(
      component: {RibName}Builder.Component,
      view: ComposeFrameLayoutContainer,
      interactor: {RibName}Interactor,
    ) = {RibName}Router(
      view,
      interactor,
      component,
    )

    @{RibName}Scope
    @Provides
    @JvmStatic
    fun provide{RibName}InteractorMP(
      parentComponent: {RibName}Builder.ParentComponent,
      presenter: {RibName}Presenter,
      dependency: {RibName}Dependency,
    ): {RibName}InteractorMP {
      return {RibName}BuilderMP()
        .build(
          coroutineExceptionHandler = parentComponent.interactorCoroutineExceptionHandler(),
          localeStream = parentComponent.appLanguageRepository().provideLocaleStream(),
          presenter = presenter,
          dependency = dependency,
        )
    }
  }
}
```

**Version B - WITHOUT Listener:**
```kotlin
package com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}

import com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}.{RibName}ComposeBridge
import com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}.{RibName}Builder.{RibName}Scope
import com.theporter.android.driverapp.ui.base.ComposeFrameLayoutContainer
import dagger.Binds
import dagger.Module
import dagger.Provides
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Params
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter

@Module
abstract class {RibName}Module {

  @{RibName}Scope
  @Binds
  internal abstract fun presenter(composeBridge: {RibName}ComposeBridge): {RibName}Presenter

  @Module
  companion object {

    @{RibName}Scope
    @Provides
    @JvmStatic
    fun router(
      component: {RibName}Builder.Component,
      view: ComposeFrameLayoutContainer,
      interactor: {RibName}Interactor,
    ) = {RibName}Router(
      view,
      interactor,
      component,
    )

    @{RibName}Scope
    @Provides
    @JvmStatic
    fun provide{RibName}InteractorMP(
      parentComponent: {RibName}Builder.ParentComponent,
      presenter: {RibName}Presenter,
      params: {RibName}Params,
    ): {RibName}InteractorMP {
      return {RibName}BuilderMP()
        .build(
          coroutineExceptionHandler = parentComponent.interactorCoroutineExceptionHandler(),
          localeStream = parentComponent.appLanguageRepository().provideLocaleStream(),
          presenter = presenter,
          params = params,
        )
    }
  }
}
```

---

## TEST FILES (SHARED MODULE)

Location: `shared/src/test/kotlin/in/porter/driverapp/shared/root/{parent_path}/{ribname}/`

### 1. TestHelper

**`{RibName}InteractorTestHelper.kt`**
```kotlin
package `in`.porter.driverapp.shared.tests.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.{RibName}Interactor
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.dependency.{RibName}Params
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.state.{RibName}StateReducer
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}Presenter
import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.view.{RibName}VMMapper
import `in`.porter.kmputils.commons.localization.Locale
import `in`.porter.kmputils.flux.base.interactor.InteractorDispatchersFactory
import `in`.porter.kmputils.flux.base.interactorv2.InteractorCoroutineExceptionHandler
import io.mockk.mockk
import kotlinx.coroutines.flow.MutableStateFlow

class {RibName}InteractorTestHelper {

  private val mockPresenter: {RibName}Presenter = mockk(relaxed = true)
  private val mockParams: {RibName}Params = {RibName}Params()
  private val localeStream = MutableStateFlow(Locale.ENGLISH)

  fun createInteractor(): {RibName}Interactor {
    val dispatchers = InteractorDispatchersFactory.createStateVMInteractorDispatcher()

    return {RibName}Interactor(
      dispatchers = dispatchers,
      coroutineExceptionHandler = InteractorCoroutineExceptionHandler { _, _ -> },
      localeStream = localeStream,
      reducer = {RibName}StateReducer(dispatchers.stateDispatcher),
      vmMapper = {RibName}VMMapper(),
      presenter = mockPresenter,
      params = mockParams,
    )
  }

  fun getMockPresenter() = mockPresenter
  fun getMockParams() = mockParams
}
```

### 2. StepDefs

**`{RibName}InteractorStepDefs.kt`**
```kotlin
package `in`.porter.driverapp.shared.tests.root.{parent_path_as_package}.{ribname}

import `in`.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}.{RibName}Interactor
import io.cucumber.java.en.Given
import io.cucumber.java.en.Then
import io.cucumber.java.en.When
import kotlinx.coroutines.runBlocking
import kotlin.test.assertNotNull

class {RibName}InteractorStepDefs {

  private val testHelper = {RibName}InteractorTestHelper()
  private lateinit var interactor: {RibName}Interactor

  @Given("the {RibName} interactor is initialized")
  fun initializeInteractor() {
    interactor = testHelper.createInteractor()
    assertNotNull(interactor)
  }

  @When("the interactor becomes active")
  fun interactorBecomesActive() = runBlocking {
    interactor.onActive()
  }

  @Then("the initial data should be loaded")
  fun verifyInitialDataLoaded() {
    // Add assertions here
  }
}
```

---

## PACKAGE NAMING

### Shared Module
Package: `in.porter.driverapp.shared.root.{parent_path_as_package}.{ribname}`

Examples:
- Parent: "loggedin/home" → `in.porter.driverapp.shared.root.loggedin.home.ordersummary`
- Parent: "paymentplatform" → `in.porter.driverapp.shared.root.paymentplatform.ordersummary`

### UI Module
Package: `com.porter.ui.driverapp.root.{parent_path_as_package}.{ribname}`

Examples:
- Parent: "loggedin/home" → `com.porter.ui.driverapp.root.loggedin.home.ordersummary`
- Parent: "paymentplatform" → `com.porter.ui.driverapp.root.paymentplatform.ordersummary`

### App Module
Package: `com.theporter.android.driverapp.ribs.root.{parent_path_as_package}.{ribname}`

Examples:
- Parent: "loggedin/home" → `com.theporter.android.driverapp.ribs.root.loggedin.home.ordersummary`
- Parent: "paymentplatform" → `com.theporter.android.driverapp.ribs.root.paymentplatform.ordersummary`

## UI TYPE VARIATIONS

### For Page (default)
- View container: `ComposeFrameLayoutContainer`
- Layout: `R.layout.rib_compose_scroll_layout_container`

### For Bottom Sheet
- View container: `ComposeBottomSheetContainer`
- Layout: `R.layout.rib_compose_bottom_sheet_container`

### For Dialog
- View container: `ComposeFrameLayoutContainer` (or custom dialog container)
- Adjust builder accordingly

## EXECUTION STEPS

1. **Ask user for required inputs:**
   - RIB name (PascalCase)
   - Parent path
   - UI type (page/bottomsheet/dialog, default: page)
   - **Parent Communication**: "Does this RIB need to communicate with its parent?" (yes/no)
2. **Perform all validation steps**
3. **Show user a summary:**
   - Directory paths for all three modules
   - Package names for all three modules
   - Total number of files to be created
   - Whether Listener will be created (based on parent communication answer)
4. **Create directory structure** in shared, ui, app, and test modules
   - ALWAYS create: `dependency/`, `state/`, `view/`, `analytics/` subdirectories
5. **Generate all files** with proper package names and class names
   - If Listener needed: Create Dependency wrapper (Params + Listener)
   - If Listener NOT needed: Use Params directly (no wrapper)
6. **Generate test files** (TestHelper + StepDefs) in shared test directory
7. **Output summary:**
   - Files created (grouped by module: shared, ui, app, tests)
   - Package names used
   - Whether Listener was created
   - Next steps for integration

## NEXT STEPS GUIDANCE

After creating files, tell the user:

1. **Implement Business Logic (Shared Module):**
   - Fill in `{RibName}State` with actual state fields
   - Implement state reduction logic in `{RibName}StateReducer`
   - Add business logic to `{RibName}Interactor.onActive()`

2. **Implement UI (UI Module):**
   - Build Compose UI in `{RibName}ComposeView`
   - Define all UI events in `{RibName}UIEvents`
   - Implement presenter methods in `{RibName}ComposeBridge`
   - Update `{RibName}VMFactory` with realistic preview data

3. **Wire Up Dependencies (App Module):**
   - Fill in `ParentComponent` interface with required dependencies from parent
   - Update `{RibName}Module` to provide any additional dependencies
   - Add child builder injections to Router if needed

4. **Integrate with Parent RIB:**
   - Update parent's Builder.Component to extend `{RibName}Builder.ParentComponent`
   - Add `{RibName}Builder` injection to parent's Router
   - Add attach/detach methods in parent's Router

5. **Define Dependency Contract:**
   - Fill in `{RibName}Params` with parameters needed from parent
   - Define callback methods in `{RibName}Listener`
   - Create and pass `{RibName}Dependency` from parent

6. **Implement Analytics (MANDATORY):**
   - Implement `{RibName}Analytics` interface methods
   - Add analytics tracking calls in Interactor (e.g., recordActive, recordSubmitTap)
   - Define event identifiers in `{RibName}EventIdentifiers`

7. **Write Tests:**
   - Implement test scenarios in `{RibName}InteractorStepDefs`
   - Add test cases for state transitions, UI events, and business logic
   - Use `{RibName}InteractorTestHelper` for test setup

8. **Optional Enhancements:**
   - Add navigation in shared `{RibName}Router` for child RIBs
   - Add additional analytics events beyond the basic ones

## SAFETY RULES

- NEVER overwrite existing files without explicit confirmation
- ALWAYS check for naming conflicts across all three modules before creating
- ALWAYS use PascalCase for class names, lowercase for directory names
- ALWAYS use backticks for `in` keyword in shared package names
- NEVER auto-register in parent without asking user
- NEVER generate business logic - only boilerplate structure
- ALWAYS create subdirectories: `dependency/`, `state/`, `view/`, `analytics/` in shared module (ALL are mandatory)
- ALWAYS ask user if Listener is needed before creating dependency files
- ALWAYS create test files: TestHelper and StepDefs for Interactor
- ALWAYS use correct view container based on UI type (page/bottomsheet/dialog)
- NEVER use XML layouts - always use Jetpack Compose
- ALWAYS follow the three-module separation: shared (business logic), ui (compose), app (wiring)
- NEVER use snake_case in package or directory names (use camelCase/lowercase)
