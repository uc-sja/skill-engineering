---
name: maestro-write-test
description: Write, fix or verify a Maestro UI test for the Porter partner app against the Ktor MockEngine harness. Use when given a TestRail C-ID to automate, a failing flow to diagnose, or a request to run/verify flows and update the coverage tracker. Encodes the traps that cost real debugging time — false witnesses, additive RIB attach, rebuild-gated fixtures, and the marking rules that keep the sheet honest.
---

# Writing Maestro tests for the Porter partner app

This suite drives the **`maestro` build flavour**, whose HTTP clients are backed by a Ktor
MockEngine answering from `app/src/maestro/assets/fixtures/`. It never calls a real API, so a
flow's behaviour is a function of its **persona fixture** plus the app's own logic.

Everything below was learned by running these flows on a device. The rules are not style
preferences — each one is here because breaking it produced a wrong result that looked right.

## The prime directive

**Never weaken, delete, or make-optional an assertion to make a flow pass.**

A suspiciously fast pass is a suspect pass. If you cannot assert a case's expected result, the
honest outcome is `Out of scope` with a citation — that is worth far more than a green run that
proves nothing. Retiring a case truthfully is a result; a hollow assertion is a liability that
will be trusted later.

## Step 1 — read the case's Detailed Steps. Always.

```bash
python3 maestro/tools/query_tracker.py --cid C67029        # status, flow, CI bucket, steps
python3 maestro/tools/query_tracker.py --sql "SELECT cid,title,steps FROM cases WHERE ..."
```

The text after each `->` is the **expected result** and is what your assertion must check. A
TestRail title says what a case is *called*; the steps say what it *does*.

**Do not classify coverability from the sheet's `reason` column.** It predates the MockEngine
harness, so it still records blockers a fixture now satisfies. On 2026-08-17 trusting it declared
167 cases undriveable when their steps showed the customer app was only *setup*. It has also been
outright wrong: it claimed the hamburger's Partner Training item opens the legacy TrainingList
screen, when `DrawerItemClickListener.kt:104` is `Training -> openYoutube(context)`, which leaves
the app. Treat `reason` as a historical note; `Detailed Steps` is the current truth.

**A customer app in the steps is setup, not disqualification.** If it merely brings an order into
being and every assertion is on a partner screen, the case is automatable. Only when the
*assertion target* is a customer screen is it out of scope.

## Step 2 — verify every id and string against source before asserting it

Use the `intellij-index` MCP tools (`ide_find_definition`, `ide_find_references`) or grep in
`app/src/main`, `ui/src/main`, `shared/src/commonMain`.

### False witnesses — assertions that pass without proving anything

| Trap | Why it lies |
|---|---|
| `FixedThumbSwitch.kt:37-54` never exports `checked` | It is a `Box` + `clickable` with no `toggleable`/`Role.Switch`, so it always reports `checked: false`. Asserting `checked: false` on a Home-card switch is a **guaranteed pass**. The popup `serviceabilitySwitch` exports it correctly — the defect is Home-card only. |
| A Compose testTag is not a resource-id | It becomes one only when an ancestor sets `Modifier.semantics { testTagsAsResourceId = true }`. `TrainingListView.kt:54-62` sets its toolbar content on a raw `ComposeView` and passes no modifier, so `onboarding_screen_title` carries **no resource-id at all**. Asserting it could never pass. Anchor on the container instead: `childOf: { id: "^.*:id/toolbar$" }`. |
| Compose controls with no `setTestResourceId` and no text | Not addressable at all. |
| Compose colours | Absent from the accessibility tree entirely. Pin a state by the string the fixture pairs with it, never by pixel. |
| Container view ids | Maestro does not surface all of them — `ribWebView` is not matchable even though its Chrome content is (its layout lives in the kmp-utils AAR, not this repo — measured on device 2026-08-21). |
| ConstraintLayout `<Group>`, empty `<FrameLayout>` | Zero bounds, never assertable. |

### `assertNotVisible` is the single most dangerous command in this repo

**RIB attach is additive.** `BaseViewRouterV2.kt:51-52` does `attachChild(it); parentView.addView(it.view)`
and never removes the sibling, and `isVisibleToUser()` performs **no occlusion test**. So a covered
screen keeps exporting every node. Consequences:

