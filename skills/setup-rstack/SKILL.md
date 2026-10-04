---
name: setup-rstack
description: Configure which models rstack uses per role and at what budget. Detects your available models and writes a config file that overrides the skill defaults. Use for /setup-rstack, "configure rstack models", "rstack budget", or changing rstack's model choices.
---

# Setup rstack

Write `~/.claude/rstack-models.md`, a config file that sets rstack's model per role.

## Steps

### 1. Detect available models

Claude Code's `Agent` tool accepts the model aliases `fable`, `opus`, `sonnet`, and `haiku`. That set is the dependable source. If this session's tooling exposes newer aliases, prefer the live set. If you cannot detect any, ask the user to paste the aliases they have access to. Never write a real alias you have not confirmed is available. The aliases `inherit-parent` and `auto` are always valid even though they are not detected models.

### 2. Load current state

The default role-to-model mapping is the config shape shown in step 5 below. If `~/.claude/rstack-models.md` already exists, read it and treat its `# budget` line and its role values as the current choices. Otherwise start from those defaults. A line whose role is not in step 5, such as `how critics`, is from a retired role. Drop it.

### 3. Budget, map, and confirm

**(a) Ask for a budget.** Prefer AskUserQuestion over free text. Offer these four options with these exact labels, and name the current budget when the config records one.

- `unlimited — keep defaults`
- `large — cap at opus`
- `medium — cap at sonnet`
- `small — cap at haiku`

**(b) Apply it.** Build the working table from the skill defaults, and on a re-run keep any role you changed by tier, list, or alias (`inherit-parent`, `auto`). `unlimited` leaves every model as in that table. `large`, `medium`, and `small` lower every real alias above the cap to the cap, panel entries included, on the ladder `fable` > `opus` > `sonnet` > `haiku`. An alias at or below the cap stays. If the result is not a detected alias, use the highest detected alias below it, else mark the role as needing a choice. `inherit-parent` and `auto` do not change. So `medium` turns `fable` and `opus` into `sonnet` and leaves `sonnet` alone, and a panel of `fable, opus, sonnet` becomes `sonnet, sonnet, sonnet`.

**(c) Show the roles and confirm.** Show every role with its model, marking any real alias not in the detected set as needing a choice. Also list each line step 2 dropped. Ask whether to accept as-is or change specific roles, offering the detected models plus `inherit-parent` and `auto` (both mean: this role runs on the parent chat model) as the options. Prefer AskUserQuestion over free text. For panel roles (arena runners, architect runners, interrogate reviewers) the value is a list, and one subagent runs per entry, alias entries included, so the list length sets the count. `arena cross-judge pool` is also a list, but Arena selects one value from it whose model tier differs from the parent's when possible. `swarm workers` is the default model for every worker unless a race or comparison assigns another model per arm.

### 4. Validate

Every real alias written must be in the detected set. `inherit-parent` and `auto` always pass. If a chosen real alias is not available, stop and ask again.

### 5. Write the config

Write `~/.claude/rstack-models.md` with a `# budget` line with the chosen label and its cap, and one line per role, using the same labels poteto-mode uses. Overwrite the whole file so re-runs stay idempotent. Shape:

```
# rstack model configuration (overrides skill defaults). One line per role. Delete a line to fall back to the skill default.
# `inherit-parent` or `auto` as a value: the role runs on the parent chat model (omit Agent `model`). Alias entries in a panel list still count toward its fan-out.
# budget: unlimited (no cap)
feature, refactoring: sonnet
bug-fix: sonnet
perf-issue: sonnet
hillclimb: sonnet
judgment and prose: fable
hardest tasks: fable
how explorer: sonnet
how explainer: fable
why investigators: sonnet
why synthesizer: fable
reflect tooling: opus
reflect judgment, divergent, synthesizer: fable
arena runners: fable, opus, sonnet
arena cross-judge pool: fable, opus, sonnet
swarm workers: sonnet
architect runners: fable, opus, sonnet
interrogate reviewers: fable, opus, sonnet
```

### 6. Confirm

Tell the user the config was written and that the skills read it whenever they delegate. Re-running this skill updates it.

### 7. Offer a verification skill (optional)

Check whether the project has a way to drive the real app for proof (a `verify-*` skill, or an existing harness). If not, offer once: "want a project-local verification skill, so agents can drive the app the way a user does and prove changes work? I can generate one with /create-verification-skill." On yes, invoke `/create-verification-skill` (resolves wherever rstack is installed: workspace, user, or plugin). On no, move on without pushing.
