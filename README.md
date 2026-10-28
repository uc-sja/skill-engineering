# Claude Android Toolkit Showcase

A curated collection of Claude Code skills and slash-command workflows for Android and Kotlin Multiplatform (KMP) engineering. The toolkit covers resource analysis, test generation, RIB lifecycle work, XML-to-Compose migration, design-system implementation, analytics instrumentation, asset conversion, UI verification, and heap-leak investigation.

The repository brings together reusable skills and project-scoped workflow examples. These files are agent instructions and workflow templates—not guarantees that code changes, cleanup operations, or tests will succeed without review.

## Featured: `migrate-to-olc`

[`migrate-to-olc`](.claude/driverapp/migrate-to-olc/SKILL.md) is the featured migration workflow in this collection. It guides migration of a legacy DriverAppV3 order-flow unit into OLC 2.0 while treating behavioural parity as the default acceptance criterion. The workflow begins with evidence-backed legacy discovery, maps responsibilities into the target architecture, records conflicts as explicit divergence decisions rather than silently changing behaviour, slices implementation into reviewable stages, and uses Maestro parity flows to verify meaningful scenarios. Its four references provide a target architecture map, a worked pre-end-trip example, host-integration guidance, and a Maestro parity strategy. This is the centrepiece of the showcase because it combines legacy analysis, cross-architecture reasoning, decision traceability, and verification in one repeatable process.

> The OLC migration material contains project-specific architecture and integration details. Confirm publication permission and sanitize confidential references before making this repository public.

## Repository layout

```text
.
├── README.md
└── .claude/
    ├── customerapp/
    │   ├── skills/
    │   │   ├── cleanup-unused-resources/  # SKILL.md + Python scanner helpers
    │   │   └── generate-junit-tests/      # JUnit 5 test-generation skill
    │   └── commands/
    │       ├── analytics/
    │       ├── assets/
    │       ├── design/
    │       ├── migration/
    │       └── testing/
    └── driverapp/
        ├── debugging/
        ├── migrate-to-olc/                # SKILL.md + four references
        ├── rib-lifecycle/
        └── testing/
```

All toolkit files are grouped under `customerapp/` or `driverapp/` to keep the two project collections separate. The repository intentionally contains no duplicate root-level `.claude/skills/` or `.claude/commands/` copies. These folders are organized for showcase and review; standard Claude Code auto-discovery generally expects skills and commands in the standard `.claude/skills/` and `.claude/commands/` directories, so use the appropriate installation/copy step if you want them active in a working repository.

## Skills

### General / CustomerApp skills

#### [`cleanup-unused-resources`](.claude/customerapp/skills/cleanup-unused-resources/SKILL.md)

Identifies potential orphaned resources across Android `res/` directories and Kotlin Multiplatform Compose resources. It uses separate scanning logic for each resource system, accounting for module boundaries, cross-repository references, dynamically loaded assets, and cascading references such as layout includes or drawable selectors. Python helpers support report-first analysis and optional JSON output, with deletion treated as an explicit follow-up step. Scanner findings must be reviewed before deletion, especially where assets may be loaded dynamically by strings or backend configuration.

#### [`generate-junit-tests`](.claude/customerapp/skills/generate-junit-tests/SKILL.md)

Guides the creation or migration of JUnit 5 tests for Kotlin Interactors, use cases, and HTTP services in a KMP codebase. It asks the agent to inspect production code and collaborators, choose a suitable test strategy, follow existing fixtures and conventions, and cover meaningful branches and observable behaviour. For HTTP services, it emphasizes using the production client/factory setup with a mock HTTP engine and asserting both responses and outgoing request details. Coroutine and source-set guidance is repository-specific and should be verified against the target project's current configuration.

### DriverAppV3 — RIB lifecycle

#### [`create-rib`](.claude/driverapp/rib-lifecycle/create-rib/SKILL.md)