- `assertNotVisible` on a covered screen's text or id **can only fail when the app is CORRECT** —
  and would have **passed** in the regression it was written to catch. Four flows carried this
  inverted polarity.
- "We navigated away from Home" is not assertable via `assertNotVisible: drawer_opener` — the whole
  Home card stack is still in the dump while another screen is on top.
- Prove arrival with a **positive** witness that exists on no other screen (e.g.
  `list_training_steps`), not with the absence of the previous screen.

Absence is only assertable when the thing was **never attached** — a different persona, a different
config branch.

### Beware the vacuous negative

`assertNotVisible: "Porter Incentive"` looked meaningful but that string is absent even when the
card is fully present (`DryRunIncentiveCardStateReducer.kt:11` sets `isExpanded = true`, and it is
the *collapsed* label). Before asserting an absence, confirm the string is present in the
opposite state.

## Step 3 — writing the flow

### House style

Two YAML documents. A long comment header that justifies **why each assertion is the right
witness**, not what it does. Then the commands.

```yaml
appId: ${APP_ID}
name: "Area - what the walk proves"
tags: [area, feature]
# COVERS C12345, C12346.
#
# C12345 "<title>": "<steps>" -> "<expected result>".
#
# WHY THIS WITNESS. <the discriminating reason — what a weaker assertion would also pass on>
#
# NOT CLAIMED (<basis>): <ids referenced in prose but not claimed>
#
# LEAVES <end state>. CLEARS APP STATE: <subflow> launches with clearState: true.
# APP_ID, DEFAULT_COUNTRY, <PERSONA>_MOBILE and LOGIN_OTP are injected externally.
---
- runFlow:
    file: ../../subflows/reach_home.yaml
    env: { MOBILE: "${SOME_MOBILE}", OTP: "${LOGIN_OTP}" }
```

**`# COVERS` is load-bearement.** `query_tracker.covers_ids(text)` takes the flow **text** and
credits every `Cxxxxx` it finds outside a `NOT CLAIMED` block. Two rules follow:

- A disclaimer opens a **BLOCK**, not a line. Everything after it is exempt until the block ends.
- The marker must literally read **`NOT CLAIMED`**. A heading like `DROPPED CLAIM` reads as a
  disclaimer to a human and means **nothing** to the parser — twice a retired case was silently
  re-credited `Automated` by a passing flow that still parsed as claiming it.

Check before you claim: `grep -rn "C12345" maestro/journeys maestro/subflows`.

### A subflow's own `env:` OUTRANKS its caller's — never declare defaults there

This is the most expensive trap in the repo, hit four separate times. Declaring `env: { TIMEOUT:
"20000" }` in a subflow does not provide a default — it **silently discards whatever the caller
passed**. It made `await_go_online_block.yaml` a no-op that also deleted the assertion it replaced,
pinned every document upload to gallery tile 0, handed all fifteen callers of `advance_waypoint`
20000 when they had asked for 45000, and left `open_earnings.yaml` with a header promising
"Accepts TIMEOUT" above a block guaranteeing it would not.

Use an `evalScript` guard, which is what the rest of the suite does:

```yaml
- evalScript: "${output.TMO = (typeof TIMEOUT !== 'undefined' && TIMEOUT !== '') ? TIMEOUT : '20000'}"
- extendedWaitUntil: { visible: { id: "x" }, timeout: "${output.TMO}" }
```

A required parameter gets no default at all — assert a selector that cannot exist, so a caller that
forgets it fails loudly naming its own mistake rather than gating on nothing:

```yaml
- runFlow:
    when: { true: "${output.DST === '' ? 'y' : ''}" }
    commands: [{ assertVisible: { id: "__needs_DEST__" } }]
```

### `extendedWaitUntil: notVisible` does not always wait

Verified on one run: the same construct polled correctly for 25.8s waiting an accept card out, and
twenty lines later reported FAILED after **0.365s** against a popup with 4.5s of life left — neither
the condition being met nor the `timeout: 20000` expiring. When you are waiting for something to go
away and the timing matters, poll on your own terms:

```yaml
- repeat:
    times: 20
    while: { visible: { id: "txt_accept_order_response_popup_title" } }
    commands: [{ waitForAnimationToEnd: { timeout: 1000 } }]
- assertNotVisible: { id: "txt_accept_order_response_popup_title" }
```

