# PartsHub Constitution
<!--
Sync Impact Report:
Version change: 1.0.0 → 1.1.0
Modified principles: None
Added sections: VI. Testing Isolation (new principle added)
Removed sections: None
Templates requiring updates:
  ✅ plan-template.md - version reference corrected (line 212: v2.1.1 → v1.1.0)
  ✅ spec-template.md - no changes needed
  ✅ tasks-template.md - no changes needed
Follow-up TODOs: None - all testing isolation requirements incorporated
-->

## Core Principles

### I. Specification-Driven Development
Every feature MUST begin with a complete specification document that defines user scenarios, functional requirements, and acceptance criteria before any technical planning occurs. Specifications MUST be business-focused and technology-agnostic to ensure clear requirements gathering.

**Rationale**: Clear requirements prevent scope creep, reduce rework, and ensure stakeholder alignment before technical investment.

### II. Test-Driven Development (NON-NEGOTIABLE)
All code MUST follow strict TDD methodology: Write failing tests → User approval → Implement to make tests pass → Refactor. No implementation code may be written before corresponding tests exist and fail. Contract tests, integration tests, and unit tests are all mandatory.

**Rationale**: TDD ensures code meets requirements, provides regression protection, and creates living documentation of system behavior.

### III. Incremental Design & Planning
Complex features MUST be broken down through systematic planning phases: Research → Design → Contracts → Task Generation. Each phase MUST be completed before the next begins, with constitution compliance checks at each gate.

**Rationale**: Incremental planning prevents over-engineering, catches design flaws early, and maintains architectural consistency.

### IV. Library-First Architecture
All functionality MUST be developed as standalone, self-contained libraries with clear interfaces. Libraries MUST be independently testable, documented, and have well-defined purposes. No organizational-only libraries are permitted.

**Rationale**: Library-first design promotes code reuse, simplifies testing, and creates modular architecture that scales with project complexity.

### V. CLI-Centric Interface
Every library MUST expose its core functionality through a command-line interface using stdin/arguments for input and stdout/stderr for output. Both JSON and human-readable formats MUST be supported for maximum interoperability.

**Rationale**: CLI interfaces ensure automation compatibility, enable easy integration testing, and provide consistent interaction patterns.

### VI. Testing Isolation (NON-NEGOTIABLE)
All tests MUST use isolated test fixtures with proper setup and teardown procedures. Tests MUST NEVER use live production databases or services. Test environments MUST use different ports, databases, and configuration from production systems. Test fixtures MUST ensure complete isolation between test runs.

**Rationale**: Test isolation prevents data corruption, ensures reproducible test results, eliminates environmental dependencies, and protects production systems from test interference.

## Development Workflow

All development MUST follow the /specify → /plan → /tasks → /implement workflow. Features cannot proceed to implementation without passing constitution compliance checks. Code reviews MUST verify adherence to these principles, and complexity violations MUST be documented and justified.

**Branching**: Feature branches MUST use format `###-feature-name`
**Documentation**: All design artifacts MUST be stored in `specs/[###-feature]/` directory
**Testing**: Integration with existing CI/CD processes is required

## Quality Standards

Code MUST pass all linting, type checking, and automated tests before merge. Performance requirements MUST be specified in feature specifications and validated during implementation. Security best practices MUST be followed, with no secrets or credentials committed to the repository.

**Observability**: All components MUST include structured logging and error handling
**Documentation**: Public APIs MUST be documented with examples
**Maintenance**: Technical debt MUST be tracked and addressed within 2 sprints

## Governance

This constitution supersedes all other development practices and guidelines. Amendments require documentation of rationale, stakeholder approval, and migration plan for existing code. All pull requests and code reviews MUST verify constitutional compliance.

**Compliance Reviews**: Constitution adherence MUST be verified at each workflow gate
**Violation Handling**: Complexity deviations MUST be documented in plan.md with justification
**Runtime Guidance**: See agent-specific guidance files (CLAUDE.md, etc.) for implementation details

**Version**: 1.1.0 | **Ratified**: 2025-09-25 | **Last Amended**: 2025-09-27