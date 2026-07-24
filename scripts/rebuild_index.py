#!/usr/bin/env python3
"""Build the human-readable reading hub from index/papers.csv.

The CSV is the single machine-readable source of truth. This script:

1. validates paper metadata and note structure;
2. refreshes generated blocks in README.md and index/topics.md;
3. generates index/papers.md;
4. supports a read-only --check mode for CI and daily automation.

Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "index" / "papers.csv"
README_PATH = ROOT / "README.md"
PAPERS_MD_PATH = ROOT / "index" / "papers.md"
TOPICS_MD_PATH = ROOT / "index" / "topics.md"

REQUIRED_FIELDS = (
    "paper_key",
    "date",
    "title",
    "authors",
    "year",
    "venue",
    "publication_status",
    "proceedings_url",
    "paper_url",
    "arxiv_id",
    "doi",
    "repo_url",
    "repo_commit",
    "topics",
    "selection_score",
    "verification_stage",
    "code_audit_status",
    "reproduction_status",
    "note_path",
    "takeaway",
)

REQUIRED_NOTE_HEADINGS = (
    "## 3 分钟速读",
    "## 10 分钟理解",
    "## 30 分钟深读",
)

# These identifiers came from unpublished planning material and should never
# re-enter the current public tree through the daily automation.
PRIVATE_MARKERS = (
    "SensorLedger3D",
    "CFGap",
    "Process-Sidecar",
)

# The legacy public repository slug contains the old project name. Linking to
# the repository itself is unavoidable and does not reveal any additional
# unpublished content.
ALLOWED_PUBLIC_LITERALS = (
    "https://github.com/drxadqz/sensorledger3d-reading-log",
)

STATUS_LABELS = {
    "Accepted": "正式录用",
    "Preprint": "预印本",
}

CODE_AUDIT_LABELS = {
    "Audited": "官方源码已核到固定 commit",
    "NotAudited": "源码尚未审计",
    "NoOfficialCode": "未找到官方源码",
}


class ValidationFailure(Exception):
    """Raised when the reading index cannot be safely generated."""


def content_for_public_scan(value: str) -> str:
    sanitized = value
    for literal in ALLOWED_PUBLIC_LITERALS:
        sanitized = sanitized.replace(literal, "")
    return sanitized


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and fail if generated files are stale; do not write.",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig").replace("\r\n", "\n")


def load_rows() -> list[dict[str, str]]:
    if not CSV_PATH.is_file():
        raise ValidationFailure(f"Missing index: {CSV_PATH.relative_to(ROOT)}")

    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        if len(fields) != len(set(fields)):
            duplicates = sorted(
                field for field in set(fields) if fields.count(field) > 1
            )
            raise ValidationFailure(
                "Duplicate CSV header(s): " + ", ".join(duplicates)
            )
        if fields != REQUIRED_FIELDS:
            raise ValidationFailure(
                "Invalid CSV schema or column order. Expected: "
                + ",".join(REQUIRED_FIELDS)
            )

        rows = []
        for line_number, raw_row in enumerate(reader, start=2):
            if None in raw_row:
                extras = raw_row[None] or []
                raise ValidationFailure(
                    f"CSV line {line_number}: {len(extras)} unquoted extra value(s); "
                    "quote fields that contain commas"
                )
            row = {key: (value or "").strip() for key, value in raw_row.items()}
            row["_line"] = str(line_number)
            rows.append(row)

    if not rows:
        raise ValidationFailure("index/papers.csv contains no paper rows")
    return rows


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def validate_url(value: str, field: str, line: str, *, optional: bool = False) -> None:
    if optional and not value:
        return
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValidationFailure(f"CSV line {line}: {field} must use an https:// URL")


def safe_note_path(value: str, line: str) -> Path:
    pure = PurePosixPath(value)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or pure.suffix.lower() != ".md"
        or not pure.parts
        or pure.parts[0] != "notes"
    ):
        raise ValidationFailure(f"CSV line {line}: unsafe note_path {value!r}")
    path = ROOT.joinpath(*pure.parts)
    if not path.is_file():
        raise ValidationFailure(f"CSV line {line}: note does not exist: {value}")
    return path


def validate_rows(rows: list[dict[str, str]]) -> None:
    unique_fields: dict[str, set[str]] = {
        "paper_key": set(),
        "title": set(),
        "note_path": set(),
        "arxiv_id": set(),
    }

    for row in rows:
        line = row["_line"]
        for field in REQUIRED_FIELDS:
            value_to_scan = content_for_public_scan(row[field])
            for marker in PRIVATE_MARKERS:
                if marker.casefold() in value_to_scan.casefold():
                    raise ValidationFailure(
                        f"CSV line {line}: {field} contains private marker {marker!r}"
                    )
        for field in REQUIRED_FIELDS:
            if field in {
                "proceedings_url",
                "arxiv_id",
                "doi",
                "repo_url",
                "repo_commit",
            }:
                continue
            if not row[field]:
                raise ValidationFailure(f"CSV line {line}: {field} is required")

        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", row["paper_key"]):
            raise ValidationFailure(
                f"CSV line {line}: paper_key must be a lowercase stable slug"
            )

        try:
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row["date"]):
                raise ValueError
            parsed_date = date.fromisoformat(row["date"])
        except ValueError as exc:
            raise ValidationFailure(
                f"CSV line {line}: invalid ISO date {row['date']!r}"
            ) from exc

        try:
            year = int(row["year"])
        except ValueError as exc:
            raise ValidationFailure(f"CSV line {line}: year must be an integer") from exc
        if not 1900 <= year <= parsed_date.year:
            raise ValidationFailure(
                f"CSV line {line}: implausible publication year {year}"
            )

        try:
            score = float(row["selection_score"])
        except ValueError as exc:
            raise ValidationFailure(
                f"CSV line {line}: selection_score must be numeric"
            ) from exc
        if not 0 <= score <= 10:
            raise ValidationFailure(
                f"CSV line {line}: selection_score must be between 0 and 10"
            )

        if row["publication_status"] not in STATUS_LABELS:
            allowed = ", ".join(STATUS_LABELS)
            raise ValidationFailure(
                f"CSV line {line}: publication_status must be one of {allowed}"
            )
        if row["code_audit_status"] not in CODE_AUDIT_LABELS:
            allowed = ", ".join(CODE_AUDIT_LABELS)
            raise ValidationFailure(
                f"CSV line {line}: code_audit_status must be one of {allowed}"
            )

        if row["publication_status"] == "Accepted" and not row["proceedings_url"]:
            raise ValidationFailure(
                f"CSV line {line}: Accepted papers require proceedings_url"
            )
        if row["publication_status"] == "Preprint" and row["proceedings_url"]:
            raise ValidationFailure(
                f"CSV line {line}: Preprint rows must leave proceedings_url empty"
            )
        validate_url(
            row["proceedings_url"],
            "proceedings_url",
            line,
            optional=row["publication_status"] == "Preprint",
        )
        validate_url(row["paper_url"], "paper_url", line)
        validate_url(row["repo_url"], "repo_url", line, optional=True)

        if bool(row["repo_url"]) != bool(row["repo_commit"]):
            raise ValidationFailure(
                f"CSV line {line}: repo_url and repo_commit must appear together"
            )
        if row["repo_commit"] and not re.fullmatch(r"[0-9a-fA-F]{40}", row["repo_commit"]):
            raise ValidationFailure(
                f"CSV line {line}: repo_commit must be a full 40-character SHA"
            )
        if row["code_audit_status"] == "Audited" and not row["repo_commit"]:
            raise ValidationFailure(
                f"CSV line {line}: Audited code requires repo_url and repo_commit"
            )
        if row["code_audit_status"] == "NoOfficialCode" and row["repo_url"]:
            raise ValidationFailure(
                f"CSV line {line}: NoOfficialCode cannot include repo_url"
            )

        topics = topic_list(row)
        if not 1 <= len(topics) <= 5:
            raise ValidationFailure(
                f"CSV line {line}: topics must contain between 1 and 5 tags"
            )
        normalized_topics = [topic.casefold() for topic in topics]
        if len(normalized_topics) != len(set(normalized_topics)):
            raise ValidationFailure(f"CSV line {line}: topics contain duplicates")
        if len(row["takeaway"]) > 160:
            raise ValidationFailure(
                f"CSV line {line}: takeaway is too long ({len(row['takeaway'])} chars)"
            )

        note_path = safe_note_path(row["note_path"], line)
        note_parts = PurePosixPath(row["note_path"]).parts
        if len(note_parts) < 3 or note_parts[1] != row["date"][:4]:
            raise ValidationFailure(
                f"CSV line {line}: note directory year must match {row['date'][:4]}"
            )
        if not PurePosixPath(row["note_path"]).name.startswith(row["date"] + "-"):
            raise ValidationFailure(
                f"CSV line {line}: note filename must start with {row['date']}-"
            )
        note = read_text(note_path)
        note_lines = note.splitlines()
        expected_h1 = f"# {row['date']} — {row['title']}"
        if not note_lines or note_lines[0].strip() != expected_h1:
            raise ValidationFailure(
                f"CSV line {line}: note H1 must be exactly {expected_h1!r}"
            )
        normalized_note_lines = [item.strip() for item in note_lines]
        heading_positions = []
        for heading in REQUIRED_NOTE_HEADINGS:
            if normalized_note_lines.count(heading) != 1:
                raise ValidationFailure(
                    f"CSV line {line}: note must contain heading {heading!r} exactly once"
                )
            heading_positions.append(normalized_note_lines.index(heading))
        if heading_positions != sorted(heading_positions):
            raise ValidationFailure(
                f"CSV line {line}: 3/10/30-minute headings are out of order"
            )
        if re.search(r"\]\(\s*\)", note):
            raise ValidationFailure(
                f"CSV line {line}: note contains an empty Markdown link"
            )
        for evidence_label in ("[论文]", "[源码]", "[判断]", "[未核验]"):
            if evidence_label not in note:
                raise ValidationFailure(
                    f"CSV line {line}: note is missing evidence label {evidence_label}"
                )
        for required_link in (
            row["paper_url"],
            row["proceedings_url"],
            row["repo_commit"],
        ):
            if required_link and required_link not in note:
                raise ValidationFailure(
                    f"CSV line {line}: note does not contain indexed link/id "
                    f"{required_link!r}"
                )
        note_to_scan = content_for_public_scan(note)
        for marker in PRIVATE_MARKERS:
            if marker.casefold() in note_to_scan.casefold():
                raise ValidationFailure(
                    f"CSV line {line}: public note contains private marker {marker!r}"
                )

        values_to_check = {
            "paper_key": row["paper_key"].casefold(),
            "title": normalized_title(row["title"]),
            "note_path": row["note_path"].casefold(),
            "arxiv_id": row["arxiv_id"].casefold(),
        }
        for field, value in values_to_check.items():
            if not value:
                continue
            if value in unique_fields[field]:
                raise ValidationFailure(
                    f"CSV line {line}: duplicate {field} value {row[field]!r}"
                )
            unique_fields[field].add(value)


def validate_public_markdown() -> None:
    paths = [README_PATH, ROOT / "SELECTION_POLICY.md"]
    for directory in ("notes", "index", "templates", "docs"):
        paths.extend((ROOT / directory).rglob("*.md"))

    seen: set[Path] = set()
    for path in paths:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        content = content_for_public_scan(read_text(path))
        for marker in PRIVATE_MARKERS:
            if marker.casefold() in content.casefold():
                relative = path.relative_to(ROOT).as_posix()
                raise ValidationFailure(
                    f"public Markdown {relative} contains private marker {marker!r}"
                )


def md_escape(value: str) -> str:
    return " ".join(value.split()).replace("|", r"\|")


def status_label(row: dict[str, str]) -> str:
    return STATUS_LABELS.get(row["publication_status"], row["publication_status"])


def code_audit_label(row: dict[str, str]) -> str:
    return CODE_AUDIT_LABELS.get(
        row["code_audit_status"],
        row["code_audit_status"],
    )


def topic_list(row: dict[str, str]) -> list[str]:
    return [item.strip() for item in row["topics"].split(";") if item.strip()]


def root_link(path: str) -> str:
    return PurePosixPath(path).as_posix()


def index_link(path: str) -> str:
    return (PurePosixPath("..") / PurePosixPath(path)).as_posix()


def code_link(row: dict[str, str], label: str | None = None) -> str:
    if not row["repo_url"]:
        return "无官方代码"
    sha = row["repo_commit"]
    text = label or f"官方代码 @ {sha[:8]}"
    return f"[{text}]({row['repo_url']}/tree/{sha})"


def render_stats(rows: list[dict[str, str]]) -> str:
    accepted = sum(row["publication_status"] == "Accepted" for row in rows)
    audited = sum(row["code_audit_status"] == "Audited" for row in rows)
    latest_date = rows[0]["date"]
    return (
        f"**{len(rows)} 篇精读** · **{accepted} 篇正式录用** · "
        f"**{audited} 篇关键源码已审** · 最近更新：**{latest_date}**"
    )


def render_latest(row: dict[str, str]) -> str:
    note = root_link(row["note_path"])
    topics = " · ".join(f"`{md_escape(topic)}`" for topic in topic_list(row))
    if row["publication_status"] == "Accepted":
        identity = (
            f"{status_label(row)}；"
            f"[官方 proceedings]({row['proceedings_url']})"
        )
    else:
        identity = "预印本；**尚无正式录用来源**"
    return "\n".join(
        (
            f"### {row['date']} · [{md_escape(row['title'])}]({note})",
            "",
            f"`{md_escape(row['venue'])} {row['year']}` · "
            f"`{status_label(row)}` · `选文 {row['selection_score']}/10`",
            "",
            f"> **3 分钟结论：** {md_escape(row['takeaway'])}",
            "",
            "| 核验项 | 当前状态 |",
            "|---|---|",
            f"| 论文身份 | {identity} |",
            f"| 阅读深度 | {md_escape(row['verification_stage'])} |",
            f"| 独立复现 | **{md_escape(row['reproduction_status'])}** |",
            f"| 主题 | {topics} |",
            "",
            f"[开始分层精读]({note}) · "
            f"[论文 PDF]({row['paper_url']}) · "
            f"{code_link(row)}",
        )
    )


def render_recent(rows: list[dict[str, str]], limit: int = 8) -> str:
    lines = (
        "| 日期 | 论文 | Venue | 主题 | 验证状态 |",
        "|---|---|---|---|---|",
    )
    output = list(lines)
    for row in rows[:limit]:
        note = root_link(row["note_path"])
        topics = "<br>".join(md_escape(topic) for topic in topic_list(row))
        output.append(
            f"| {row['date']} | [{md_escape(row['title'])}]({note}) | "
            f"{md_escape(row['venue'])} {row['year']} | {topics} | "
            f"{code_audit_label(row)}；"
            f"**{md_escape(row['reproduction_status'])}** |"
        )
    return "\n".join(output)


def render_papers_md(rows: list[dict[str, str]]) -> str:
    accepted = sum(row["publication_status"] == "Accepted" for row in rows)
    lines = [
        "# 全部论文精读",
        "",
        "[返回首页](../README.md) · [主题路线](topics.md) · "
        "[开放问题](open_questions.md)",
        "",
        "> 本页由 `index/papers.csv` 自动生成。请不要手工编辑；运行",
        "> `python scripts/rebuild_index.py` 更新。",
        "",
        f"共 **{len(rows)}** 篇，其中 **{accepted}** 篇已由权威来源核验为正式录用。",
        "“代码已审”不等于“结果已复现”。",
        "",
        "| 日期 | 论文 | Venue / 状态 | 主题 | 一句话结论 | 证据状态 |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        note = index_link(row["note_path"])
        topics = "<br>".join(md_escape(topic) for topic in topic_list(row))
        evidence = (
            f"{md_escape(row['verification_stage'])}<br>"
            f"{code_audit_label(row)}<br>"
            f"**{md_escape(row['reproduction_status'])}**"
        )
        links = (
            f"[精读]({note}) · [论文]({row['paper_url']}) · "
            f"{code_link(row, '代码')}"
        )
        lines.append(
            f"| {row['date']} | **{md_escape(row['title'])}**<br>{links} | "
            f"{md_escape(row['venue'])} {row['year']}<br>{status_label(row)} | "
            f"{topics} | {md_escape(row['takeaway'])} | {evidence} |"
        )
    lines.extend(
        (
            "",
            "## 状态解释",
            "",
            "- **正式录用**：已通过 proceedings、OpenReview decision 或出版社页面核验；",
            "- **预印本**：尚无权威录用来源，不能据此称为顶会论文；",
            "- **代码已审**：阅读了固定 commit 的关键实现；",
            "- **Checkpoint not run**：论文数字尚未被本仓库独立验证。",
            "",
        )
    )
    return "\n".join(lines)


def render_topics(rows: list[dict[str, str]]) -> str:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        for topic in topic_list(row):
            grouped[topic].append(row)

    lines = []
    for topic in sorted(grouped, key=str.casefold):
        topic_rows = sorted(grouped[topic], key=lambda row: row["date"], reverse=True)
        lines.extend((f"### {md_escape(topic)} ({len(topic_rows)})", ""))
        for row in topic_rows:
            note = index_link(row["note_path"])
            suffix = f" · {code_link(row, '代码')}" if row["repo_url"] else ""
            lines.append(
                f"- {row['date']} · [{md_escape(row['title'])}]({note}) — "
                f"{md_escape(row['venue'])} {row['year']} · "
                f"[论文]({row['paper_url']}){suffix}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def replace_block(text: str, name: str, body: str) -> str:
    start = f"<!-- AUTO:{name}:START -->"
    end = f"<!-- AUTO:{name}:END -->"
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValidationFailure(
            f"Expected exactly one start/end marker for generated block {name!r}"
        )
    pattern = re.compile(
        rf"{re.escape(start)}.*?{re.escape(end)}",
        flags=re.DOTALL,
    )
    replacement = f"{start}\n{body.rstrip()}\n{end}"
    # A callable replacement keeps backslashes in titles, topics, and LaTeX
    # summaries literal instead of interpreting them as regex backreferences.
    updated, count = pattern.subn(lambda _match: replacement, text)
    if count != 1:
        raise ValidationFailure(
            f"Expected exactly one generated block {name!r}, found {count}"
        )
    return updated


def expected_files(rows: list[dict[str, str]]) -> dict[Path, str]:
    readme = read_text(README_PATH)
    readme = replace_block(readme, "STATS", render_stats(rows))
    readme = replace_block(readme, "LATEST", render_latest(rows[0]))
    readme = replace_block(readme, "RECENT", render_recent(rows))

    topics = read_text(TOPICS_MD_PATH)
    topics = replace_block(topics, "TOPICS", render_topics(rows))

    return {
        README_PATH: readme.rstrip() + "\n",
        PAPERS_MD_PATH: render_papers_md(rows).rstrip() + "\n",
        TOPICS_MD_PATH: topics.rstrip() + "\n",
    }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def main() -> int:
    args = parse_args()
    try:
        rows = load_rows()
        rows.sort(key=lambda row: (row["date"], row["paper_key"]), reverse=True)
        validate_rows(rows)
        validate_public_markdown()
        targets = expected_files(rows)

        stale = []
        for path, expected in targets.items():
            current = read_text(path) if path.exists() else ""
            if current != expected:
                stale.append(path)
                if not args.check:
                    write_text(path, expected)

        if args.check and stale:
            for path in stale:
                print(f"STALE: {path.relative_to(ROOT).as_posix()}", file=sys.stderr)
            print(
                "Run `python scripts/rebuild_index.py` and commit the results.",
                file=sys.stderr,
            )
            return 1

        if stale:
            for path in stale:
                print(f"UPDATED: {path.relative_to(ROOT).as_posix()}")
        else:
            print("OK: generated pages are current")
        print(f"OK: validated {len(rows)} indexed paper(s)")
        return 0
    except ValidationFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