The `assertNotVisible` after the loop still holds the claim — something that never disappears
exhausts the rounds and fails there. The loop only bounds how long you watch.

### Selectors

- `id:` is a **regex**, so `id: "aBtn|bBtn"` is a valid hard assertion for "either CTA".
- `index:` selects among elements matching the whole selector.
- `text:` is a **full-string** match — `"Improve completion score"` does not match
  `"Improve completion score and login hours"`. For a substring use `.*`, and remember a negative
  needs `.*` on both sides.
- `childOf:` / `above:` / `below:` carry positional claims. Use them when the expected result is
  positional ("the card appears ABOVE order details") — presence alone is not enough.
- `containsChild:` is the right operator when a title lives *inside* the container you are
  disambiguating on. `below:` is wrong there: a header is never below its own child.

### Gestures

- The waypoint advance and any `SwipeableHintView` need a **coordinate** swipe
  (`start: "10%, 93%"` -> `end: "92%, 93%"`). The element-relative form silently no-ops — it
  reports COMPLETED while the waypoint never advances.
- **Never inline a threshold swipe. Use the subflow that guards it.** Every swipe-to-confirm in the
  app is a distance/velocity threshold, and Maestro reports `swipe` COMPLETED on **either side** of
  that threshold — so a drag the device stretches under load does nothing at all, silently, and the
  flow dies later on an assertion whose cause is already off screen. Measured on three separate
  controls in one week (6.2s / 8.5s drags against 3.4s on the runs that passed):

| control | subflow | pass |
|---|---|---|
| bottom action bar — Cash Collected, Arrived, Start Trip, Continue | `subflows/swipe_bottom_action.yaml` | `DEST`, `TIMEOUT` |
| the accept card | `subflows/accept_order_swipe.yaml` | `DEST`, `TIMEOUT` |
| waypoint advance | `subflows/advance_waypoint.yaml` | `ADDRESS`, `TIMEOUT` |

```yaml
- runFlow:
    file: ../../../subflows/swipe_bottom_action.yaml
    env: { DEST: "tripRatingBar", TIMEOUT: "20000" }
```

- **`DEST` must be DURABLE.** These subflows spend an optional wait plus a retry gate deciding
  whether the swipe landed — measured at **seven seconds**. A destination that lives ~5s, such as
  `txt_accept_order_response_popup_title`, is already gone before anything can assert it: converting
  `accept_card_refused_no_reason` cost exactly that. Transient destinations keep an **inline** swipe
  with the wait on the very next line, and nothing in between.
- The two gates differ on purpose. `swipe_bottom_action` and `advance_waypoint` give the first
  attempt the caller's **full** timeout before retrying, because re-swiping a screen that already
  advanced would hit the next screen's control. `accept_order_swipe` cannot — the **offer expires** —
  so it gates on the accept card still being present instead, which is stronger evidence anyway.

- `scrollUntilVisible` is **occlusion-blind** — it stops on bounds, so an element can be "found"
  behind the bottom-anchored GO ONLINE bar and the following `tapOn` hits the bar. Use
  `centerElement: true`.
- `tapOn: { waitToSettleTimeoutMs: 0 }` disables Maestro's post-tap hierarchy settle (9.2s on the
  bench device) when you know the screen does not change.

### Deeplinks — use `portermock://`, never `https://`

No `https://porter.in` App Link flow has ever passed, for two independent reasons: Maestro
resolves `openLink`'s autoVerify target from the flow's **static `appId:` header without env
substitution**, so `pm set-app-links` targets a package literally named `${APP_ID}`; and
`porter.in` is unverified (`pm get-app-links` reads `1024`), so the link resolves to Chrome.

The maestro flavour registers a `portermock://porter.in` ACTION_VIEW filter. `Uri.getRawDeepLink`
(`UriExtensions.kt:6-26`) reads only `pathSegments` minus `partner`/`app` and **ignores scheme and
host**, so the link is equivalent and needs no verification. Never add `autoVerify: true`.

```yaml
- openLink: { link: "portermock://porter.in/partner/app/training/0" }
```

Order notifications use the same bridge: `- openLink: portermock://notify/new_order`.

