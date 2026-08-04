# workspace-os — Agent Contract

> **Workspace OS v2 agent contract.** This subdir is a workspace subsystem with a specific responsibility boundary. AI agents loading workspace-os should read this file before touching anything in this directory.

## Purpose
Workspace OS v2 — the validator + mission CLI for the entire ecosystem. Owns the `workspace-os validate` gate, the BOOTSTRAP procedure, and the canonical CONTEXT routing that every other subsystem depends on.

## Operational rules

1. **Identity preservation (Article XI).** NEVER mutate `git config user.name` / `user.email` in this subdir. If a commit author identity is wrong, STOP and ask the operator.
2. **Constitutional authority.** This subdir is governed by `/home/taras/projects/GOVERNANCE/WORKSPACE-CONSTITUTION.md`. Read it before making authority claims.
3. **Bootstrap.** A cold-start that lands in this subdir MUST also load:
   - `/home/taras/projects/IDENTITY.md` (WSOS canonical, Tier-2)
   - `/home/taras/projects/ARCHITECTURE.md` (WSOS canonical, Tier-2)
   - `/home/taras/projects/GOVERNANCE/BOOTSTRAP.md` (Tier-2)
   - `/home/taras/projects/ai-context/v3.1/runtime/EXECUTIVE_CONTEXT.md` (AI Context, Tier-3, 60-sec orientation)
   - `/home/taras/projects/ai-context/v3.1/runtime/AI_BOOTSTRAP.md` (AI Context, Tier-3, task routing)

## Forbiddens

- Do NOT regenerate files in this subdir unless explicitly authorized by the operator
- Do NOT add new dependencies without a documented reason
- Do NOT skip the workspace validator after changes

## Cross-references

- VERIFIED-BACKLOG task: B-17 (subdir CLAUDE.md propagation)
- Validator gate: `workspace-os validate` must remain 16+ PASS / <2 FAIL (current: 16 PASS / 1 FAIL — see CHANGELOG)
- AI Context v3.1 Decision Record: `/home/taras/projects/ai-context/v3.1/governance/AI_CONTEXT_ARCHITECTURE_DECISION_RECORD.md`
- Last updated: 2026-07-30 (Phase 2 ecosystem integration)
