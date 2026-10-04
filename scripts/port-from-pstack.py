"""Apply rstack's mechanical Cursor-to-Claude-Code rewrites to pstack files.

Usage:
    python scripts/port-from-pstack.py FILE...          rewrite files in place
    python scripts/port-from-pstack.py --check [PATH]   list leftover Cursor-isms

The rewrites cover only edits that read the same everywhere. Prose that needs
judgment (deslop, control-ui, cloud agents, model-family wording, README
credits) is reported by --check and fixed by hand. See docs/UPDATING.md.
"""

import pathlib
import re
import sys

MODELS = {
    "claude-opus-5-5-max": "fable",
    "claude-fable-5-thinking-max": "fable",
    "gpt-5.6-sol-max": "opus",
    "grok-4.7-xhigh-fast": "sonnet",
    "grok-4.6-fast-xhigh": "sonnet",
    "claude-opus-5-thinking-xhigh": "haiku",
}

REWRITES = [
    (r"~/\.cursor/rules/pstack-models\.mdc", "~/.claude/rstack-models.md"),
    (r"pstack-models\.mdc", "rstack-models.md"),
    (r"~/\.cursor/projects/", "~/.claude/projects/"),
    (r"~/\.cursor/plugins/", "~/.claude/plugins/"),
    (r"(~/)?\.cursor/(skills|automations|benny|worktrees|settings\.json)", r"\1.claude/\2"),
    (r"`\.cursor`", "`.claude`"),
    (
        r"(?:under )?the active workspace's `agent-transcripts/` directory \(the system prompt names (?:this|the) path\)",
        "under `~/.claude/projects/<project-slug>/` (the project's absolute path with separators turned into dashes)",
    ),
    (r"\bsetup-pstack\b", "setup-rstack"),
    (r"\bgeneralPurpose\b", "general-purpose"),
    (r"^is_background:", "background:"),
    (r"\bAskQuestion\b", "AskUserQuestion"),
    (r'"Comment Sicko"', '"comment-sicko"'),
    (r"^name: Comment Sicko$", "name: comment-sicko"),
    (r"^name: Poteto Mode$", "name: poteto-mode"),
    (r"^(?:mode: true|icon: crown|color: yellow|reminder: New task\?.*)\n", ""),
    (r"- `readonly`: `true`", "- Read-only posture: instruct the subagent to write nothing"),
    (r"\bthe Task tool\b", "the Agent tool"),
    (r"`Task` calls\b", "`Agent` tool calls"),
    (r"`Task` call\b", "`Agent` tool call"),
    (r"\bTask `model`", "Agent `model`"),
    (r"\bTask subagent\b", "subagent (Agent tool)"),
    (r"\bCursor's `/loop`", "Claude Code's `/loop`"),
    (r"\ba Cursor restart\b", "a Claude Code restart"),
    (r"\brestart Cursor\b", "restart Claude Code"),
    (r"\bcloud-agent URL\b", "remote-session URL"),
    (r"\bmodel family\b", "model tier"),
    (r"the closest valid slug of the same family from its error message", "the closest valid alias from its error message"),
    (r"\bReviewers return findings in the `Task` response body", "Reviewers return findings in the Agent tool response body"),
    (r"\b[pr]stack/(skills|agents|docs)/", r"\1/"),
    (r"\ba pstack skill\b", "an rstack skill"),
    (r"\bpstack's\b", "rstack's"),
    (r"\bpstack\b", "rstack"),
    (r"\b([Uu])rstack\b", r"\1pstack"),
    (r"@cursor-skill/", "@rstack/"),
]
REWRITES += [(re.escape(slug), tier) for slug, tier in MODELS.items()]
COMPILED = [(re.compile(pattern, re.MULTILINE), repl) for pattern, repl in REWRITES]

LEFTOVERS = re.compile(
    r"\bCursor\b|\.cursor\b|\bcursor-team-kit\b|\bpstack\b|\bTask\b|\breadonly\b|run_in_background"
    r"|environment: |cloud_base_branch|\bcloud\b|\.mdc\b|alwaysApply|\bgrok\b|\bsol\b|opus 5\.5"
    r"|\bclaude-[a-z0-9.-]+|\bgpt-5[a-z0-9.-]*|\bgrok-[a-z0-9.-]+|create-skill|/deslop|`deslop`"
    r"|control-ui|control-cli|agent-transcripts|\bAskQuestion\b|/add-plugin|\bfamily\b|\bfamilies\b"
)
SKIP_CHECK = {"README.md", "docs/UPDATING.md", "scripts/port-from-pstack.py", "CHANGELOG.md"}


def port(text: str) -> str:
    for pattern, repl in COMPILED:
        text = pattern.sub(repl, text)
    return text


def rewrite(paths: list[str]) -> None:
    for name in paths:
        path = pathlib.Path(name)
        before = path.read_bytes().decode("utf-8")
        crlf = "\r\n" in before
        after = port(before.replace("\r\n", "\n"))
        if crlf:
            after = after.replace("\n", "\r\n")
        if after != before:
            path.write_bytes(after.encode("utf-8"))
            print(f"ported {name}")


CURSOR_ONLY_KEYS = {"mode", "icon", "color", "reminder", "readonly", "is_background"}


def check(root: pathlib.Path) -> int:
    hits = 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if not path.is_file() or rel.startswith(".git/") or rel in SKIP_CHECK:
            continue
        if path.suffix not in {".md", ".json", ".yaml", ".yml", ".sh", ".ts", ".mjs", ".tsv"} and path.name != "watch-pr":
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in LEFTOVERS.finditer(line):
                hits += 1
                print(f"{rel}:{number}: {match.group(0)!r}: {line.strip()[:160]}")
    for path in sorted([*root.glob("skills/*/SKILL.md"), *root.glob("agents/*.md")]):
        rel = path.relative_to(root).as_posix()
        for problem in frontmatter_problems(path):
            hits += 1
            print(f"{rel}:1: frontmatter: {problem}")
    return hits


def frontmatter_problems(path: pathlib.Path) -> list[str]:
    match = re.match(r"---\n(.*?)\n---\n", path.read_text(encoding="utf-8").replace("\r\n", "\n"), re.S)
    if not match:
        return ["missing"]
    keys = dict(re.findall(r"^([\w-]+):\s*(.*)$", match.group(1), re.M))
    problems = [f"no {key}" for key in ("name", "description") if key not in keys]
    if path.name == "SKILL.md" and keys.get("name", "").strip("\"'") != path.parent.name:
        problems.append(f"name {keys.get('name')!r} != directory {path.parent.name!r}")
    problems += [f"Cursor-only key {key}" for key in keys if key in CURSOR_ONLY_KEYS]
    return problems


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if args[:1] == ["--check"]:
        sys.exit(1 if check(pathlib.Path(args[1] if len(args) > 1 else ".")) else 0)
    rewrite(args)