### What the harness cannot do

| Not assertable | Why |
|---|---|
| Remote WebView page content | MockEngine intercepts **Ktor**, not WebView page loads. A Chrome error page proves a WebView attached and attempted a load — nothing about the page. |
| Anything needing real media | `AndroidDownloadUrlToFile` hands off to the **system DownloadManager**, not Ktor, and fixture URLs are `mock.local`. There is also no app-side timeout, so the app sits on a permanent "Content is getting downloaded" loader and **never reaches a download-failure state** — assert the loader, not a failure message. |
| Mid-session backend state change | Fixtures are static APK assets; `MockPersona.pinTo` is called only by the login route. |
| A short offer window on a slow device | `notif_info.duration_sec` is the accept card's whole life. `openLink` alone has measured **10.5s** on BrowserStack, so a 10s window can lapse before Maestro looks and the failure reads as a broken card. Give the fixture a window the assertions fit inside — but only as far as the flow allows: one that waits for the offer to LAPSE needs it short enough to still lapse inside its own timeout. |
| Notification sound / vibration / silent mode | Not in the accessibility tree. |
| Anything needing local device state | Contacts (BrowserStack's address book is **empty**), adb-pushed files, a real network. **CI viability decides scope** — a local-desk-only pass is `Out of scope` with the environment reason cited, not a debugging-queue item. |

## Step 4 — personas and fixtures

`FixtureLoader.findPersonaRoot` scans **all** groups, so the `by_persona/<group>/` subdirectory is
irrelevant — search by msisdn: `grep -rn "9000000085" maestro/ app/src/maestro/`.

**Everything under `app/src/maestro/assets/fixtures/` is REBUILD-GATED** — it ships inside the APK.
A fixture written now does not exist on the device until:

```bash
GIT_BRANCH_NAME=master ./gradlew assembleMaestroRelease -PdisableR8
```

**Verify the install rather than trusting it.** An APK built before your fixture existed looks
identical to a broken flow:

```bash
P=$(adb shell pm path com.theporter.android.driverapp | head -1 | sed 's/package://' | tr -d '\r')
adb pull "$P" /tmp/inst.apk && unzip -l /tmp/inst.apk | grep <msisdn>
```

**Never add state to a shared persona.** Check who else uses it first. `9000000085` is used by six
flows, two of which pass asserting content is *not* consumed — a pre-consumed tracker there would
invert both. Add a new persona instead, and **rewrite the msisdn inside its copied login fixture**
or `LoginRoutes.sessionFor` reports the number you copied from.

**Declare every new persona env var**, in `maestro/run_maestro.sh` — the declaration near the other
`*_MOBILE` lines **and** the export list further down. An undeclared var interpolates to **empty**
and the flow silently logs in as nobody; that cost a 6-case flow a full run with five perfectly
correct fixtures, and the failure looks exactly like a bad assertion. `bash -n maestro/run_maestro.sh`
after editing.

Wire every new flow into the right `maestro/config_*.yaml`, or it never executes.

## Step 5 — running

```bash
# one flow
MOCK=release bash maestro/run_maestro.sh maestro/journeys/<area>/<flow>.yaml

# a config
MOCK=release CONFIG=config_onboarding_happy.yaml bash maestro/run_maestro.sh

# a worklist, marking the sheet on each pass
bash maestro/tools/verify_and_mark.sh maestro/tools/worklist_x.txt

# one config on BrowserStack, exactly as CI runs it
bash maestro/run_config_on_browserstack.sh --config orders/config_orders_rating.yaml
```

On BrowserStack a config is **one session on a wiped device** and is never split, so its order is
load-bearing: the first entry logs in and later entries ride that session. A config whose `execute`
list exceeds **900 characters** is refused by name — shard it into smaller configs rather than
trimming it. There is no adb, which is why every config opens with
`ci/browserstack_setup/device_setup.yaml` to walk Settings for automatic date/time.

`MOCK=release`, **never** `MOCK=1` — the debug variant blank-screens on first launch and installs
under `...driverapp.debug`, so flows silently target the wrong package.

**One physical device.** Concurrent Maestro sessions kill each other
(`IOException: Command failed (tcp:NNNNN): closed`). Check before launching:

```bash
pgrep -f "verify_and_mark.sh maestro" >/dev/null && echo BUSY || echo FREE
```

Do **not** background a waiter loop that greps for the runner — it matches its own command line and
deadlocks, and two queued batches once silently never ran. Check, then launch directly.

### Reading a failure

`maestro/maestro-results/<flow>.out` holds only the verdict line. **The evidence is in
`~/.maestro/tests/<newest run>/`** — `commands-(<name>).json` for per-command status and duration,
`maestro.log` for per-tap element dumps with `resource-id` and bounds, plus a failure screenshot.
Several root causes came from there and nowhere else. (Map-heavy screens lose the screenshot to
`RESOURCE_EXHAUSTED: gRPC message exceeds maximum size 4194304`.)

Two traps when re-running:

- **`verify_and_mark.sh` SKIPS any flow with a verdict on file.** Always `rm` the stale `.out`
  first, or you will report failures for flows that never ran.
- **Check the `.out` mtime against the APK install time.** Six "failures" once turned out to be
  stale pre-rebuild verdicts.

## Step 6 — marking, and keeping the sheet honest

```bash
python3 maestro/tools/preflight_sync.py --fix      # align all view tabs with master FIRST
python3 maestro/tools/mark_flow.py <flow>          # credit a passing flow's COVERS
python3 maestro/tools/mark_status.py "<status>" "<reason>" C1 C2
python3 maestro/tools/mark_status_bulk.py decisions.json    # per-case status+reason, ONE save
python3 maestro/tools/query_tracker.py --report    # the two locked tables
python3 maestro/tools/reconcile.py                # 8 checks; expect ALL RECONCILED
```

Allowed statuses: `Automated`, `Automatable with mocking`, `Out of scope`, `Backend / API`,
`Blocked — test account`, `Non-LFC (parked)`. Anything else lands the case in no bucket.

- **Sync before verifying.** A journey-tab-only edit once made 8 already-`Automated` cases get
  re-verified on a device.
- **Never run two xlsx writers at once.** `mark_status_bulk` opens every tab and saves once;
  overlapping it with `verify_and_mark`'s own save loses one side silently, and that corrupted the
  workbook twice. Wait for `pgrep` to come back empty.
- **Every retirement needs a cited reason** — a `file:line`, or a quote from the steps. A
  reclassified row with no basis is indistinguishable from one someone gave up on.
- **A blocker with no path to being unblocked is a retirement, not a queue item.** Two cases sat as
  "Blocked — test account" for months when `LoginRoutes.sessionFor` resolves one session per msisdn
  and the identity they needed is a backend relationship the mock cannot express.
- Coverage reports use **one locked format** — generate with `--report`, never hand-assemble.
- Keep `To verify` (never run — a cheap win) separate from `Re-verify` (ran and FAILED — not).

## When a flow fails, suspect the test first

Of the failures diagnosed in the 2026-08 push to 100%, **almost every one was a broken test**, not
a broken app: inverted `assertNotVisible` polarity, occlusion-blind scrolling, an unexported Compose
testTag, single-shot threshold swipes, an undeclared env var, and a flow asserting WebView content
no case ever asked for. Follow `superpowers:systematic-debugging` — root cause before fix, and
prefer a **stronger** assertion over a deleted one.

Genuine app findings do happen, and they belong in `APP_FINDINGS_MAESTRO.md` with source, evidence
and affected cases, so a ticket needs no re-derivation.

## Sources of truth

| What | Where |
|---|---|
| Case classification (statuses, journeys, steps) | `~/StudioProjects/latest_final_update/PartnerApp_Maestro_MASTER.xlsx`, tab `Full Flow-wise (all)` — the other tabs are views |
| Queryable mirror | `~/StudioProjects/latest_final_update/tracker.sqlite` via `query_tracker.py` |
| Session log | `~/StudioProjects/latest_final_update/final_context.md` — **append only, never read or print it** (holds a live key) |
| Coverage, repo-wide | `Partner_App_Repo_source_of_truth.md` |
| Coverage, Order Lifecycle | `OLC_TARGET.md` |
| Pending rebuild dependencies | `maestro/tools/REBUILD_PENDING.md` |

**Never `git add -A` or `git add .`** in this repo — it has swept plaintext credentials before.
Stage explicit paths only.