Guides an agent through scaffolding a DriverAppV3-style RIB across shared KMP logic, UI, and Android app wiring. It covers inputs such as the RIB name, parent location, UI type, communication needs, dependency contracts, state management, analytics, and tests. The goal is to make new feature scaffolding systematic across layers. Since not all RIBs have UI and conventions can evolve, generated output should be checked against the current architecture guide and a comparable existing RIB.

#### [`read-rib`](.claude/driverapp/rib-lifecycle/read-rib/SKILL.md)

Provides a structured investigation workflow for understanding an existing RIB before changing it. It directs the agent to locate implementation files and trace dependencies, parent/child routing, usages, responsibilities, lifecycle behaviour, and architectural conventions. It aims to produce an evidence-backed model of a feature and its connections rather than infer behaviour from filenames. The actual implementation pattern should determine which checks apply because RIBs may differ in layout and lifecycle methods.

#### [`update-rib`](.claude/driverapp/rib-lifecycle/update-rib/SKILL.md)

Guides targeted changes to an existing RIB, including dependency changes, child RIB wiring, lifecycle updates, renaming or relocating a RIB, Compose conversion, and analytics or view-contract updates. It encourages identifying the intended operation and required parameters before editing. Because a small RIB change can affect DI, routing, lifecycle, and callers, edits should be grounded in the current implementation and validated with appropriate builds and tests.

#### [`delete-rib`](.claude/driverapp/rib-lifecycle/delete-rib/SKILL.md)

Treats RIB removal as a destructive operation that starts with impact analysis. It directs the agent to inventory files, trace references and routing, consider soft-delete versus hard-delete, and seek confirmation before proceeding. Its purpose is to reduce accidental breakage across modules. Before reporting success, verify exact deletion paths, confirm any backup is usable, inspect remaining references, and run relevant validation.

### DriverAppV3 — migration

#### [`migrate-to-olc`](.claude/driverapp/migrate-to-olc/SKILL.md)

The featured workflow for migrating legacy order-flow functionality into OLC 2.0. It establishes the legacy behaviour first, builds a source-backed parity ledger, maps each responsibility to the target architecture, and makes behaviour changes explicit through a divergence register. It also separates library work from host-app integration and requires scenario-based verification rather than relying on compilation or a happy-path screenshot alone. See the four references below for additional architecture and validation detail.

**Supporting references:**

- [`target-map.md`](.claude/driverapp/migrate-to-olc/references/target-map.md) — maps legacy responsibilities to OLC architecture and integration points.
- [`worked-example-pre-end-trip.md`](.claude/driverapp/migrate-to-olc/references/worked-example-pre-end-trip.md) — a worked pre-end-trip migration example and reviewable implementation slicing.
- [`host-stitch.md`](.claude/driverapp/migrate-to-olc/references/host-stitch.md) — host-application integration contracts and wiring that need verification.
- [`maestro-parity.md`](.claude/driverapp/migrate-to-olc/references/maestro-parity.md) — using Maestro flows to compare legacy behaviour with the migrated implementation.

### DriverAppV3 — testing and debugging

#### [`maestro-write-test`](.claude/driverapp/testing/maestro-write-test/SKILL.md)

Guides authoring, debugging, and verification of Maestro UI flows for a MockEngine-backed Android test harness. It emphasizes deriving assertions from expected behaviour, understanding fixture and launch-state dependencies, validating selectors against the UI, and preserving meaningful assertions rather than weakening them to get a green run. It also covers coverage tracking and honest reporting of scenarios that cannot be automated. Some helper scripts or trackers may be developer-local, so availability must be checked before claiming that a workflow was executed.

#### [`heap-leak-investigate`](.claude/driverapp/debugging/heap-leak-investigate/SKILL.md)

Turns a heap-dump digest, dump identifier, or suspect class into a source-backed memory-leak investigation. It uses retention-chain evidence, class-name resolution, object counts, and source searches to develop hypotheses about object retention and missing cleanup. The workflow distinguishes heap evidence from source observations and inferred causes, and encourages a fix or a discriminating experiment rather than treating a suspicious class name as proof.

