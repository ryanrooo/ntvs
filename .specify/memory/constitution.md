<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- Template Principle 1 -> I. Canonical Data Integrity
- Template Principle 2 -> II. Idempotent Pipeline Slices
- Template Principle 3 -> III. Contracted Interfaces & Compatibility
- Template Principle 4 -> IV. Test Evidence Before Merge
- Template Principle 5 -> V. Operability & Traceability
Added sections:
- Delivery Constraints
- Development Workflow
Removed sections:
- None
Templates requiring updates:
- ✅ updated /Users/ryannguyen/Documents/projects/ntvs/.specify/templates/plan-template.md
- ✅ updated /Users/ryannguyen/Documents/projects/ntvs/.specify/templates/spec-template.md
- ✅ updated /Users/ryannguyen/Documents/projects/ntvs/.specify/templates/tasks-template.md
- ✅ updated /Users/ryannguyen/Documents/projects/ntvs/README.md
Follow-up TODOs:
- None
-->
# NTVS Constitution

## Core Principles

### I. Canonical Data Integrity
Every change that touches scraped data, transformed records, database schema, or API
responses MUST preserve a single canonical meaning for each domain entity. Features
MUST define source-of-truth ownership, required fields, normalization rules, and
duplicate-handling behavior before implementation begins. Rationale: this project is a
data pipeline and API; silent drift in identifiers, standings, or match records is a
product failure, not a minor defect.

### II. Idempotent Pipeline Slices
Extraction, transformation, loading, and scheduled orchestration MUST be safe to rerun
for the same tournament window without corrupting data or producing duplicate records.
Feature plans MUST describe the rerun behavior for every changed pipeline step, plus
how partial failure recovery is handled. Rationale: Airflow retries, backfills, and
manual reruns are normal operations, so deterministic replay is a non-negotiable
quality bar.

### III. Contracted Interfaces & Compatibility
Database schema changes, file formats, environment variables, and API behavior MUST be
treated as explicit contracts. Any change that alters a public or cross-component
contract MUST document compatibility impact, migration or rollout steps, and the
consumer-facing acceptance criteria. Breaking changes MUST be justified in the plan
before implementation starts. Rationale: this repository spans ETL jobs, storage, and
served responses; unclear contract changes create cascading failures.

### IV. Test Evidence Before Merge
Changes to extraction logic, transformation rules, loading behavior, orchestration, or
API responses MUST include automated tests at the level that proves the risk is
controlled. Unit tests cover parsing and business rules, integration tests cover
database and pipeline interactions, and contract tests cover externally consumed API or
schema behavior. When a proposed change cannot be tested automatically, the plan MUST
state why and define a repeatable manual verification procedure. Rationale: data bugs
are expensive to detect after ingestion and often irreversible without cleanup work.

### V. Operability & Traceability
Production-relevant workflows MUST emit enough structured evidence to diagnose
failures, reconcile records, and confirm successful runs. New features MUST define
logging, error visibility, and operator-facing validation signals proportionate to the
risk of the change. Plans and tasks MUST preserve traceability from source ingestion to
stored records and exposed API responses. Rationale: a pipeline that cannot explain its
results cannot be trusted by downstream users.

## Delivery Constraints

- The repository MUST preserve a clear separation between orchestration in `dags/`,
  application logic in `code/`, and schema initialization in `db/`.
- Features SHOULD prefer incremental, reversible changes over large rewrites. Plans
  MUST document rollback or containment steps for schema, pipeline, and API changes.
- Secrets and environment-specific values MUST stay outside committed source files.
- New dependencies, infrastructure requirements, or recurring operational costs MUST be
  justified in the implementation plan.
- User-facing and consumer-facing behavior MUST be documented in feature specs using
  outcomes and acceptance scenarios rather than implementation details.

## Development Workflow

1. Work begins with a feature specification that describes the user or operator value,
   acceptance scenarios, edge cases, assumptions, and measurable outcomes.
2. The implementation plan MUST pass a Constitution Check covering data integrity,
   idempotency, compatibility, testing, and operability before implementation starts.
3. Task breakdowns MUST include the verification work needed to prove changed behavior,
   plus any migration, observability, and rollback tasks required by the feature.
4. Pull requests and reviews MUST cite the relevant spec, plan, and test evidence.
5. Before merge, contributors MUST verify affected services or jobs still run in the
   repository's local containerized workflow or document why that validation was not
   possible.

## Governance

This constitution supersedes ad hoc project practices for specification, planning,
implementation, and review. Amendments require: (1) the proposed text change, (2) a
summary of the impact on templates or workflow, and (3) updates to any dependent
artifacts in the same change set. Compliance reviews occur during plan approval, task
generation, and pull request review.

Versioning policy follows semantic versioning for governance documents:
- MAJOR: Removes or materially redefines a principle or governance requirement.
- MINOR: Adds a new principle or materially expands required workflow or quality gates.
- PATCH: Clarifies wording without changing expected behavior.

Any constitution exception MUST be documented in the relevant implementation plan under
Complexity Tracking with the simpler alternative rejected and the operational risk it
introduces.

**Version**: 1.0.0 | **Ratified**: 2026-03-22 | **Last Amended**: 2026-03-22
