---
name: setup-rstack
description: Configure which models rstack uses per role. Detects your available models and writes a config file that overrides the skill defaults. Use for /setup-rstack, "configure rstack models", or changing rstack's model choices.
---

# Setup rstack

Write `~/.claude/rstack-models.md`, a config file that sets rstack's model per role. The skills read it and fall back to their inline defaults when a line is absent, so this is an override layer, not a requirement.

## Steps

### 1. Detect available models

Claude Code's `Agent` tool accepts the model aliases `sonnet`, `opus`, `haiku`, and `fable`; that set is the dependable source. If this session's tooling exposes newer aliases, prefer the live set. If you cannot detect any, ask the user to paste the slugs they have access to. Never write a real slug you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not detected slugs.

### 2. Load current state

The default role-to-model mapping is the rule shape shown in step 5 below. If `~/.claude/rstack-models.md` already exists, read it and treat its values as the current choices. Otherwise start from those defaults.

### 3. Map and confirm

Show every role with its current model, marking any real slug not in the detected set as needing a choice. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model) as the options. Prefer AskUserQuestion over free text. For panel roles (how critics, arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose model tier differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real slug written must be in the detected set; `inherit-parent` and `auto` always pass. If a chosen real slug is not available, stop and ask again. A rule pointing at a model the user cannot use breaks every delegation that reads it.

### 5. Write the rule

Write `~/.claude/rstack-models.md` with one line per role, using the same labels poteto-mode uses. Overwrite the whole file so re-runs stay idempotent. Shape:

```
# rstack model configuration (overrides skill defaults). One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit Agent `model`). Alias entries in a panel list still count toward its fan-out.
feature, refactoring: sonnet
bug-fix: opus
perf-issue: opus
hillclimb: opus
judgment and prose: fable
hardest tasks: fable
how explorer: sonnet
how explainer: fable
how critics: fable, opus, sonnet, haiku
why investigators: sonnet
why synthesizer: fable
reflect tooling: opus
reflect judgment, divergent, synthesizer: fable
arena runners: fable, opus, sonnet, haiku
arena cross-judge pool: fable, opus, sonnet, haiku
swarm workers: sonnet
architect runners: fable, opus, sonnet, haiku
interrogate reviewers: fable, opus, sonnet, haiku
```

### 6. Confirm

Tell the user the config was written and that the skills read it whenever they delegate. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill` (resolves wherever rstack is installed — workspace, user, or plugin). On no, move on without pushing.