## Slash-command workflows

The `.claude/customerapp/commands/` directory contains these CustomerApp workflows:

| Area | Command | Purpose |
|---|---|---|
| Analytics | [`add-analytics`](.claude/customerapp/commands/analytics/add-analytics.md) | Add feature analytics events and tests using the project's established event conventions. |
| Assets | [`convert-svg-to-xml`](.claude/customerapp/commands/assets/convert-svg-to-xml.md) | Convert SVG assets to Android vector drawable XML and integrate the resources. |
| Design | [`implement-screen`](.claude/customerapp/commands/design/implement-screen.md) | Implement a Compose screen from design references using the project's design-system components and tokens. |
| Migration | [`create-migration-checklist`](.claude/customerapp/commands/migration/create-migration-checklist.md) | Create a trackable checklist for XML-to-Compose parity across UI states and interactions. |
| Migration | [`migrate-xml-to-ds-rib`](.claude/customerapp/commands/migration/migrate-xml-to-ds-rib.md) | Original XML-backed RIB to Compose/design-system migration workflow. |
| Migration | [`migrate-xml-to-ds-rib_v2`](.claude/customerapp/commands/migration/migrate-xml-to-ds-rib_v2.md) | Revised migration workflow with deeper legacy XML and design-coverage discovery. |
| Testing | [`generate-compose-ui-tests`](.claude/customerapp/commands/testing/generate-compose-ui-tests.md) | Draft Compose UI tests for rendered states, interactions, and UI events. |
| Testing | [`generate-rib-tests`](.claude/customerapp/commands/testing/generate-rib-tests.md) | Derive RIB behaviour scenarios from state, routing, and UI logic. |
| Testing | [`generate-tests`](.claude/customerapp/commands/testing/generate-tests.md) | Generate Kotlin/Cucumber-style tests for component behaviour using repository conventions. |
| Testing | [`test-compose-view`](.claude/customerapp/commands/testing/test-compose-view.md) | Explore Compose view variants with previews and runtime scenarios; review source/manifest changes carefully. |

The two XML-to-Compose/RIB migration commands are retained as separate versions for comparison. Choose and maintain a canonical workflow before using them as a team standard.

## How to use the toolkit

1. Open the relevant `SKILL.md` or command file.
2. Check its prerequisites, repository paths, architecture assumptions, and validation steps.
3. Inspect the target implementation and nearby examples before applying generic templates.
4. Review the generated diff and confirm destructive actions explicitly.
5. Run the relevant build, tests, or UI scenarios where permitted and available.
6. Report what was actually verified, what failed, and what remains untested.

## Important publication and safety notes

- These files were assembled from supplied repository snapshots and have been preserved as project-specific instructions rather than rewritten into universal tools.
- Before making this repository public, confirm permission to publish the original material. Review organization-specific names, architecture details, package names, internal paths, links, PR/commit references, credentials, and proprietary workflows.
- Resource-cleanup results are candidates for review, not automatic proof that a resource is unused. Dynamic references can be missed.
- A successful compile does not prove behavioural or visual parity. Migrations should be checked across meaningful states, interactions, navigation, analytics, accessibility, scrolling, and keyboard behaviour.
- The Maestro and heap-investigation workflows may depend on local helper scripts, trackers, fixtures, or developer tooling that is not included in every checkout.
- No license is included. Confirm the right to publish the content and select a license before adding one.

## Scope and provenance

This showcase groups the supplied CustomerApp skills and command workflows under `.claude/customerapp/` and the DriverAppV3 RIB, OLC migration, Maestro, and heap-investigation skills under `.claude/driverapp/`. Each supplied skill or command is retained in one location; identical root-level copies were removed. The README describes intended use; it does not claim that every command was executed or every generated result was independently validated.
