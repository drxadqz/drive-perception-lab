#!/usr/bin/env python3
r"""Lint public Markdown for GitHub-safe mathematical notation.

Repository convention:

- display mathematics uses fenced ``math`` blocks;
- inline mathematics uses GitHub's robust $`...`$ form;
- TeX delimiters such as \(...\), \[...\], and $$ are forbidden;
- paper-only macros are expanded before a formula enters a note.

The linter intentionally uses only the Python standard library so it can run
both in GitHub Actions and in the daily reading automation.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

INLINE_MATH_RE = re.compile(r"\$`(?P<body>[^`\n]+)`\$")
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
FENCE_RE = re.compile(
    r"^ {0,3}(?P<marker>`{3,}|~{3,})[ \t]*(?P<info>[\w+-]*)"
)
TEX_COMMAND_RE = re.compile(r"\\[A-Za-z]+")
DETAILS_TAG_RE = re.compile(r"</?details\b[^>]*>", re.IGNORECASE)
ENVIRONMENT_RE = re.compile(r"\\(?P<action>begin|end)\{(?P<name>[^{}]+)\}")

FORBIDDEN_DELIMITERS = (r"\(", r"\)", r"\[", r"\]")
UNSUPPORTED_MATH_MACROS = (
    r"\paradigm",
    r"\metric",
    r"\method",
    r"\mathds",
    r"\cref",
    r"\cite",
    r"\label",
    r"\textcolor",
    r"\newcommand",
    r"\renewcommand",
    r"\providecommand",
    r"\DeclareMathOperator",
    r"\def",
)
HIDDEN_CHARACTERS = {
    "\ufeff": "BOM / ZERO WIDTH NO-BREAK SPACE",
    "\ufffd": "Unicode replacement character",
    "\u00a0": "non-breaking space",
    "\u200b": "zero-width space",
    "\u200c": "zero-width non-joiner",
    "\u200d": "zero-width joiner",
}


@dataclass(frozen=True)
class LintError:
    path: Path
    line: int
    rule: str
    message: str

    def render(self) -> str:
        relative = self.path.relative_to(ROOT).as_posix()
        return f"{relative}:{self.line}: {self.rule} {self.message}"


def markdown_paths() -> list[Path]:
    paths = [ROOT / "README.md", ROOT / "SELECTION_POLICY.md"]
    for directory in ("notes", "index", "templates", "docs"):
        paths.extend((ROOT / directory).rglob("*.md"))
    return sorted({path for path in paths if path.is_file()})


def add_error(
    errors: list[LintError],
    path: Path,
    line: int,
    rule: str,
    message: str,
) -> None:
    errors.append(LintError(path, line, rule, message))


def strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Remove HTML comments so hidden examples cannot affect render checks."""

    fragments: list[str] = []
    cursor = 0
    while cursor < len(line):
        if in_comment:
            end = line.find("-->", cursor)
            if end < 0:
                return "".join(fragments), True
            cursor = end + 3
            in_comment = False
            continue
        start = line.find("<!--", cursor)
        if start < 0:
            fragments.append(line[cursor:])
            break
        fragments.append(line[cursor:start])
        cursor = start + 4
        in_comment = True
    return "".join(fragments), in_comment


def is_escaped(value: str, index: int) -> bool:
    backslashes = 0
    cursor = index - 1
    while cursor >= 0 and value[cursor] == "\\":
        backslashes += 1
        cursor -= 1
    return backslashes % 2 == 1


def is_fence_close(line: str, marker: str) -> bool:
    stripped = line.lstrip(" ")
    indent = len(line) - len(stripped)
    if indent > 3 or not stripped.startswith(marker[0]):
        return False
    run = len(stripped) - len(stripped.lstrip(marker[0]))
    return run >= len(marker) and not stripped[run:].strip()


def math_syntax_issues(payload: str) -> list[str]:
    """Return lightweight, dependency-free TeX integrity failures."""

    issues: list[str] = []
    if "$$" in payload or any(item in payload for item in FORBIDDEN_DELIMITERS):
        issues.append("math payload contains a nested math delimiter")
    if any(char == "$" and not is_escaped(payload, index) for index, char in enumerate(payload)):
        issues.append("math payload contains a nested unescaped '$' delimiter")

    for macro in UNSUPPORTED_MATH_MACROS:
        if macro in payload:
            issues.append(f"expand unsupported paper macro {macro!r}")

    brace_depth = 0
    for index, char in enumerate(payload):
        if is_escaped(payload, index):
            continue
        if char == "{":
            brace_depth += 1
        elif char == "}":
            brace_depth -= 1
            if brace_depth < 0:
                issues.append("math payload contains an unmatched '}'")
                break
    if brace_depth > 0:
        issues.append("math payload contains an unclosed '{'")

    environment_stack: list[str] = []
    for match in ENVIRONMENT_RE.finditer(payload):
        action = match.group("action")
        name = match.group("name")
        if action == "begin":
            environment_stack.append(name)
        elif not environment_stack or environment_stack[-1] != name:
            issues.append(f"math environment {name!r} closes out of order")
            break
        else:
            environment_stack.pop()
    if environment_stack:
        issues.append(
            "math environment(s) left open: " + ", ".join(environment_stack)
        )
    return issues


