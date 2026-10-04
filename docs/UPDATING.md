# updating rstack from upstream pstack

rstack tracks [pstack](https://github.com/cursor/plugins/tree/main/pstack), which lives in the `pstack/` directory of `cursor/plugins`. an update is a three-way merge: the pstack commit rstack was last ported from is the base, rstack is ours, and the new pstack commit is theirs. upstream's changes are replayed onto rstack, and every touched file is re-ported to Claude Code.

## lineage

| rstack | pstack | cursor/plugins commit |
|---|---|---|
| 0.14.1 | 0.14.1 | `2a80444425c7bddf429c3bdedf3ab61e791d34d65` |
| 0.15.9 | 0.15.9 | `e43c7ee26e0038c6c1fa8380dd34ce86ff94cb2a` |

add a row with every update. the last row is the base for the next one.

## 1. fetch both upstream commits

```bash
git fetch https://github.com/cursor/plugins <base-sha>:refs/upstream/pstack-<base>
git fetch https://github.com/cursor/plugins <new-sha>:refs/upstream/pstack-<new>
git switch -c update-<new>
```

to find `<new-sha>`, take the latest commit that touches `pstack/` on `cursor/plugins` main, or the commit Cursor caches under `~/.cursor/plugins/cache/cursor-public/pstack/<sha>/`. confirm the version with `git show <new-sha>:pstack/.cursor-plugin/plugin.json`.

see what changed before applying anything:

```bash
git diff --name-status -M refs/upstream/pstack-<base>:pstack refs/upstream/pstack-<new>:pstack
```

## 2. apply upstream's diff with a three-way fallback

```bash
git diff --binary --full-index -M refs/upstream/pstack-<base>:pstack refs/upstream/pstack-<new>:pstack > ../upstream.patch
git apply -3 --exclude=.cursor-plugin/* --exclude=skills/setup-pstack/* <more excludes> ../upstream.patch
```

`git apply -3` is all-or-nothing: one path it can't place aborts the whole patch. exclude these paths and port them by hand:

- `.cursor-plugin/*`. rstack's manifests are `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.
- `skills/setup-pstack/*`. rstack's copy is `skills/setup-rstack/SKILL.md`, which has its own model tables (step 6).
- upstream deletions of files rstack changed. delete them yourself after checking nothing still links to them.
- new Cursor-only skills you won't ship (0.15.9: `skills/make-bot-ui/`). either exclude them or apply and then delete.

on Windows with `core.autocrlf=true`, keep the patch on disk. piping `git archive` or `git show` output through PowerShell rewrites the bytes. use `git -c core.autocrlf=false archive -o file.tar <ref>` when you need a tree on disk.

## 3. resolve conflicts: take theirs, port, restore the hand edits

```bash
git diff --name-only --diff-filter=U > ../conflicts.txt
git checkout --theirs -- $(cat ../conflicts.txt)
python scripts/port-from-pstack.py $(cat ../conflicts.txt)
```

then compare each file against the previous port with `git diff HEAD -- <file>`. a hunk that brings back a Cursor phrase undid a hand edit, so restore the old port's wording for it. keep every hunk that is upstream's own change.

## 4. port every other touched file

```bash
git diff --name-only HEAD > ../touched.txt
git ls-files --others --exclude-standard >> ../touched.txt
python scripts/port-from-pstack.py $(cat ../touched.txt)
```

the script is idempotent, so running it over already-ported files is safe.

## 5. hand edits the script can't make

`python scripts/port-from-pstack.py --check .` lists leftover Cursor-isms and frontmatter problems. port each hit with these conventions:

| pstack | rstack |
|---|---|
| `Task` tool, `subagent_type: "generalPurpose"` | `Agent` tool, `general-purpose` |
| `readonly: true` on a spawn | an instruction in the prompt not to write files |
| `run_in_background: true` | "they run in the background" (the Agent tool's default) |
| cloud agents, `environment: "cloud"` | background subagents, `isolation: "worktree"` for writers |
| `/deslop` (cursor-team-kit) | a slop-strip pass over the diff with the `unslop` skill |
| `control-ui` / `control-cli` | the project's verification skill (`/create-verification-skill`) |
| `/create-skill` | the authoring-a-skill playbook plus Claude Code's SKILL.md format |
| Cursor's `/babysit` | "even when another installed skill's description matches" |
| `~/.cursor/projects/<slug>/agent-transcripts/` | `~/.claude/projects/<project-slug>/` |
| `~/.cursor/rules/pstack-models.mdc` | `~/.claude/rstack-models.md` |
| `AskQuestion` | `AskUserQuestion` |
| Cursor's `/loop`, restarts, dashboard | Claude Code's `/loop`, restarts, a background task's output file |
| "same model family" fallbacks | "next tier down the ladder `fable` > `opus` > `sonnet` > `haiku`" |

some hits are false positives: TypeScript's `readonly`, the word "Task" in templates, and the conditional `origin` forge paths. to see only what this update introduced, diff the hit text against the previous release:

```bash
git -c core.autocrlf=false archive -o ../head.tar HEAD && mkdir ../_head && tar -xf ../head.tar -C ../_head
python scripts/port-from-pstack.py --check ../_head | sed 's/:[0-9]*:/:/' | sort > ../before.txt
python scripts/port-from-pstack.py --check .        | sed 's/:[0-9]*:/:/' | sort > ../after.txt
comm -13 ../before.txt ../after.txt
```

## 6. models

pstack picks models by vendor and slug. rstack maps each role onto a Claude tier:

| pstack 0.15.9 default | rstack tier | roles |
|---|---|---|
| `claude-opus-5-5-max` | `fable` | judgment, prose, hardest tasks, synthesizers |
| `gpt-5.6-sol-max` | `opus` | reflect tooling |
| `grok-4.7-xhigh-fast` | `sonnet` | feature, refactoring, bug fix, perf, hillclimb, explorers, swarm workers |

three-vendor panels (arena, architect, interrogate) become `fable, opus, sonnet`. pstack's reasoning budget becomes a tier cap: `unlimited` keeps the defaults, `large` caps at `opus`, `medium` at `sonnet`, `small` at `haiku`.

when upstream changes a default slug:

1. add the slug to `MODELS` in `scripts/port-from-pstack.py`.
2. update the defaults table in `skills/setup-rstack/SKILL.md`.
3. check every skill's inline defaults against it: `rg -n 'fable|opus|sonnet|haiku' skills`.
4. if old config files now pin stale defaults, update the note in `README.md` and `docs/guide/01-setup.md`.

## 7. readme, manifests, verify, ship

1. apply upstream's `README.md` diff by hand, in rstack's wording: `git diff refs/upstream/pstack-<base> refs/upstream/pstack-<new> -- pstack/README.md`. keep rstack's credits and install block. record new divergences under "differences from the original pstack".
2. bump `version` in `.claude-plugin/plugin.json` to the pstack version.
3. `python scripts/port-from-pstack.py --check .` should report only known false positives.
4. add the lineage row above, commit on the update branch, open a PR, merge.

installed users pick it up with:

```
/plugin marketplace update rstack
```

then start a new session.

## 0.14.1 → 0.15.9 notes

- new upstream: `/correct`, `/benchmark-checklist`, three principles (attack-the-premise, test-behavior-not-implementation, explain-the-number), the opening-a-pr playbook row, `scripts/check-plan.mjs`, and the setup budget step.
- removed upstream: `poteto-mode/references/plan.md`, and how's critic prompt and rubric.
- not ported: `/make-bot-ui`. it drives Cursor Grok Bot routines, and Claude Code has no equivalent.
- defaults: bug fix, perf, and hillclimb moved from `opus` to `sonnet`. panels went from four seats to three.
- fixed a 0.14.1 port bug: replacing every `pstack` with `rstack` had turned "upstack" into "urstack". the script now reverses that.
- `orchestrate.md` needed its cloud-agent lines re-ported after taking theirs. upstream had rewritten the paragraphs around them.
- known gap carried over: `skills/poteto-mode/scripts/worktree-audit.sh` still reads Cursor's transcript path.