def lint_path(path: Path) -> list[LintError]:
    errors: list[LintError] = []
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        add_error(
            errors,
            path,
            exc.start + 1,
            "MATH009",
            f"file is not strict UTF-8: {exc}",
        )
        return errors

    for character, label in HIDDEN_CHARACTERS.items():
        offset = text.find(character)
        if offset >= 0:
            line = text.count("\n", 0, offset) + 1
            add_error(
                errors,
                path,
                line,
                "MATH009",
                f"contains {label}",
            )

    active_marker: str | None = None
    active_info = ""
    active_line = 0
    active_content: list[str] = []
    details_depth = 0
    in_comment = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if active_marker is not None:
            if is_fence_close(raw_line, active_marker):
                if active_info == "math":
                    payload = "\n".join(active_content).strip()
                    if not payload:
                        add_error(
                            errors,
                            path,
                            active_line,
                            "MATH013",
                            "fenced math block must not be empty",
                        )
                    else:
                        for issue in math_syntax_issues(payload):
                            add_error(
                                errors,
                                path,
                                active_line,
                                "MATH008",
                                issue,
                            )
                active_marker = None
                active_info = ""
                active_line = 0
                active_content = []
                continue

            if active_info == "math":
                active_content.append(raw_line)
            continue

        line, in_comment = strip_html_comments(raw_line, in_comment)
        fence_match = FENCE_RE.match(line)
        if fence_match:
            active_marker = fence_match.group("marker")
            active_info = fence_match.group("info").casefold()
            active_line = line_number
            active_content = []
            if active_info == "math" and details_depth:
                add_error(
                    errors,
                    path,
                    line_number,
                    "MATH012",
                    "GitHub renders fenced math inside <details> as a code block; "
                    "move the equation into visible Markdown",
                )
            continue

        line_without_inline_code = INLINE_CODE_RE.sub("", line)
        for match in DETAILS_TAG_RE.finditer(line_without_inline_code):
            if match.group(0).casefold().startswith("</"):
                if details_depth == 0:
                    add_error(
                        errors,
                        path,
                        line_number,
                        "MATH014",
                        "unmatched </details> can hide or corrupt rendered Markdown",
                    )
                else:
                    details_depth -= 1
            else:
                details_depth += 1

        for match in INLINE_MATH_RE.finditer(line):
            payload = match.group("body")
            for issue in math_syntax_issues(payload):
                add_error(
                    errors,
                    path,
                    line_number,
                    "MATH008",
                    issue,
                )

        without_math = INLINE_MATH_RE.sub("", line)
        without_code = INLINE_CODE_RE.sub("", without_math)

        for delimiter in FORBIDDEN_DELIMITERS:
            if delimiter in without_code:
                add_error(
                    errors,
                    path,
                    line_number,
                    "MATH001",
                    f"use GitHub inline math instead of {delimiter!r}",
                )

        if "$$" in without_code:
            add_error(
                errors,
                path,
                line_number,
                "MATH002",
                "display math must use a fenced ```math block",
            )

        if re.search(r"(?<!\\)\$", without_code):
            add_error(
                errors,
                path,
                line_number,
                "MATH003",
                "inline math must use the complete GitHub $`...`$ form",
            )

        command = TEX_COMMAND_RE.search(without_code)
        if command:
            add_error(
                errors,
                path,
                line_number,
                "MATH004",
                f"TeX command {command.group(0)!r} is outside a math region",
            )

    if active_marker is not None:
        add_error(
            errors,
            path,
            active_line,
            "MATH003",
            "unclosed Markdown fence",
        )
    if in_comment:
        add_error(
            errors,
            path,
            max(1, len(text.splitlines())),
            "MATH014",
            "unclosed HTML comment can hide rendered Markdown",
        )
    if details_depth:
        add_error(
            errors,
            path,
            max(1, len(text.splitlines())),
            "MATH014",
            f"{details_depth} unclosed <details> element(s) can hide rendered Markdown",
        )

    return errors


def collect_errors() -> list[LintError]:
    errors: list[LintError] = []
    for path in markdown_paths():
        errors.extend(lint_path(path))
    return errors


def main() -> int:
    errors = collect_errors()
    if errors:
        for error in errors:
            print(error.render(), file=sys.stderr)
        print(
            f"ERROR: {len(errors)} GitHub Markdown math issue(s) found",
            file=sys.stderr,
        )
        return 1

    print(f"OK: GitHub-safe math in {len(markdown_paths())} Markdown file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
