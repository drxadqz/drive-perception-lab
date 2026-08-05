#!/usr/bin/env python3
"""Build the human-readable reading hub from paper and Taste indexes.

The CSV is the single machine-readable source of truth. This script:

1. validates paper metadata and note structure;
2. validates the daily transferable-design Taste cards;
3. refreshes generated blocks in README.md and index/topics.md;
4. generates index/papers.md and taste/README.md;
5. supports a read-only --check mode for CI and daily automation.

Only the Python standard library is required.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import struct
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath, PureWindowsPath
from urllib.parse import SplitResult, unquote, urlsplit

import rebuild_research_radar as research_radar


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "index" / "papers.csv"
TASTE_CSV_PATH = ROOT / "index" / "taste.csv"
TAXONOMY_PATH = ROOT / "index" / "taxonomy.json"
README_PATH = ROOT / "README.md"
PAPERS_MD_PATH = ROOT / "index" / "papers.md"
TOPICS_MD_PATH = ROOT / "index" / "topics.md"
TASTE_MD_PATH = ROOT / "taste" / "README.md"
OPEN_QUESTIONS_PATH = ROOT / "index" / "open_questions.md"

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
    "primary_track",
    "modalities",
    "topics",
    "selection_score",
    "verification_stage",
    "code_audit_status",
    "reproduction_status",
    "note_path",
    "takeaway",
)

TASTE_REQUIRED_FIELDS = (
    "taste_key",
    "date",
    "module_name",
    "source_paper",
    "year",
    "venue",
    "publication_status",
    "proceedings_url",
    "paper_url",
    "repo_url",
    "repo_commit",
    "mechanism_family",
    "transfer_targets",
    "note_path",
    "takeaway",
    "main_boundary",
)

TASTE_REQUIRED_HEADINGS = (
    "## 1. 先看瓶颈：为什么需要它",
    "## 2. 原理图：它怎样执行",
    "## 3. 架构位置与接口合同",
    "## 4. 设计 Taste：为什么值得迁移",
    "## 5. 证据、边界与反证实验",
    "## 6. 适用场景与最小接入方案",
)

REQUIRED_NOTE_HEADINGS = (
    "## 1. 看图：论文到底做了什么",
    "## 2. 读公式：核心机制怎样表达",
    "## 3. 看结果：证据是否支持主张",
    "## 4. 对源码：公式如何落地",
    "## 5. 记结论：贡献、边界与开放问题",
)

TRANSLATION_OVERVIEW_HEADING = "阅读起点：术语先导与摘要完整翻译"
REQUIRED_READING_SUBSECTIONS = (
    "首次术语解释",
    "摘要完整专业中文翻译",
    "原文公开的实验配置",
    "原文公开的实验流程",
    "原文结论完整翻译",
    "原文局限与展望完整翻译",
    "笔记分析与研究启发",
)
DAILY_SELECTION_TITLE = "为什么今天值得读"
BACKGROUND_CONTEXT_TITLE = "问题背景与前置工作"
EXPERIMENT_OVERVIEW_TITLE = "数据集与实验设计总览"
PRIOR_ART_AUDIT_TITLE = "开放问题的相邻工作检索"
SELECTION_AND_PRIOR_ART_CONTRACT_DATE = date(2026, 8, 6)
DAILY_SELECTION_FIELDS = (
    "新近性与录用",
    "影响与社区信号",
    "作者与团队脉络",
    "覆盖与研究价值",
    "候选对照",
)
BACKGROUND_CONTEXT_FIELDS = (
    "30 秒问题背景",
    "任务与评价对象",
    "关键前置算法",
    "相关论文路线",
    "本文接在哪里",
    "资料使用边界",
)
EXPERIMENT_OVERVIEW_FIELDS = (
    "数据集与任务",
    "传感器与输入",
    "实验分组",
    "训练—验证—测试路线",
    "指标与回答的问题",
    "一眼看懂实验结论",
)
PRIOR_ART_AUDIT_FIELDS = (
    "待核查主张",
    "检索日期与范围",
    "三路检索式",
    "最接近已有工作",
    "覆盖判断",
    "可保留的差异",
    "公开表述边界",
)
PRIOR_ART_VERDICTS = (
    "[已覆盖]",
    "[部分覆盖]",
    "[本次检索未找到直接覆盖]",
    "[检索受阻]",
)
ARCHITECTURE_SUBSECTION_TITLE = "整体算法架构与创新设计"
ARCHITECTURE_OVERVIEW_LABELS = (
    "原方法瓶颈",
    "主干网络与基线",
    "继承与新增边界",
    "端到端信息流",
    "总体训练方式",
)
ARCHITECTURE_MODULE_FIELDS = (
    "位置与接口",
    "输入",
    "内部变换",
    "输出",
    "为什么这样设计",
    "训练信号",
    "作用与证据",
    "论文位置",
    "源码入口",
)
ARCHITECTURE_CARD_HEADING_RE = re.compile(
    r"^创新(?P<kind>模块|单元)\s*(?P<number>[1-9]\d*)"
    r"\s*[：:]\s*(?P<name>\S.*)"
)
ORIGINAL_TRANSLATION_LABEL = "[原文翻译]"
READER_ANALYSIS_LABEL = "[笔记解释]"
MISSING_SOURCE_SECTION_LABEL = "**原文缺失声明：**"
MIN_GLOSSARY_ENTRIES = 3
MIN_ABSTRACT_TRANSLATION_CHARS = 120
MIN_CONCLUSION_TRANSLATION_CHARS = 60
MIN_EXPERIMENT_CONFIG_ROWS = 5
MIN_EXPERIMENT_CONFIG_BULLETS = 8
MIN_EXPERIMENT_FLOW_STEPS = 5

MARKDOWN_IMAGE_RE = re.compile(
    r"!\[(?P<alt>[^\]]*)\]\((?P<target><[^>]+>|[^)\s]+)"
    r"(?:\s+[\"'][^\"']*[\"'])?\)"
)
MARKDOWN_LINK_RE = re.compile(
    r"(?<!!)\[[^\]\n]+\]\((?P<target><[^>\n]+>|[^)\s]+)"
    r"(?:\s+[\"'][^\"']*[\"'])?\)"
)
FENCE_RE = re.compile(
    r"^(?P<indent> {0,3})(?P<marker>`{3,}|~{3,})"
    r"[ \t]*(?P<info>[^ \t`]*)"
)
INLINE_CODE_RE = re.compile(r"`+[^`\n]*`+")
DETAILS_TAG_RE = re.compile(r"</?details\b[^>]*>", re.IGNORECASE)
HTML_IMAGE_RE = re.compile(r"<img\b", re.IGNORECASE)
HTML_PICTURE_TAG_RE = re.compile(r"</?(?:picture|source)\b", re.IGNORECASE)
HTML_TABLE_TAG_RE = re.compile(r"</?table\b", re.IGNORECASE)
FIGURE_ID_RE = re.compile(r"\bFigure\s+S?\d+[A-Za-z]?\b")
TABLE_ID_RE = re.compile(r"\bTable\s+(?:S?\d+[A-Za-z]?|[A-Z]\d+[A-Za-z]?)\b")
PDF_PAGE_RE = re.compile(r"\bPDF p\.\s*\d+\b")
IMAGE_RIGHTS_NOTICE = "原图版权归原作者及其他权利人"
FORMULA_ALT_PREFIX = "公式："
FORMULA_SOURCE_LABEL = "**公式来源：**"
FORMULA_IDENTITY_LEGEND = (
    "**变量身份图例：** **[领域惯用]** 表示语义角色在本领域常见，但不表示所有论文都使用同一个字母；"
    "**[本文定义]** 表示论文给该符号赋予了本文特定含义；**[源码/笔记重排]** 表示固定源码等价式或本笔记计算新增的符号。"
)
FORMULA_TEACHING_LABELS = (
    "**先建立画面：**",
    "**变量逐项解释与身份：**",
    "**变量变化会怎样：**",
    "**纯文字读法：**",
    "**教学小例子：**",
)
FORMULA_IDENTITY_TAGS = ("[领域惯用]", "[本文定义]", "[源码/笔记重排]")
FORMULA_SOURCE_FILE = "source.tex"
FORMULA_MANIFEST_FILE = "manifest.json"
FORMULA_MIN_DISPLAY_WIDTH = 96
FORMULA_MAX_DISPLAY_WIDTH = 720
FORMULA_MIN_DISPLAY_HEIGHT = 36
FORMULA_MAX_DISPLAY_HEIGHT = 180
FORMULA_PICTURE_RE = re.compile(
    r'^<p align="center"><picture>'
    r'<source media="\(prefers-color-scheme: dark\)" '
    r'srcset="(?P<dark>[^"<>\s]+-dark\.png)">'
    r'<img src="(?P<light>[^"<>\s]+-light\.png)" '
    r'alt="(?P<alt>公式：[^"<>\n]+)" '
    r'width="(?P<width>[1-9]\d*)" height="(?P<height>[1-9]\d*)">'
    r"</picture></p>$"
)
FORMULA_SOURCE_FRAGMENT_RE = re.compile(
    r"^L(?P<begin>[1-9]\d*)-L(?P<end>[1-9]\d*)$"
)
FORMULA_BLOCK_RE = re.compile(
    r"^% BEGIN (?P<name>[a-z0-9-]+)\n"
    r"(?P<body>.*?)"
    r"^% END (?P=name)\s*$",
    re.MULTILINE | re.DOTALL,
)
NUMBERED_EQUATION_SOURCE_RE = re.compile(
    r"\*\*原文公式：\*\*[^\n]*\bEq\.\s*"
    r"(?:\([^)\n]*\d[^)\n]*\)|\d+)[^\n]*\bPDF p\.\s*\d+\b"
)
UNNUMBERED_EQUATION_SOURCE_RE = re.compile(
    r"\*\*原文未编号公式：\*\*[^\n]*\bPDF p\.\s*\d+\b"
)
MARKDOWN_HEADING_RE = re.compile(
    r"^(?P<marks>#{2,4})\s+(?P<title>\S(?:.*\S)?)\s*$"
)
HEADING_NUMBER_RE = re.compile(
    r"^\d+(?:\.\d+)*(?:[.)、：:]|\s)+"
)
STABLE_TRANSLATION_ANCHOR_RE = re.compile(
    r'^<a id="(?P<slug>'
    r"abstract-a(?P<abstract_number>\d{2})"
    r"|conclusion-c(?P<conclusion_number>\d{2})"
    r"|limitations-l(?P<limitations_number>\d{2})"
    r"|(?:future-work|outlook)-o(?P<outlook_number>\d{2})"
    r')"></a>$',
    re.IGNORECASE,
)
TRANSLATION_BLOCK_HEADER_RE = re.compile(
    r"^>\s*\*\*\[原文翻译\]\s+"
    r"(?P<section>Abstract|Conclusion|Discussion(?:\s*(?:/|and|&)\s*Summary)?"
    r"|Summary(?:\s*(?:/|and|&)\s*Discussion)?|Concluding Remarks"
    r"|Limitations?(?:\s*/\s*Discussion)?"
    r"|Future Work(?:\s*(?:/|within)\s*(?:Outlook|Limitations))?|Outlook)"
    r"\s*·\s*(?P<source>.+?)\s*·\s*(?P<code>[ACLO]\d{2})\*\*\s*$",
    re.IGNORECASE,
)
ORIGINAL_LOCATION_RE = re.compile(
    r"(?:"
    r"\bPDF p\.\s*\d+(?:\s*[-–]\s*\d+)?\b"
    r"|§\s*(?:\d+(?:\.\d+)*|[A-Z](?:\.\d+)*|Abstract|Conclusion|Discussion|Summary"
    r"|Limitations?|Future Work|Outlook)"
    r"|\b(?:Section|Sec\.)\s*(?:\d+(?:\.\d+)*|[A-Z](?:\.\d+)*)\b"
    r"|\b(?:Appendix|Supplement(?:ary)?)\s+"
    r"(?:\d+(?:\.\d+)*|[A-Z](?:\.\d+)*)\b"
    r")",
    re.IGNORECASE,
)
PDF_PAGE_RE = re.compile(
    r"\bPDF p\.\s*\d+(?:\s*[-–]\s*\d+)?\b",
    re.IGNORECASE,
)
DATED_NOTE_FILENAME_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}-[^/\\]+\.md$",
    re.IGNORECASE,
)
NUMBERED_FLOW_STEP_RE = re.compile(
    r"^\s*(?P<number>[1-9]\d*)[.)、]\s+"
    r"\*\*(?P<label>[^*\n]{2,40}?)(?:[。.:：])?\*\*\s*"
    r"(?P<body>\S.*)$"
)
MOBILE_GLOSSARY_ENTRY_RE = re.compile(
    r"^\s*[-*]\s+\*\*(?P<term>[^*\n]{2,100})\*\*\s*[：:]\s*"
    r"(?P<explanation>\S.*)\s*$"
)
CONFIG_BULLET_RE = re.compile(
    r"^\s*[-*]\s+\*\*(?P<item>[^*\n]{2,100})\*\*\s*"
    r"(?P<body>\S.*)$"
)
FIXED_SHA_URL_RE = re.compile(
    r"https://github\.com/[^)\s]+/(?:blob|tree)/[0-9a-fA-F]{40}(?:/|$)"
)
EVIDENCE_LABEL_RE = re.compile(
    r"\[(?:论文|源码|未核验)(?:/(?:论文|源码|未核验))*\]"
)
JUDGMENT_LABEL_RE = re.compile(r"\[判断\]")

# These identifiers came from unpublished planning material and should never
# re-enter the current public tree through the daily automation.
PRIVATE_MARKERS = (
    "SensorLedger3D",
    "CFGap",
    "Process-Sidecar",
)

ALLOWED_PUBLIC_LITERALS: tuple[str, ...] = ()

NOTE_TEMPLATE_MARKERS = (
    "NOTE_KEY",
    "example.org",
    "FULL_SHA",
    "Author et al.",
    "在这里放",
    "Figure X",
    "Table X",
    "Eq. (X)",
    "PDF p. Y",
    "Venue YYYY",
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


@dataclass(frozen=True)
class FormulaPicture:
    """One compact, theme-aware formula image referenced by a note."""

    name: str
    light_path: Path
    dark_path: Path
    source_line: int
    anchor_begin: int
    anchor_end: int
    display_width: int
    display_height: int


class MarkdownStructure:
    """Rendered Markdown fragments needed by the note validator."""

    def __init__(
        self,
        *,
        top_level_lines: list[tuple[int, str]],
        rendered_lines: list[tuple[int, str]],
        top_level_math_blocks: list[tuple[int, int, str]],
    ) -> None:
        self.top_level_lines = top_level_lines
        self.rendered_lines = rendered_lines
        self.top_level_math_blocks = top_level_math_blocks

    @property
    def top_level_text(self) -> str:
        return "\n".join(line for _, line in self.top_level_lines)

    @property
    def rendered_text(self) -> str:
        return "\n".join(line for _, line in self.rendered_lines)


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


def load_taxonomy() -> dict[str, object]:
    """Load and validate the stable perception taxonomy definition."""

    if not TAXONOMY_PATH.is_file():
        raise ValidationFailure(
            f"Missing taxonomy: {TAXONOMY_PATH.relative_to(ROOT).as_posix()}"
        )
    try:
        taxonomy = json.loads(read_text(TAXONOMY_PATH))
    except json.JSONDecodeError as exc:
        raise ValidationFailure(f"Invalid taxonomy JSON: {exc}") from exc
    if not isinstance(taxonomy, dict) or taxonomy.get("schema_version") != 1:
        raise ValidationFailure("taxonomy.json must be an object with schema_version 1")

    tracks = taxonomy.get("tracks")
    modalities = taxonomy.get("modalities")
    large_model_tags = taxonomy.get("large_model_tags")
    if not isinstance(tracks, list) or not tracks:
        raise ValidationFailure("taxonomy.json tracks must be a non-empty list")
    if not isinstance(modalities, list) or not modalities:
        raise ValidationFailure("taxonomy.json modalities must be a non-empty list")
    if not isinstance(large_model_tags, list) or not large_model_tags:
        raise ValidationFailure(
            "taxonomy.json large_model_tags must be a non-empty list"
        )

    track_ids: set[str] = set()
    track_names: set[str] = set()
    for position, track in enumerate(tracks, start=1):
        if not isinstance(track, dict):
            raise ValidationFailure(
                f"taxonomy track {position} must be a JSON object"
            )
        required = ("id", "name", "intro", "scope", "question")
        if any(not isinstance(track.get(field), str) or not track[field].strip() for field in required):
            raise ValidationFailure(
                f"taxonomy track {position} requires non-empty "
                "id/name/intro/scope/question"
            )
        track_id = track["id"]
        expected_prefix = f"p{position:02d}-"
        if (
            not track_id.startswith(expected_prefix)
            or not re.fullmatch(r"p\d{2}-[a-z0-9-]+", track_id)
        ):
            raise ValidationFailure(
                f"taxonomy track {position} id must start with {expected_prefix!r}"
            )
        normalized_name = track["name"].casefold()
        if track_id in track_ids or normalized_name in track_names:
            raise ValidationFailure("taxonomy track ids and names must be unique")
        track_ids.add(track_id)
        track_names.add(normalized_name)

    def validate_string_list(values: object, field: str) -> list[str]:
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
        ):
            raise ValidationFailure(
                f"taxonomy.json {field} must contain non-empty strings"
            )
        normalized = [value.casefold() for value in values]
        if len(normalized) != len(set(normalized)):
            raise ValidationFailure(f"taxonomy.json {field} contains duplicates")
        return values

    validate_string_list(modalities, "modalities")
    validate_string_list(large_model_tags, "large_model_tags")
    return taxonomy


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


def load_taste_rows() -> list[dict[str, str]]:
    if not TASTE_CSV_PATH.is_file():
        raise ValidationFailure(
            f"Missing index: {TASTE_CSV_PATH.relative_to(ROOT)}"
        )

    with TASTE_CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fields = tuple(reader.fieldnames or ())
        if fields != TASTE_REQUIRED_FIELDS:
            raise ValidationFailure(
                "Invalid Taste CSV schema or column order. Expected: "
                + ",".join(TASTE_REQUIRED_FIELDS)
            )
        rows = []
        for line_number, raw_row in enumerate(reader, start=2):
            if None in raw_row:
                raise ValidationFailure(
                    f"Taste CSV line {line_number}: unquoted extra value(s)"
                )
            row = {key: (value or "").strip() for key, value in raw_row.items()}
            row["_line"] = str(line_number)
            rows.append(row)

    if not rows:
        raise ValidationFailure("index/taste.csv contains no Taste rows")
    return rows


def normalized_title(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def validate_url(value: str, field: str, line: str, *, optional: bool = False) -> None:
    if optional and not value:
        return
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValidationFailure(f"CSV line {line}: {field} must use an https:// URL")


def strip_html_comments(line: str, in_comment: bool) -> tuple[str, bool]:
    """Remove Markdown HTML comments while preserving visible text."""

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


def is_fence_close(line: str, marker: str) -> bool:
    """Return whether *line* closes the active CommonMark-style fence."""

    stripped = line.lstrip(" ")
    indent = len(line) - len(stripped)
    if indent > 3 or not stripped.startswith(marker[0]):
        return False
    run = len(stripped) - len(stripped.lstrip(marker[0]))
    return run >= len(marker) and not stripped[run:].strip()


def outside_details(
    line: str,
    details_depth: int,
    *,
    source_line: int,
) -> tuple[str, int]:
    """Keep only text rendered outside ``<details>`` elements."""

    fragments: list[str] = []
    cursor = 0
    for match in DETAILS_TAG_RE.finditer(line):
        if details_depth == 0:
            fragments.append(line[cursor : match.start()])
        tag = match.group(0).casefold()
        if tag.startswith("</"):
            if details_depth == 0:
                raise ValidationFailure(
                    f"Markdown line {source_line}: unmatched </details>"
                )
            details_depth -= 1
        else:
            details_depth += 1
        cursor = match.end()
    if details_depth == 0:
        fragments.append(line[cursor:])
    return "".join(fragments), details_depth


def scan_markdown(note: str) -> MarkdownStructure:
    """Parse the Markdown regions that GitHub actually renders.

    Fenced code, HTML comments, inline code, and collapsed ``<details>`` content
    cannot satisfy the indexed note's visible learning-path requirements.
    """

    top_level_lines: list[tuple[int, str]] = []
    rendered_lines: list[tuple[int, str]] = []
    top_level_math_blocks: list[tuple[int, int, str]] = []

    in_comment = False
    details_depth = 0
    active_marker: str | None = None
    active_info = ""
    active_start = 0
    active_depth = 0
    active_content: list[str] = []

    for line_number, raw_line in enumerate(note.splitlines(), start=1):
        if active_marker is not None:
            if is_fence_close(raw_line, active_marker):
                if active_info == "math" and active_depth == 0:
                    top_level_math_blocks.append(
                        (active_start, line_number, "\n".join(active_content).strip())
                    )
                active_marker = None
                active_info = ""
                active_start = 0
                active_depth = 0
                active_content = []
            else:
                active_content.append(raw_line)
            continue

        line, in_comment = strip_html_comments(raw_line, in_comment)
        fence_match = FENCE_RE.match(line)
        if fence_match:
            active_marker = fence_match.group("marker")
            active_info = fence_match.group("info").casefold()
            active_start = line_number
            active_depth = details_depth
            active_content = []
            continue

        without_inline_code = INLINE_CODE_RE.sub("", line)
        rendered_lines.append((line_number, without_inline_code))
        visible_line, details_depth = outside_details(
            without_inline_code,
            details_depth,
            source_line=line_number,
        )
        top_level_lines.append((line_number, visible_line))

    if in_comment:
        raise ValidationFailure("Markdown contains an unclosed HTML comment")
    if active_marker is not None:
        raise ValidationFailure(
            f"Markdown line {active_start}: unclosed Markdown fence"
        )
    if details_depth:
        raise ValidationFailure("Markdown contains an unclosed <details> element")

    return MarkdownStructure(
        top_level_lines=top_level_lines,
        rendered_lines=rendered_lines,
        top_level_math_blocks=top_level_math_blocks,
    )


def normalized_heading(line: str) -> tuple[int, str] | None:
    """Return a visible Markdown heading's level and number-free title."""

    match = MARKDOWN_HEADING_RE.fullmatch(line.strip())
    if match is None:
        return None
    title = HEADING_NUMBER_RE.sub("", match.group("title").strip(), count=1)
    return len(match.group("marks")), title.strip()


def visible_reading_sections(
    structure: MarkdownStructure,
) -> dict[str, tuple[int, int, list[tuple[int, str]]]]:
    """Collect uniquely named visible sections required by the reading standard.

    Values are ``(heading level, source line, body lines)``.  A section body
    ends at the next heading of the same or a higher level, which prevents text
    in a neighbouring subsection from satisfying its requirements.
    """

    headings: list[tuple[int, int, int, str]] = []
    required_titles = {
        TRANSLATION_OVERVIEW_HEADING,
        *REQUIRED_READING_SUBSECTIONS,
        ARCHITECTURE_SUBSECTION_TITLE,
        DAILY_SELECTION_TITLE,
        BACKGROUND_CONTEXT_TITLE,
        EXPERIMENT_OVERVIEW_TITLE,
        PRIOR_ART_AUDIT_TITLE,
    }
    for index, (source_line, content) in enumerate(structure.top_level_lines):
        parsed = normalized_heading(content)
        if parsed is None:
            continue
        level, title = parsed
        headings.append((index, source_line, level, title))

    sections: dict[str, tuple[int, int, list[tuple[int, str]]]] = {}
    for position, (line_index, source_line, level, title) in enumerate(headings):
        if title not in required_titles:
            continue
        if title in sections:
            raise ValidationFailure(
                f"Markdown line {source_line}: reading section {title!r} "
                "must appear exactly once"
            )
        body_end = len(structure.top_level_lines)
        for next_index, _, next_level, _ in headings[position + 1 :]:
            if next_level <= level:
                body_end = next_index
                break
        sections[title] = (
            level,
            source_line,
            structure.top_level_lines[line_index + 1 : body_end],
        )
    return sections


def meaningful_character_count(lines: list[tuple[int, str]]) -> int:
    """Count prose characters while excluding validation labels and markup."""

    fragments: list[str] = []
    ignored_labels = (
        ORIGINAL_TRANSLATION_LABEL,
        READER_ANALYSIS_LABEL,
        MISSING_SOURCE_SECTION_LABEL,
    )
    for _, raw_line in lines:
        line = raw_line
        if any(label in line for label in ignored_labels):
            continue
        line = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", line)
        line = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", line)
        line = re.sub(r"<[^>]+>", "", line)
        line = re.sub(r"[*_~`>#|\-\s]", "", line)
        fragments.append(line)
    return len("".join(fragments))


def section_text(lines: list[tuple[int, str]]) -> str:
    return "\n".join(content for _, content in lines)


def contract_prose_character_count(text: str) -> int:
    """Count reader-contract prose without discarding evidence-labelled lines."""

    for label in (
        ORIGINAL_TRANSLATION_LABEL,
        READER_ANALYSIS_LABEL,
        "[论文]",
        "[论文/源码]",
        "[论文/笔记解释]",
        "[源码]",
        "[判断]",
        "[未核验]",
    ):
        text = text.replace(label, "")
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[*_~`>#|\-\s]", "", text)
    return len(text)


def contract_field_blocks(
    lines: list[tuple[int, str]],
    fields: tuple[str, ...],
    *,
    line: str,
    section_title: str,
) -> dict[str, tuple[int, str]]:
    """Return uniquely anchored field blocks from a reader-facing contract."""

    anchors: list[tuple[int, int, str]] = []
    for index, (source_line, content) in enumerate(lines):
        stripped = content.strip()
        for field in fields:
            if stripped.startswith(f"**{field}：**"):
                anchors.append((index, source_line, field))
                break

    found_names = [field for _, _, field in anchors]
    missing = [field for field in fields if field not in found_names]
    duplicates = sorted(
        {field for field in found_names if found_names.count(field) > 1}
    )
    out_of_order = not missing and not duplicates and found_names != list(fields)
    if missing or duplicates or out_of_order:
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if duplicates:
            details.append("duplicated " + ", ".join(duplicates))
        if out_of_order:
            details.append("fields must keep the documented order")
        raise ValidationFailure(
            f"CSV line {line}: {section_title!r} contract fields are invalid: "
            + "; ".join(details)
        )

    blocks: dict[str, tuple[int, str]] = {}
    for position, (start_index, source_line, field) in enumerate(anchors):
        end_index = (
            anchors[position + 1][0]
            if position + 1 < len(anchors)
            else len(lines)
        )
        blocks[field] = (
            source_line,
            "\n".join(content for _, content in lines[start_index:end_index]),
        )
    return blocks


def validate_selection_and_prior_art_contract(
    *,
    structure: MarkdownStructure,
    published_date: date,
    line: str,
    note_text: str | None = None,
) -> None:
    """Validate transparent daily selection and scoped prior-art claims."""

    if published_date < SELECTION_AND_PRIOR_ART_CONTRACT_DATE:
        return

    sections = visible_reading_sections(structure)
    missing = [
        title
        for title in (DAILY_SELECTION_TITLE, PRIOR_ART_AUDIT_TITLE)
        if title not in sections
    ]
    if missing:
        raise ValidationFailure(
            f"CSV line {line}: notes dated {published_date.isoformat()} or later "
            "must include reader-facing selection/prior-art section(s): "
            + ", ".join(missing)
        )

    selection_level, selection_line, selection_lines = sections[
        DAILY_SELECTION_TITLE
    ]
    prior_level, prior_line, prior_lines = sections[PRIOR_ART_AUDIT_TITLE]
    if selection_level != 3:
        raise ValidationFailure(
            f"CSV line {line}: {DAILY_SELECTION_TITLE!r} on Markdown line "
            f"{selection_line} must be an H3"
        )
    if prior_level != 4:
        raise ValidationFailure(
            f"CSV line {line}: {PRIOR_ART_AUDIT_TITLE!r} on Markdown line "
            f"{prior_line} must be an H4"
        )

    major_lines = {
        content.strip(): source_line
        for source_line, content in structure.top_level_lines
        if content.strip() in REQUIRED_NOTE_HEADINGS
    }
    abstract_line = sections["摘要完整专业中文翻译"][1]
    analysis_line = sections["笔记分析与研究启发"][1]
    if not (
        abstract_line
        < selection_line
        < major_lines[REQUIRED_NOTE_HEADINGS[0]]
        and analysis_line < prior_line
    ):
        raise ValidationFailure(
            f"CSV line {line}: daily selection must follow the complete abstract "
            "and precede Section 1; prior-art audit must remain inside the "
            "Section 5 analysis region"
        )

    selection = contract_field_blocks(
        selection_lines,
        DAILY_SELECTION_FIELDS,
        line=line,
        section_title=DAILY_SELECTION_TITLE,
    )
    newness = selection["新近性与录用"][1]
    if (
        re.search(r"20\d{2}", newness) is None
        or re.search(r"https?://", newness) is None
        or re.search(r"Accepted|正式录用|Preprint|预印本", newness) is None
    ):
        raise ValidationFailure(
            f"CSV line {line}: '新近性与录用' requires year, publication "
            "status, and an authoritative URL"
        )
    impact = selection["影响与社区信号"][1]
    if (
        re.search(r"20\d{2}-\d{2}-\d{2}", impact) is None
        or re.search(r"https?://", impact) is None
    ):
        raise ValidationFailure(
            f"CSV line {line}: '影响与社区信号' requires a query date and "
            "a checkable source URL"
        )
    team = selection["作者与团队脉络"][1]
    if re.search(r"https?://", team) is None or not any(
        phrase in team for phrase in ("不是论文质量", "不等于论文质量", "不能替代")
    ):
        raise ValidationFailure(
            f"CSV line {line}: '作者与团队脉络' requires an official URL "
            "and an explicit prestige-is-not-quality boundary"
        )
    coverage = selection["覆盖与研究价值"][1]
    if re.search(r"\bP(?:0[1-9]|1[0-3])\b", coverage) is None:
        raise ValidationFailure(
            f"CSV line {line}: '覆盖与研究价值' must name one P01-P13 track"
        )
    candidate = selection["候选对照"][1]
    if re.search(r"https?://", candidate) is None:
        raise ValidationFailure(
            f"CSV line {line}: '候选对照' requires at least one official "
            "candidate URL"
        )

    prior = contract_field_blocks(
        prior_lines,
        PRIOR_ART_AUDIT_FIELDS,
        line=line,
        section_title=PRIOR_ART_AUDIT_TITLE,
    )
    search_scope = prior["检索日期与范围"][1]
    if (
        re.search(r"20\d{2}-\d{2}-\d{2}", search_scope) is None
        or len(re.findall(r"(?:proceedings|OpenReview|PMLR|IEEE|ACM|"
                          r"Springer|arXiv|OpenAlex|Semantic Scholar|Crossref)",
                          search_scope, flags=re.IGNORECASE)) < 2
    ):
        raise ValidationFailure(
            f"CSV line {line}: prior-art search scope requires a date and at "
            "least two named scholarly source families"
        )
    queries = prior["三路检索式"][1]
    if not all(term in queries for term in ("机制词", "问题词", "同义词")):
        raise ValidationFailure(
            f"CSV line {line}: prior-art audit requires three query "
            "families: mechanism, problem, and synonym/neighbouring terms"
        )
    if note_text is not None:
        raw_queries_match = re.search(
            r"(?ms)^\*\*三路检索式：\*\*(?P<body>.*?)"
            r"(?=^\*\*最接近已有工作：\*\*)",
            note_text,
        )
        raw_queries = raw_queries_match.group("body") if raw_queries_match else ""
        for query_family in ("机制词", "问题词", "同义词/邻域词"):
            if re.search(
                rf"{re.escape(query_family)}：`[^`\r\n]{{3,}}`", raw_queries
            ) is None:
                raise ValidationFailure(
                    f"CSV line {line}: {query_family!r} must contain a "
                    "non-empty literal query string in a code span"
                )
    closest = prior["最接近已有工作"][1]
    if re.search(r"https?://", closest) is None or meaningful_character_count(
        [(prior["最接近已有工作"][0], closest)]
    ) < 40:
        raise ValidationFailure(
            f"CSV line {line}: closest-work audit requires an official URL and "
            "a substantive four-axis overlap/delta comparison"
        )
    verdict_text = prior["覆盖判断"][1]
    verdicts = [verdict for verdict in PRIOR_ART_VERDICTS if verdict in verdict_text]
    if len(verdicts) != 1:
        raise ValidationFailure(
            f"CSV line {line}: '覆盖判断' must contain exactly one allowed verdict"
        )
    if verdicts[0] == "[检索受阻]":
        raise ValidationFailure(
            f"CSV line {line}: blocked prior-art search cannot be merged; keep "
            "the reviewable branch or PR until sources are available"
        )
    delta = prior["可保留的差异"][1]
    if meaningful_character_count([(prior["可保留的差异"][0], delta)]) < 30:
        raise ValidationFailure(
            f"CSV line {line}: '可保留的差异' is too vague to be falsifiable"
        )
    boundary = prior["公开表述边界"][1]
    if not all(phrase in boundary for phrase in ("本次检索", "不等于", "学界无人做过")):
        raise ValidationFailure(
            f"CSV line {line}: prior-art boundary must state that a scoped "
            "search is not proof that nobody in the field has done it"
        )


def validate_background_and_experiment_overview(
    *,
    structure: MarkdownStructure,
    published_date: date,
    line: str,
) -> None:
    """Require a front-loaded context map and a reader-first experiment map."""

    if published_date < SELECTION_AND_PRIOR_ART_CONTRACT_DATE:
        return

    sections = visible_reading_sections(structure)
    missing = [
        title
        for title in (BACKGROUND_CONTEXT_TITLE, EXPERIMENT_OVERVIEW_TITLE)
        if title not in sections
    ]
    if missing:
        raise ValidationFailure(
            f"CSV line {line}: notes dated {published_date.isoformat()} or later "
            "must include reader-facing background/experiment section(s): "
            + ", ".join(missing)
        )

    background_level, background_line, background_lines = sections[
        BACKGROUND_CONTEXT_TITLE
    ]
    overview_level, overview_line, overview_lines = sections[
        EXPERIMENT_OVERVIEW_TITLE
    ]
    if background_level != 3:
        raise ValidationFailure(
            f"CSV line {line}: {BACKGROUND_CONTEXT_TITLE!r} on Markdown line "
            f"{background_line} must be an H3"
        )
    if overview_level != 3:
        raise ValidationFailure(
            f"CSV line {line}: {EXPERIMENT_OVERVIEW_TITLE!r} on Markdown line "
            f"{overview_line} must be an H3"
        )

    major_lines = {
        content.strip(): source_line
        for source_line, content in structure.top_level_lines
        if content.strip() in REQUIRED_NOTE_HEADINGS
    }
    selection_line = sections[DAILY_SELECTION_TITLE][1]
    config_line = sections["原文公开的实验配置"][1]
    flow_line = sections["原文公开的实验流程"][1]
    if not (
        selection_line
        < background_line
        < major_lines[REQUIRED_NOTE_HEADINGS[0]]
        and major_lines[REQUIRED_NOTE_HEADINGS[2]]
        < overview_line
        < config_line
        < flow_line
    ):
        raise ValidationFailure(
            f"CSV line {line}: background must follow daily selection and "
            "precede Section 1; experiment overview must be the first H3 in "
            "Section 3, before detailed configuration and flow"
        )

    background = contract_field_blocks(
        background_lines,
        BACKGROUND_CONTEXT_FIELDS,
        line=line,
        section_title=BACKGROUND_CONTEXT_TITLE,
    )
    story = background["30 秒问题背景"][1]
    if (
        READER_ANALYSIS_LABEL not in story
        or contract_prose_character_count(story) < 60
    ):
        raise ValidationFailure(
            f"CSV line {line}: '30 秒问题背景' requires a substantive "
            f"{READER_ANALYSIS_LABEL} traffic-scenario explanation"
        )

    task = background["任务与评价对象"][1]
    if (
        "[论文]" not in task
        or "→" not in task
        or re.search(r"(?:PDF\s*pp?\.|论文\s*§|https?://)", task) is None
        or contract_prose_character_count(task) < 60
    ):
        raise ValidationFailure(
            f"CSV line {line}: '任务与评价对象' requires paper evidence, "
            "an input-to-output arrow, a source anchor, and substantive scope"
        )

    prerequisites = background["关键前置算法"][1]
    if (
        "[论文" not in prerequisites
        or contract_prose_character_count(prerequisites) < 100
    ):
        raise ValidationFailure(
            f"CSV line {line}: '关键前置算法' must explain the interfaces and "
            "limits of the indispensable prior methods"
        )

    route = background["相关论文路线"][1]
    if (
        len(re.findall(r"https?://", route)) < 2
        or "本文" not in route
        or contract_prose_character_count(route) < 120
    ):
        raise ValidationFailure(
            f"CSV line {line}: '相关论文路线' requires at least two official "
            "paper URLs and substantive inheritance/difference explanations"
        )

    position = background["本文接在哪里"][1]
    if (
        "[判断]" not in position
        or contract_prose_character_count(position) < 50
    ):
        raise ValidationFailure(
            f"CSV line {line}: '本文接在哪里' requires a substantive, "
            "analysis-labelled inherited/changed/unresolved boundary"
        )

    source_boundary = background["资料使用边界"][1]
    if not (
        "[判断]" in source_boundary
        and "解析" in source_boundary
        and re.search(r"不(?:作为|能作为)", source_boundary)
        and "原论文" in source_boundary
        and "固定" in source_boundary
    ):
        raise ValidationFailure(
            f"CSV line {line}: '资料使用边界' must state that explainers are "
            "not final evidence and facts return to papers and fixed source"
        )

    overview = contract_field_blocks(
        overview_lines,
        EXPERIMENT_OVERVIEW_FIELDS,
        line=line,
        section_title=EXPERIMENT_OVERVIEW_TITLE,
    )
    datasets = overview["数据集与任务"][1]
    if (
        "[论文]" not in datasets
        or not all(split in datasets for split in ("train", "val", "test"))
        or re.search(r"(?:PDF\s*pp?\.|论文\s*§|Supplement\s*§|https?://)", datasets)
        is None
        or contract_prose_character_count(datasets) < 80
    ):
        raise ValidationFailure(
            f"CSV line {line}: '数据集与任务' requires paper evidence, all "
            "train/val/test states (including explicit non-disclosure), and a "
            "source anchor"
        )

    inputs = overview["传感器与输入"][1]
    if (
        not any(label in inputs for label in ("[论文]", "[论文/源码]", "[源码]"))
        or contract_prose_character_count(inputs) < 50
    ):
        raise ValidationFailure(
            f"CSV line {line}: '传感器与输入' requires paper/source evidence "
            "and a substantive per-dataset input description"
        )

    groups = overview["实验分组"][1]
    group_terms = (
        "主 benchmark",
        "主比较",
        "消融",
        "鲁棒",
        "泛化",
        "效率",
        "部署",
        "迁移",
        "跟踪",
    )
    if sum(term in groups for term in group_terms) < 3:
        raise ValidationFailure(
            f"CSV line {line}: '实验分组' must identify at least three "
            "main/ablation/robustness/generalization/efficiency group roles"
        )

    route = overview["训练—验证—测试路线"][1]
    if (
        not any(label in route for label in ("[论文]", "[论文/源码]", "[源码]"))
        or route.count("→") < 4
        or "训练" not in route
        or not any(term in route for term in ("验证", "选模"))
        or not any(term in route for term in ("测试", "最终评测"))
    ):
        raise ValidationFailure(
            f"CSV line {line}: '训练—验证—测试路线' must expose the full "
            "data-to-final-evaluation arrow flow and evidence boundary"
        )

    metrics = overview["指标与回答的问题"][1]
    if (
        "[论文" not in metrics
        or "不等于" not in metrics
        or contract_prose_character_count(metrics) < 70
    ):
        raise ValidationFailure(
            f"CSV line {line}: '指标与回答的问题' requires paper evidence, "
            "metric meaning, and an explicit 'does not equal' boundary"
        )

    conclusion = overview["一眼看懂实验结论"][1]
    if not (
        "[判断]" in conclusion
        and "最强" in conclusion
        and re.search(r"Table|Figure|表\s*\d|图\s*\d", conclusion)
        and re.search(r"最大.{0,8}边界", conclusion)
    ):
        raise ValidationFailure(
            f"CSV line {line}: '一眼看懂实验结论' requires the strongest "
            "numbered evidence and the maximum evidence boundary"
        )


def validate_open_questions_contract() -> None:
    """Keep legacy/open questions from silently becoming novelty claims."""

    text = read_text(OPEN_QUESTIONS_PATH)
    active_text = text.split("## 已关闭问题", maxsplit=1)[0]
    blocks = re.findall(
        r"(?ms)^## Q\d{3}\b.*?(?=^## Q\d{3}\b|\Z)", active_text
    )
    if not blocks:
        raise ValidationFailure("index/open_questions.md has no active QNNN entries")
    for block in blocks:
        heading = block.splitlines()[0]
        status_matches = re.findall(
            r"(?m)^- \*\*相邻工作核查状态\*\*：(?P<value>.+)$", block
        )
        boundary_matches = re.findall(
            r"(?m)^- \*\*公开表述边界\*\*：(?P<value>.+)$", block
        )
        if len(status_matches) != 1 or len(boundary_matches) != 1:
            raise ValidationFailure(
                f"{heading}: requires exactly one adjacent-work audit status "
                "and one public-claim boundary"
            )
        status = status_matches[0]
        if not any(value in status for value in ("NeedsPriorArtAudit", "Audited")):
            raise ValidationFailure(
                f"{heading}: adjacent-work status must be NeedsPriorArtAudit or Audited"
            )
        boundary = boundary_matches[0]
        if "待验证问题" not in boundary or "无人做过" not in boundary:
            raise ValidationFailure(
                f"{heading}: public boundary must keep the item as a testable "
                "question and forbid nobody-has-done-it wording"
            )
        if "Audited" in status:
            for label in ("检索日期与范围", "最接近已有工作", "覆盖判断"):
                if f"- **{label}**：" not in block:
                    raise ValidationFailure(
                        f"{heading}: Audited status requires {label!r}"
                    )
            if re.search(r"https?://", block) is None:
                raise ValidationFailure(
                    f"{heading}: Audited status requires an official closest-work URL"
                )


def labeled_paragraphs(
    lines: list[tuple[int, str]],
    label: str,
) -> list[str]:
    """Return labeled prose paragraphs, including wrapped continuation lines."""

    paragraphs: list[str] = []
    for index, (_, content) in enumerate(lines):
        if label not in content:
            continue
        parts = [content.strip()]
        cursor = index + 1
        while cursor < len(lines):
            _, continuation = lines[cursor]
            stripped = continuation.strip()
            if (
                not stripped
                or normalized_heading(stripped) is not None
                or STABLE_TRANSLATION_ANCHOR_RE.fullmatch(stripped)
                or TRANSLATION_BLOCK_HEADER_RE.fullmatch(stripped)
            ):
                break
            parts.append(stripped)
            cursor += 1
        paragraphs.append(" ".join(parts))
    return paragraphs


def anchored_field_paragraphs(
    lines: list[tuple[int, str]],
    fields: tuple[str, ...],
) -> dict[str, list[str]]:
    """Collect vertical-card fields whose labels begin a visible paragraph.

    Requiring ``**字段：**`` at the start prevents several nominal fields from
    being packed into one line and sharing a single provenance anchor.
    """

    field_patterns = {
        field: re.compile(rf"^\*\*{re.escape(field)}：\*\*\s*(?P<value>.*)$")
        for field in fields
    }
    paragraphs = {field: [] for field in fields}
    index = 0
    while index < len(lines):
        _, content = lines[index]
        stripped = content.strip()
        matched_field: str | None = None
        for field, pattern in field_patterns.items():
            if pattern.fullmatch(stripped):
                matched_field = field
                break
        if matched_field is None:
            index += 1
            continue

        parts = [stripped]
        cursor = index + 1
        while cursor < len(lines):
            _, continuation = lines[cursor]
            continuation_stripped = continuation.strip()
            if not continuation_stripped:
                break
            if normalized_heading(continuation_stripped) is not None:
                break
            if any(
                pattern.fullmatch(continuation_stripped)
                for pattern in field_patterns.values()
            ):
                break
            parts.append(continuation_stripped)
            cursor += 1
        paragraphs[matched_field].append(" ".join(parts))
        index = cursor
    return paragraphs


def plain_prose_character_count(value: str) -> int:
    """Count substantive prose after removing links, labels, and markup."""

    plain = re.sub(r"https?://\S+", "", value)
    plain = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", plain)
    plain = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", plain)
    plain = re.sub(r"\[(?:论文|源码|未核验|判断)(?:/[^\]]+)?\]", "", plain)
    plain = re.sub(r"<[^>]+>", "", plain)
    plain = re.sub(r"[*_`>#|\-\s]", "", plain)
    return len(plain)


def has_evidence_token(value: str, token: str) -> bool:
    """Return whether a bracketed provenance label contains ``token``."""

    for label in re.findall(r"\[([^\]\n]+)\]", value):
        if token in {part.strip() for part in label.split("/")}:
            return True
    return False


def _markdown_table_cells(value: str) -> list[str] | None:
    """Split a GitHub Markdown table row, with or without outer pipes."""

    stripped = value.strip()
    while stripped.startswith(">"):
        stripped = stripped[1:].lstrip()
    if "|" not in stripped:
        return None
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    cells = [cell.strip() for cell in stripped.split("|")]
    if len(cells) < 2:
        return None
    return cells


def markdown_table_rows(lines: list[tuple[int, str]]) -> list[tuple[int, list[str]]]:
    """Return rows from valid visible GitHub Markdown table blocks."""

    rows: list[tuple[int, list[str]]] = []
    index = 0
    while index + 1 < len(lines):
        header_line, header_content = lines[index]
        header_cells = _markdown_table_cells(header_content)
        separator_cells = _markdown_table_cells(lines[index + 1][1])
        if (
            header_cells is None
            or separator_cells is None
            or len(header_cells) != len(separator_cells)
            or not all(
                re.fullmatch(r":?-+:?", cell)
                for cell in separator_cells
            )
        ):
            index += 1
            continue

        rows.append((header_line, header_cells))
        cursor = index + 2
        while cursor < len(lines):
            source_line, content = lines[cursor]
            cells = _markdown_table_cells(content)
            if cells is None or len(cells) != len(header_cells):
                break
            rows.append((source_line, cells))
            cursor += 1
        index = cursor
    return rows


def source_evidence_is_specific(value: str) -> bool:
    """Return whether an experiment item has a checkable source or absence."""

    if ORIGINAL_LOCATION_RE.search(value):
        return True
    if FIXED_SHA_URL_RE.search(value):
        return True
    return "[未核验]" in value and bool(
        re.search(
            r"(?:未公开|未报告|未披露|未说明|未给出|无法确认|尚未运行|"
            r"没有提供|没有报告|没有说明)",
            value,
        )
    )


def github_repo_identity(value: str) -> tuple[str, str] | None:
    """Return a normalized GitHub ``(owner, repo)`` pair."""

    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.netloc.casefold() != "github.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return None
    return parts[0].casefold(), parts[1].removesuffix(".git").casefold()


def translation_section_family(section_name: str) -> str:
    """Map a truthful source-section label to its stable translation family."""

    normalized = section_name.casefold()
    if normalized.startswith("abstract"):
        return "Abstract"
    if normalized.startswith(
        ("conclusion", "discussion", "summary", "concluding remarks")
    ):
        return "Conclusion"
    if normalized.startswith("limitation"):
        return "Limitations"
    if normalized.startswith(("future work", "outlook")):
        return "Future Work"
    raise ValidationFailure(
        f"unsupported source section in translation header: {section_name!r}"
    )


def mobile_config_entries(
    lines: list[tuple[int, str]],
) -> list[tuple[int, str, str]]:
    """Collect bold mobile-card bullets together with their indented body."""

    entries: list[tuple[int, str, str]] = []
    index = 0
    while index < len(lines):
        source_line, content = lines[index]
        match = CONFIG_BULLET_RE.fullmatch(content)
        if match is None:
            index += 1
            continue
        body_parts = [match.group("body")]
        cursor = index + 1
        while cursor < len(lines):
            _, continuation = lines[cursor]
            if (
                not continuation.strip()
                or CONFIG_BULLET_RE.fullmatch(continuation)
                or normalized_heading(continuation) is not None
                or not continuation.startswith((" ", "\t"))
            ):
                break
            body_parts.append(continuation.strip())
            cursor += 1
        entries.append(
            (source_line, match.group("item"), " ".join(body_parts))
        )
        index = max(cursor, index + 1)
    return entries


def numbered_flow_entries(
    lines: list[tuple[int, str]],
) -> list[tuple[int, re.Match[str], str]]:
    """Collect numbered experiment steps and their indented continuation text."""

    entries: list[tuple[int, re.Match[str], str]] = []
    index = 0
    while index < len(lines):
        source_line, content = lines[index]
        match = NUMBERED_FLOW_STEP_RE.fullmatch(content)
        if match is None:
            index += 1
            continue
        body_parts = [match.group("body")]
        cursor = index + 1
        while cursor < len(lines):
            _, continuation = lines[cursor]
            if (
                not continuation.strip()
                or NUMBERED_FLOW_STEP_RE.fullmatch(continuation)
                or normalized_heading(continuation) is not None
                or not continuation.startswith((" ", "\t"))
            ):
                break
            body_parts.append(continuation.strip())
            cursor += 1
        entries.append((source_line, match, " ".join(body_parts)))
        index = max(cursor, index + 1)
    return entries


def parse_translation_blocks(
    lines: list[tuple[int, str]],
    *,
    line: str,
    section_title: str,
) -> list[dict[str, object]]:
    """Parse stable, source-anchored quoted translation blocks."""

    blocks: list[dict[str, object]] = []
    consumed_headers = 0
    for index, (anchor_line, content) in enumerate(lines):
        anchor_match = STABLE_TRANSLATION_ANCHOR_RE.fullmatch(content.strip())
        if anchor_match is None:
            continue
        next_index = index + 1
        while next_index < len(lines) and not lines[next_index][1].strip():
            next_index += 1
        if next_index >= len(lines):
            raise ValidationFailure(
                f"CSV line {line}: translation anchor on Markdown line "
                f"{anchor_line} has no [原文翻译] header"
            )
        header_line, header_content = lines[next_index]
        header_match = TRANSLATION_BLOCK_HEADER_RE.fullmatch(
            header_content.strip()
        )
        if header_match is None:
            raise ValidationFailure(
                f"CSV line {line}: translation anchor on Markdown line "
                f"{anchor_line} must be followed by a canonical [原文翻译] header"
            )
        consumed_headers += 1
        code = header_match.group("code").upper()
        slug = anchor_match.group("slug").casefold()
        if not slug.endswith("-" + code.casefold()):
            raise ValidationFailure(
                f"CSV line {line}: stable anchor {slug!r} does not match "
                f"translation code {code!r}"
            )
        section_name = header_match.group("section")
        section_family = translation_section_family(section_name)
        expected_prefix = {
            "Abstract": "A",
            "Conclusion": "C",
            "Limitations": "L",
            "Future Work": "O",
        }
        if code[0] != expected_prefix[section_family]:
            raise ValidationFailure(
                f"CSV line {line}: {section_name!r} translation must use an "
                f"{expected_prefix[section_family]}NN stable code"
            )
        if PDF_PAGE_RE.search(header_match.group("source")) is None:
            raise ValidationFailure(
                f"CSV line {line}: [原文翻译] header on Markdown line "
                f"{header_line} requires a numeric PDF page"
            )

        translated_lines: list[tuple[int, str]] = []
        cursor = next_index + 1
        while cursor < len(lines):
            translated_line, translated_content = lines[cursor]
            stripped = translated_content.strip()
            if STABLE_TRANSLATION_ANCHOR_RE.fullmatch(stripped):
                break
            if normalized_heading(stripped) is not None:
                break
            if not stripped:
                cursor += 1
                continue
            if not stripped.startswith(">"):
                break
            quote = stripped[1:].strip()
            if quote and not quote.startswith("[!"):
                translated_lines.append((translated_line, quote))
            cursor += 1
        if not translated_lines:
            raise ValidationFailure(
                f"CSV line {line}: [原文翻译] block {code} contains no quoted "
                "Chinese translation"
            )
        translated_text = section_text(translated_lines)
        if READER_ANALYSIS_LABEL in translated_text or "[判断]" in translated_text:
            raise ValidationFailure(
                f"CSV line {line}: [原文翻译] block {code} mixes in "
                "[笔记解释] or [判断]"
            )
        blocks.append(
            {
                "code": code,
                "family": section_family,
                "source_section": section_name,
                "anchor_line": anchor_line,
                "end_line": translated_lines[-1][0],
                "lines": translated_lines,
            }
        )

    body = section_text(lines)
    if body.count(ORIGINAL_TRANSLATION_LABEL) != consumed_headers:
        raise ValidationFailure(
            f"CSV line {line}: {section_title!r} contains an unanchored "
            "[原文翻译] marker"
        )
    return blocks


def validate_contiguous_translation_codes(
    blocks: list[dict[str, object]],
    family: str,
    *,
    line: str,
    required: bool,
) -> list[dict[str, object]]:
    family_blocks = [block for block in blocks if block["family"] == family]
    if required and not family_blocks:
        raise ValidationFailure(
            f"CSV line {line}: missing source-anchored {family} translation"
        )
    actual_codes = [str(block["code"]) for block in family_blocks]
    prefix = {"Abstract": "A", "Conclusion": "C", "Limitations": "L", "Future Work": "O"}[
        family
    ]
    expected_codes = [
        f"{prefix}{number:02d}" for number in range(1, len(family_blocks) + 1)
    ]
    if actual_codes != expected_codes:
        raise ValidationFailure(
            f"CSV line {line}: {family} stable codes must be unique, ordered, "
            f"and contiguous from {prefix}01"
        )
    return family_blocks


def translation_character_count(blocks: list[dict[str, object]]) -> int:
    lines: list[tuple[int, str]] = []
    for block in blocks:
        lines.extend(block["lines"])  # type: ignore[arg-type]
    return meaningful_character_count(lines)


def validate_translation_first_reading(
    note_path: Path,
    line: str,
    *,
    structure: MarkdownStructure,
) -> None:
    """Enforce the translation-first reading contract for every indexed note."""

    relative_note = note_path.relative_to(ROOT).as_posix()

    sections = visible_reading_sections(structure)
    expected_titles = {
        TRANSLATION_OVERVIEW_HEADING,
        *REQUIRED_READING_SUBSECTIONS,
    }
    missing = sorted(expected_titles - sections.keys())
    if missing:
        raise ValidationFailure(
            f"CSV line {line}: new note {relative_note!r} is missing required "
            "translation-first section(s): " + ", ".join(missing)
        )

    overview_level, overview_line, _ = sections[TRANSLATION_OVERVIEW_HEADING]
    if overview_level != 2:
        raise ValidationFailure(
            f"CSV line {line}: {TRANSLATION_OVERVIEW_HEADING!r} must be an H2"
        )
    for title in REQUIRED_READING_SUBSECTIONS:
        level, heading_line, _ = sections[title]
        if level != 3:
            raise ValidationFailure(
                f"CSV line {line}: {title!r} on Markdown line {heading_line} "
                "must be an H3"
            )

    major_lines = {
        content.strip(): source_line
        for source_line, content in structure.top_level_lines
        if content.strip() in REQUIRED_NOTE_HEADINGS
    }
    figure_line = major_lines[REQUIRED_NOTE_HEADINGS[0]]
    result_line = major_lines[REQUIRED_NOTE_HEADINGS[2]]
    code_line = major_lines[REQUIRED_NOTE_HEADINGS[3]]
    conclusion_line = major_lines[REQUIRED_NOTE_HEADINGS[4]]
    glossary_line = sections["首次术语解释"][1]
    abstract_line = sections["摘要完整专业中文翻译"][1]
    config_line = sections["原文公开的实验配置"][1]
    process_line = sections["原文公开的实验流程"][1]
    translated_conclusion_line = sections["原文结论完整翻译"][1]
    outlook_line = sections["原文局限与展望完整翻译"][1]
    analysis_line = sections["笔记分析与研究启发"][1]
    if not (
        overview_line < glossary_line < abstract_line < figure_line
        and result_line < config_line < process_line < code_line
        and conclusion_line
        < translated_conclusion_line
        < outlook_line
        < analysis_line
    ):
        raise ValidationFailure(
            f"CSV line {line}: translation-first sections are out of order or "
            "outside their abstract/result/conclusion regions"
        )

    glossary_lines = sections["首次术语解释"][2]
    entries = []
    for index, (source_line, content) in enumerate(glossary_lines):
        match = MOBILE_GLOSSARY_ENTRY_RE.fullmatch(content)
        if match is not None:
            explanation_parts = [match.group("explanation")]
            cursor = index + 1
            while cursor < len(glossary_lines):
                _, continuation = glossary_lines[cursor]
                if (
                    not continuation.strip()
                    or MOBILE_GLOSSARY_ENTRY_RE.fullmatch(continuation)
                    or normalized_heading(continuation) is not None
                    or not continuation.startswith((" ", "\t"))
                ):
                    break
                explanation_parts.append(continuation.strip())
                cursor += 1
            entries.append(
                (
                    source_line,
                    match.group("term"),
                    " ".join(explanation_parts),
                )
            )
    if len(entries) < MIN_GLOSSARY_ENTRIES:
        raise ValidationFailure(
            f"CSV line {line}: '首次术语解释' requires at least "
            f"{MIN_GLOSSARY_ENTRIES} mobile-friendly bilingual bullet entries"
        )
    for source_line, term, explanation in entries:
        if not re.search(r"[A-Za-z]", term) or not re.search(
            r"[\u3400-\u9fff]", explanation
        ):
            raise ValidationFailure(
                f"CSV line {line}: terminology bullet on Markdown line "
                f"{source_line} must include the source-language term or "
                "abbreviation and a Chinese contextual explanation"
            )
        if len(re.sub(r"\s+", "", explanation)) < 12:
            raise ValidationFailure(
                f"CSV line {line}: terminology explanation on Markdown line "
                f"{source_line} is too short"
            )
    glossary_body = section_text(glossary_lines)
    if (
        re.search(r"(?:首次|第一次)出现", glossary_body) is None
        or "解释" not in glossary_body
    ):
        raise ValidationFailure(
            f"CSV line {line}: terminology guidance must state that new terms "
            "are explained at first occurrence"
        )

    abstract_lines = sections["摘要完整专业中文翻译"][2]
    all_abstract_blocks = parse_translation_blocks(
        abstract_lines,
        line=line,
        section_title="摘要完整专业中文翻译",
    )
    abstract_blocks = validate_contiguous_translation_codes(
        all_abstract_blocks,
        "Abstract",
        line=line,
        required=True,
    )
    if len(abstract_blocks) != len(all_abstract_blocks):
        raise ValidationFailure(
            f"CSV line {line}: abstract translation section may contain only "
            "Abstract/A-NN blocks"
        )
    abstract_chars = translation_character_count(abstract_blocks)
    if abstract_chars < MIN_ABSTRACT_TRANSLATION_CHARS:
        raise ValidationFailure(
            f"CSV line {line}: complete abstract translation is too short "
            f"({abstract_chars} < {MIN_ABSTRACT_TRANSLATION_CHARS})"
        )

    config_lines = sections["原文公开的实验配置"][2]
    config_body = section_text(config_lines)
    if ORIGINAL_LOCATION_RE.search(config_body) is None:
        raise ValidationFailure(
            f"CSV line {line}: experiment configuration requires an explicit "
            "paper page or section anchor"
        )
    has_code_source = bool(FIXED_SHA_URL_RE.search(config_body))
    has_code_absence = bool(
        "[未核验]" in config_body
        and re.search(r"(?:源码|代码)", config_body)
        and re.search(r"(?:未公开|未提供|无法确认|没有提供)", config_body)
    )
    if not (has_code_source or has_code_absence):
        raise ValidationFailure(
            f"CSV line {line}: experiment configuration requires a fixed-SHA "
            "source link or an explicit [未核验] code-availability statement"
        )

    config_rows = markdown_table_rows(config_lines)
    config_header = ["配置项", "公开值或做法", "来源锚点"]
    config_header_positions = [
        position
        for position, (_, cells) in enumerate(config_rows)
        if cells == config_header
    ]
    if len(config_header_positions) > 1:
        raise ValidationFailure(
            f"CSV line {line}: experiment configuration contains duplicate "
            "table headers"
        )
    if config_header_positions:
        config_entries = config_rows[config_header_positions[0] + 1 :]
        if len(config_entries) < MIN_EXPERIMENT_CONFIG_ROWS:
            raise ValidationFailure(
                f"CSV line {line}: table-form experiment configuration requires "
                f"at least {MIN_EXPERIMENT_CONFIG_ROWS} sourced rows"
            )
        for source_line, cells in config_entries:
            if len(cells) != 3 or any(not cell for cell in cells):
                raise ValidationFailure(
                    f"CSV line {line}: experiment configuration row on Markdown "
                    f"line {source_line} must fill all three columns"
                )
            if not source_evidence_is_specific(cells[2]):
                raise ValidationFailure(
                    f"CSV line {line}: experiment configuration row on Markdown "
                    f"line {source_line} needs a PDF/section/fixed-SHA anchor or "
                    "an explicit [未核验] absence"
                )
    else:
        config_bullets = mobile_config_entries(config_lines)
        if len(config_bullets) < MIN_EXPERIMENT_CONFIG_BULLETS:
            raise ValidationFailure(
                f"CSV line {line}: mobile experiment configuration requires at "
                f"least {MIN_EXPERIMENT_CONFIG_BULLETS} bold card-style bullets"
            )
        for source_line, _, body in config_bullets:
            if EVIDENCE_LABEL_RE.search(body) is None:
                raise ValidationFailure(
                    f"CSV line {line}: configuration bullet on Markdown line "
                    f"{source_line} needs a [论文], [源码], or [未核验] label"
                )
            if not source_evidence_is_specific(body):
                raise ValidationFailure(
                    f"CSV line {line}: configuration bullet on Markdown line "
                    f"{source_line} needs its own PDF/section/fixed-SHA anchor or "
                    "an explicit [未核验] absence"
                )

    process_lines = sections["原文公开的实验流程"][2]
    process_body = section_text(process_lines)
    if ORIGINAL_LOCATION_RE.search(process_body) is None:
        raise ValidationFailure(
            f"CSV line {line}: experiment flow requires an explicit paper page "
            "or section anchor"
        )
    experiment_source_context = config_body + "\n" + process_body
    if not (
        FIXED_SHA_URL_RE.search(experiment_source_context)
        or (
            "[未核验]" in experiment_source_context
            and re.search(r"(?:源码|代码)", experiment_source_context)
            and re.search(
                r"(?:未公开|未提供|无法确认|没有提供)",
                experiment_source_context,
            )
        )
    ):
        raise ValidationFailure(
            f"CSV line {line}: experiment flow requires a fixed-SHA link or an "
            "explicit [未核验] code-availability statement"
        )
    flow_steps = numbered_flow_entries(process_lines)
    if len(flow_steps) < MIN_EXPERIMENT_FLOW_STEPS:
        raise ValidationFailure(
            f"CSV line {line}: experiment flow requires at least "
            f"{MIN_EXPERIMENT_FLOW_STEPS} numbered, sourced steps"
        )
    if [int(match.group("number")) for _, match, _ in flow_steps] != list(
        range(1, len(flow_steps) + 1)
    ):
        raise ValidationFailure(
            f"CSV line {line}: experiment flow step numbers must be contiguous "
            "from 1"
        )
    flow_labels = "；".join(match.group("label") for _, match, _ in flow_steps)
    semantic_families = (
        r"(?:数据|标注|预处理|准备)",
        r"(?:预训练|训练|微调|优化)",
        r"(?:保存|验证|选模|检查点|checkpoint)",
        r"(?:推理|后处理|任务)",
        r"(?:评测|测试|消融|迁移)",
    )
    if any(
        re.search(pattern, flow_labels, re.IGNORECASE) is None
        for pattern in semantic_families
    ):
        raise ValidationFailure(
            f"CSV line {line}: experiment flow must cover data preparation, "
            "training, checkpoint/validation, inference, and evaluation semantics"
        )
    for source_line, _, body in flow_steps:
        if EVIDENCE_LABEL_RE.search(body) is None:
            raise ValidationFailure(
                f"CSV line {line}: experiment flow step on Markdown line "
                f"{source_line} needs a [论文], [源码], or [未核验] label"
            )
        if not source_evidence_is_specific(body):
            raise ValidationFailure(
                f"CSV line {line}: experiment flow step on Markdown line "
                f"{source_line} needs its own PDF/section/fixed-SHA anchor or "
                "an explicit [未核验] absence"
            )

    conclusion_lines = sections["原文结论完整翻译"][2]
    conclusion_blocks = parse_translation_blocks(
        conclusion_lines,
        line=line,
        section_title="原文结论完整翻译",
    )
    conclusion_family = validate_contiguous_translation_codes(
        conclusion_blocks,
        "Conclusion",
        line=line,
        required=True,
    )
    if len(conclusion_family) != len(conclusion_blocks):
        raise ValidationFailure(
            f"CSV line {line}: conclusion translation section may contain only "
            "Conclusion/C-NN blocks"
        )
    conclusion_chars = translation_character_count(conclusion_family)
    if conclusion_chars < MIN_CONCLUSION_TRANSLATION_CHARS:
        raise ValidationFailure(
            f"CSV line {line}: complete conclusion translation is too short "
            f"({conclusion_chars} < {MIN_CONCLUSION_TRANSLATION_CHARS})"
        )
    conclusion_source_sections = {
        str(block["source_section"]) for block in conclusion_family
    }
    has_named_conclusion = any(
        section.casefold() == "conclusion"
        for section in conclusion_source_sections
    )
    if not has_named_conclusion:
        conclusion_missing_declarations = labeled_paragraphs(
            conclusion_lines,
            MISSING_SOURCE_SECTION_LABEL,
        )
        alternative_names = {
            section.casefold() for section in conclusion_source_sections
        }
        has_precise_conclusion_declaration = any(
            re.search(
                r"(?:未单列|没有单列|未设置|没有独立|无独立)",
                declaration,
            )
            and re.search(r"(?:Conclusion|结论)", declaration, re.IGNORECASE)
            and any(
                name in declaration.casefold()
                for name in alternative_names
            )
            and re.search(
                r"(?:不代写|不补写|不虚构|不伪造|不冒充|不改写)",
                declaration,
            )
            for declaration in conclusion_missing_declarations
        )
        if not has_precise_conclusion_declaration:
            actual_sections = ", ".join(sorted(conclusion_source_sections))
            raise ValidationFailure(
                f"CSV line {line}: a paper without a named Conclusion must add "
                f"a precise {MISSING_SOURCE_SECTION_LABEL} naming the real "
                f"closing section ({actual_sections}) and promising not to "
                "invent or relabel author conclusions"
            )

    outlook_lines = sections["原文局限与展望完整翻译"][2]
    outlook_body = section_text(outlook_lines)
    outlook_blocks = parse_translation_blocks(
        outlook_lines,
        line=line,
        section_title="原文局限与展望完整翻译",
    )
    limitation_blocks = validate_contiguous_translation_codes(
        outlook_blocks,
        "Limitations",
        line=line,
        required=False,
    )
    future_blocks = validate_contiguous_translation_codes(
        outlook_blocks,
        "Future Work",
        line=line,
        required=False,
    )
    if len(limitation_blocks) + len(future_blocks) != len(outlook_blocks):
        raise ValidationFailure(
            f"CSV line {line}: limitation/outlook section may contain only "
            "Limitations/L-NN and Future Work/O-NN blocks"
        )
    missing_lines = labeled_paragraphs(
        outlook_lines,
        MISSING_SOURCE_SECTION_LABEL,
    )
    for missing_line in missing_lines:
        if (
            not re.search(
                r"(?:未单列|没有单列|未提供|没有独立|无独立)",
                missing_line,
            )
            or not re.search(r"(?:不代写|不补写|不虚构)", missing_line)
        ):
            raise ValidationFailure(
                f"CSV line {line}: {MISSING_SOURCE_SECTION_LABEL} must identify "
                "the absent source section and promise not to invent author views"
            )
    has_limitation_absence = any(
        re.search(r"(?:Limitations?|局限)", content, re.IGNORECASE)
        for content in missing_lines
    )
    has_future_absence = any(
        re.search(r"(?:Future Work|Outlook|未来工作|展望)", content, re.IGNORECASE)
        for content in missing_lines
    )
    if not limitation_blocks and not has_limitation_absence:
        raise ValidationFailure(
            f"CSV line {line}: translate source limitations or add a precise "
            f"{MISSING_SOURCE_SECTION_LABEL}"
        )
    if not future_blocks and not has_future_absence:
        raise ValidationFailure(
            f"CSV line {line}: translate source Future Work or add a precise "
            f"{MISSING_SOURCE_SECTION_LABEL}"
        )
    for family, blocks in (
        ("Limitations", limitation_blocks),
        ("Future Work", future_blocks),
    ):
        if blocks and translation_character_count(blocks) < 30:
            raise ValidationFailure(
                f"CSV line {line}: {family} translation is too short to be complete"
            )
    if READER_ANALYSIS_LABEL in outlook_body or "[判断]" in outlook_body:
        raise ValidationFailure(
            f"CSV line {line}: source limitation/outlook translation must not "
            "mix in [笔记解释] or [判断]"
        )

    analysis_lines = sections["笔记分析与研究启发"][2]
    analysis_body = section_text(analysis_lines)
    if ORIGINAL_TRANSLATION_LABEL in analysis_body:
        raise ValidationFailure(
            f"CSV line {line}: '笔记分析与研究启发' must not contain "
            "[原文翻译]"
        )
    if READER_ANALYSIS_LABEL not in analysis_body or "[判断]" not in analysis_body:
        raise ValidationFailure(
            f"CSV line {line}: '笔记分析与研究启发' requires both "
            "[笔记解释] and [判断]"
        )
    if meaningful_character_count(analysis_lines) < 80:
        raise ValidationFailure(
            f"CSV line {line}: '笔记分析与研究启发' is too short"
        )


def validate_architecture_reading(
    note_path: Path,
    line: str,
    *,
    structure: MarkdownStructure,
    code_audit_status: str | None = None,
    repo_commit: str = "",
    repo_url: str = "",
) -> None:
    """Require an evidence-grounded architecture and innovation explanation."""

    relative_note = note_path.relative_to(ROOT).as_posix()
    sections = visible_reading_sections(structure)
    if ARCHITECTURE_SUBSECTION_TITLE not in sections:
        raise ValidationFailure(
            f"CSV line {line}: note {relative_note!r} is missing required "
            f"architecture section {ARCHITECTURE_SUBSECTION_TITLE!r}"
        )

    level, architecture_line, architecture_lines = sections[
        ARCHITECTURE_SUBSECTION_TITLE
    ]
    if level != 3:
        raise ValidationFailure(
            f"CSV line {line}: {ARCHITECTURE_SUBSECTION_TITLE!r} on Markdown "
            f"line {architecture_line} must be an H3"
        )

    major_lines = {
        content.strip(): source_line
        for source_line, content in structure.top_level_lines
        if content.strip() in REQUIRED_NOTE_HEADINGS
    }
    if not (
        major_lines[REQUIRED_NOTE_HEADINGS[0]]
        < architecture_line
        < major_lines[REQUIRED_NOTE_HEADINGS[1]]
    ):
        raise ValidationFailure(
            f"CSV line {line}: {ARCHITECTURE_SUBSECTION_TITLE!r} must appear "
            "inside Section 1 before the formula section"
        )

    preceding_h2: str | None = None
    for source_line, content in structure.top_level_lines:
        if source_line >= architecture_line:
            break
        parsed = normalized_heading(content)
        if parsed is not None and parsed[0] == 2:
            preceding_h2 = content.strip()
    if preceding_h2 != REQUIRED_NOTE_HEADINGS[0]:
        raise ValidationFailure(
            f"CSV line {line}: {ARCHITECTURE_SUBSECTION_TITLE!r} must be a "
            "direct H3 child of Section 1"
        )

    if markdown_table_rows(architecture_lines) or any(
        HTML_TABLE_TAG_RE.search(content)
        for _, content in architecture_lines
    ):
        raise ValidationFailure(
            f"CSV line {line}: architecture explanation must use vertical "
            "mobile-friendly cards; Markdown tables are prohibited in this section"
        )

    module_positions: list[tuple[int, int, str, int, str]] = []
    for index, (source_line, content) in enumerate(architecture_lines):
        parsed = normalized_heading(content)
        if parsed is None:
            continue
        heading_level, title = parsed
        heading_match = ARCHITECTURE_CARD_HEADING_RE.fullmatch(title)
        if heading_level == 4 and heading_match is not None:
            module_positions.append(
                (
                    index,
                    source_line,
                    title,
                    int(heading_match.group("number")),
                    heading_match.group("name").strip(),
                )
            )
    if not module_positions:
        raise ValidationFailure(
            f"CSV line {line}: {ARCHITECTURE_SUBSECTION_TITLE!r} requires at "
            "least one H4 '创新模块 N：名称' or "
            "'创新单元 N：名称' card"
        )
    module_names = [
        name.casefold() for _, _, _, _, name in module_positions
    ]
    if len(module_names) != len(set(module_names)):
        raise ValidationFailure(
            f"CSV line {line}: architecture card names must be unique"
        )
    module_numbers = [number for _, _, _, number, _ in module_positions]
    if module_numbers != list(range(1, len(module_numbers) + 1)):
        raise ValidationFailure(
            f"CSV line {line}: architecture card numbers must be unique and "
            "continuous from 1"
        )

    overview_lines = architecture_lines[: module_positions[0][0]]
    overview_fields = anchored_field_paragraphs(
        overview_lines,
        ARCHITECTURE_OVERVIEW_LABELS,
    )
    overview_minimum_chars = {
        "原方法瓶颈": 40,
        "主干网络与基线": 40,
        "继承与新增边界": 40,
        "端到端信息流": 50,
        "总体训练方式": 40,
    }
    for field in ARCHITECTURE_OVERVIEW_LABELS:
        label = f"**{field}：**"
        paragraphs = overview_fields[field]
        if len(paragraphs) != 1:
            raise ValidationFailure(
                f"CSV line {line}: architecture overview requires exactly one "
                f"paragraph beginning with {label}"
            )
        paragraph = paragraphs[0]
        if plain_prose_character_count(paragraph) < overview_minimum_chars[field]:
            raise ValidationFailure(
                f"CSV line {line}: architecture overview field {field!r} "
                "is too short to explain the method"
            )
        if EVIDENCE_LABEL_RE.search(paragraph) is None:
            raise ValidationFailure(
                f"CSV line {line}: architecture overview field {field!r} "
                "requires a [论文], [源码], or [未核验] label"
            )
        if not source_evidence_is_specific(paragraph):
            raise ValidationFailure(
                f"CSV line {line}: architecture overview field {field!r} "
                "requires its own PDF/section/fixed-SHA anchor or an explicit "
                "[未核验] absence"
            )

    minimum_field_chars = {
        "位置与接口": 12,
        "输入": 8,
        "内部变换": 18,
        "输出": 8,
        "为什么这样设计": 24,
        "训练信号": 16,
        "作用与证据": 20,
        "论文位置": 8,
        "源码入口": 8,
    }
    for position, (start_index, source_line, title, _, _) in enumerate(
        module_positions
    ):
        card_end = len(architecture_lines)
        if position + 1 < len(module_positions):
            card_end = module_positions[position + 1][0]
        for index in range(start_index + 1, card_end):
            parsed = normalized_heading(architecture_lines[index][1])
            if parsed is not None and parsed[0] <= 4:
                card_end = index
                break
        card_lines = architecture_lines[start_index + 1 : card_end]
        parsed_card_fields = anchored_field_paragraphs(
            card_lines,
            ARCHITECTURE_MODULE_FIELDS,
        )
        card_fields: dict[str, str] = {}
        for field in ARCHITECTURE_MODULE_FIELDS:
            label = f"**{field}：**"
            paragraphs = parsed_card_fields[field]
            if len(paragraphs) != 1:
                raise ValidationFailure(
                    f"CSV line {line}: architecture card {title!r} on "
                    f"Markdown line {source_line} requires exactly one "
                    f"paragraph beginning with {label}"
                )
            paragraph = paragraphs[0]
            value = paragraph.split(label, 1)[1]
            if plain_prose_character_count(value) < minimum_field_chars[field]:
                raise ValidationFailure(
                    f"CSV line {line}: architecture card {title!r} field "
                    f"{field!r} is too short"
                )
            card_fields[field] = paragraph

        why_text = card_fields["为什么这样设计"]
        causal_language = re.search(
            r"(?:因为|因此|为了|解决|避免|针对|瓶颈|动机|使得|从而)",
            why_text,
        )
        paper_motivation = (
            has_evidence_token(why_text, "论文")
            and ORIGINAL_LOCATION_RE.search(why_text)
        )
        reconstructed_motivation = (
            has_evidence_token(why_text, "判断")
            and re.search(r"(?:笔记|本文笔记).*(?:推断|判断|因果重建)", why_text)
            and re.search(r"(?:前述|上述|原方法|瓶颈|失败模式)", why_text)
            and re.search(
                r"(?:不是作者原句|并非作者(?:的)?(?:原句|明确(?:说明|表述|动机))"
                r"|原文未(?:直接|明确)(?:说明|表述|给出))",
                why_text,
            )
        )
        if causal_language is None or not (
            paper_motivation or reconstructed_motivation
        ):
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} must explain "
                "a causal rationale as either [论文] with a source anchor or "
                "[判断] explicitly marked as the note's bottleneck-based reconstruction"
            )

        training_text = card_fields["训练信号"]
        if (
            EVIDENCE_LABEL_RE.search(training_text) is None
            or not source_evidence_is_specific(training_text)
        ):
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} training signal "
                "requires an evidence label and a specific source or absence"
            )

        evidence_text = card_fields["作用与证据"]
        positive_intervention = re.search(
            r"(?:加入|移除|去掉|删除|替换|启用|关闭|有无|"
            r"\bwith(?:out)?\b|相比|相对|优于|劣于|从.+?到|→)",
            evidence_text,
            re.IGNORECASE,
        )
        whole_system_substitution = (
            re.search(
                r"(?:没有|未做|未提供|并非|不是|无).{0,30}"
                r"(?:独立)?(?:消融|受控(?:对照|比较))",
                evidence_text,
            )
            and re.search(r"(?:整套系统|全模型|完整模型|整条路线)", evidence_text)
        )
        empirical_evidence = (
            has_evidence_token(evidence_text, "论文")
            and source_evidence_is_specific(evidence_text)
            and re.search(r"(?:消融|受控对照|受控比较)", evidence_text)
            and re.search(
                r"(?:Table|表|Figure|图)\s*[A-Z]?\d+",
                evidence_text,
                re.IGNORECASE,
            )
            and re.search(
                r"(?:\d+(?:\.\d+)?\s*(?:%|mIoU|AP|AR|GB|ms|FPS|分|点)"
                r"|提高|提升|下降|降低|改善|优于|增加|减少|恶化)",
                evidence_text,
                re.IGNORECASE,
            )
            and positive_intervention
            and not whole_system_substitution
        )
        explicit_absence = (
            has_evidence_token(evidence_text, "未核验")
            and re.search(
                r"(?:原文|论文).*(?:未提供|未报告|未给出).*独立"
                r"(?:消融|对照|比较)",
                evidence_text,
            )
            and re.search(r"(?:不能|无法).*单独归因", evidence_text)
        )
        if not (empirical_evidence or explicit_absence):
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} must map its "
                "claimed role to a numbered Table/Figure ablation or controlled "
                "comparison "
                "with a result, or use [未核验] to state that no independent "
                "evidence exists and the effect cannot be attributed separately"
            )

        paper_text = card_fields["论文位置"]
        if (
            not has_evidence_token(paper_text, "论文")
            or ORIGINAL_LOCATION_RE.search(paper_text) is None
        ):
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} requires a "
                "[论文] PDF/section anchor"
            )

        source_text = card_fields["源码入口"]
        source_absence = (
            "[未核验]" in source_text
            and re.search(r"(?:源码|代码)", source_text)
            and re.search(
                r"(?:未公开|未提供|没有提供|无法确认|未找到)",
                source_text,
            )
        )
        source_pending = (
            "[未核验]" in source_text
            and re.search(
                r"(?:尚未|还未|未完成).*(?:审计|核对|检查)",
                source_text,
            )
        )
        fixed_sha_links = FIXED_SHA_URL_RE.findall(source_text)
        if fixed_sha_links and not has_evidence_token(source_text, "源码"):
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} fixed-SHA "
                "entry requires a [源码] provenance label"
            )
        if code_audit_status == "Audited" and not fixed_sha_links:
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} cannot claim "
                "source is unavailable or pending when index status is Audited"
            )
        if code_audit_status == "NoOfficialCode" and not source_absence:
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} must use an "
                "explicit [未核验] official-code absence when index status is "
                "NoOfficialCode"
            )
        if (
            code_audit_status == "NotAudited"
            and not (fixed_sha_links or source_pending)
        ):
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} must say the "
                "source is not yet audited, rather than claiming it does not exist"
            )
        expected_repo_identity = github_repo_identity(repo_url) if repo_url else None
        normalized_commit = repo_commit.casefold()
        matching_official_links: list[str] = []
        for link in fixed_sha_links:
            sha_match = re.search(
                r"/(?:blob|tree)/([0-9a-fA-F]{40})(?:/|$)",
                link,
            )
            if sha_match is None:
                continue
            link_commit = sha_match.group(1).casefold()
            link_repo_identity = github_repo_identity(link)
            if (
                (not normalized_commit or link_commit == normalized_commit)
                and (
                    expected_repo_identity is None
                    or link_repo_identity == expected_repo_identity
                )
            ):
                matching_official_links.append(link)
        if (repo_commit or repo_url) and fixed_sha_links and not matching_official_links:
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} source link "
                "must match the official GitHub repository and repo_commit "
                "recorded in index/papers.csv"
            )
        if not (fixed_sha_links or source_absence or source_pending):
            raise ValidationFailure(
                f"CSV line {line}: architecture card {title!r} requires a "
                "fixed-SHA source link or an explicit [未核验] no-code statement"
            )


def safe_note_path(value: str, line: str) -> Path:
    pure = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        pure.is_absolute()
        or "\\" in value
        or ".." in pure.parts
        or windows_path.drive
        or windows_path.root
        or any(
            PureWindowsPath(part).drive or PureWindowsPath(part).root
            for part in pure.parts
        )
        or pure.suffix.lower() != ".md"
        or not pure.parts
        or pure.parts[0] != "notes"
    ):
        raise ValidationFailure(f"CSV line {line}: unsafe note_path {value!r}")
    path = ROOT.joinpath(*pure.parts).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise ValidationFailure(
            f"CSV line {line}: note_path escapes repository root: {value!r}"
        ) from exc
    if not path.is_file():
        raise ValidationFailure(f"CSV line {line}: note does not exist: {value}")
    return path


def png_dimensions(path: Path) -> tuple[int, int]:
    """Return PNG dimensions without adding an image-library CI dependency."""

    with path.open("rb") as handle:
        header = handle.read(24)
    if (
        len(header) != 24
        or header[:8] != b"\x89PNG\r\n\x1a\n"
        or header[12:16] != b"IHDR"
    ):
        raise ValidationFailure(
            f"invalid PNG signature or IHDR: {path.relative_to(ROOT).as_posix()}"
        )
    return struct.unpack(">II", header[16:24])


def validate_formula_source(path: Path, line: str) -> dict[str, str]:
    """Validate canonical fragment-only TeX and return normalized blocks."""

    raw = path.read_bytes()
    if not raw or len(raw) > 64 * 1024:
        raise ValidationFailure(
            f"CSV line {line}: formula TeX source must be 1 byte–64 KiB"
        )
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw or b"\x00" in raw:
        raise ValidationFailure(
            f"CSV line {line}: formula TeX source must be BOM-free UTF-8 with LF endings"
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationFailure(
            f"CSV line {line}: formula TeX source is not strict UTF-8"
        ) from exc

    dangerous = (
        r"\documentclass",
        r"\usepackage",
        r"\begin{document}",
        r"\input",
        r"\include",
        r"\openout",
        r"\write",
        r"\immediate",
    )
    for command in dangerous:
        if command in text:
            raise ValidationFailure(
                f"CSV line {line}: formula TeX source contains forbidden command "
                f"{command!r}"
            )

    blocks = {
        match.group("name"): match.group("body").strip()
        for match in FORMULA_BLOCK_RE.finditer(text)
    }
    if not blocks:
        raise ValidationFailure(
            f"CSV line {line}: formula TeX source contains no named formula blocks"
        )
    begin_count = len(re.findall(r"^% BEGIN ", text, re.MULTILINE))
    end_count = len(re.findall(r"^% END ", text, re.MULTILINE))
    if begin_count != len(blocks) or end_count != len(blocks):
        raise ValidationFailure(
            f"CSV line {line}: formula TeX contains unmatched or duplicate block markers"
        )
    return blocks


def validate_note_assets(
    note_path: Path,
    line: str,
    *,
    paper_url: str,
    structure: MarkdownStructure,
) -> None:
    """Validate visible paper figures, tables, attributions, and equations."""

    paper_images: list[tuple[Path, int, str]] = []
    formula_images: list[FormulaPicture] = []
    root = ROOT.resolve()
    expected_asset_root = ("assets", "notes", note_path.stem)
    expected_formula_root = (*expected_asset_root, "formulas")
    formula_directory = ROOT.joinpath(*expected_formula_root)
    formula_source_path = formula_directory / FORMULA_SOURCE_FILE
    top_text = structure.top_level_text
    rendered_text = structure.rendered_text
    top_lines = structure.top_level_lines

    rendered_formula_pictures: list[tuple[int, re.Match[str]]] = []
    for source_line, rendered_line in structure.rendered_lines:
        picture_match = FORMULA_PICTURE_RE.fullmatch(rendered_line)
        if picture_match is not None:
            rendered_formula_pictures.append((source_line, picture_match))
            continue
        if (
            HTML_IMAGE_RE.search(rendered_line)
            or HTML_PICTURE_TAG_RE.search(rendered_line)
        ):
            raise ValidationFailure(
                f"CSV line {line}: Markdown line {source_line} contains HTML image "
                "markup outside the exact theme-aware formula <picture> format"
            )

    rendered_image_count = len(MARKDOWN_IMAGE_RE.findall(rendered_text))
    top_level_image_count = len(MARKDOWN_IMAGE_RE.findall(top_text))
    if rendered_image_count != top_level_image_count:
        raise ValidationFailure(
            f"CSV line {line}: note images must remain visible outside <details>"
        )
    top_level_formula_picture_count = sum(
        FORMULA_PICTURE_RE.fullmatch(item) is not None for _, item in top_lines
    )
    if len(rendered_formula_pictures) != top_level_formula_picture_count:
        raise ValidationFailure(
            f"CSV line {line}: formula pictures must remain visible outside <details>"
        )

    paper_source_label_count = sum(
        item.count("**原图出处：**") for _, item in top_lines
    )
    formula_source_label_count = sum(
        item.count(FORMULA_SOURCE_LABEL) for _, item in top_lines
    )
    source_kinds: list[tuple[int, str]] = []

    def source_block_after(
        line_index: int,
        source_line: int,
        expected_label: str,
    ) -> str:
        next_index = line_index + 1
        while next_index < len(top_lines) and not top_lines[next_index][1].strip():
            next_index += 1
        if next_index >= len(top_lines) or not top_lines[next_index][
            1
        ].lstrip().startswith(expected_label):
            raise ValidationFailure(
                f"CSV line {line}: image on Markdown line {source_line} must be "
                f"followed immediately by a {expected_label!r} block"
            )

        source_block_lines: list[str] = []
        while (
            next_index < len(top_lines)
            and top_lines[next_index][1].lstrip().startswith(">")
        ):
            source_block_lines.append(top_lines[next_index][1])
            next_index += 1
        return "\n".join(source_block_lines)

    def formula_source_anchor(
        source_block: str,
        source_line: int,
    ) -> tuple[int, int]:
        source_links: list[tuple[str, SplitResult]] = []
        for link_match in MARKDOWN_LINK_RE.finditer(source_block):
            raw_link_target = link_match.group("target").strip("<>")
            parsed_link = urlsplit(raw_link_target)
            link_parts = PurePosixPath(unquote(parsed_link.path)).parts
            if link_parts[-2:] == ("formulas", FORMULA_SOURCE_FILE):
                source_links.append((raw_link_target, parsed_link))
        if len(source_links) != 1:
            raise ValidationFailure(
                f"CSV line {line}: formula attribution after Markdown line "
                f"{source_line} must contain exactly one anchored "
                f"'formulas/{FORMULA_SOURCE_FILE}#Lbegin-Lend' link"
            )
        raw_source_target, parsed_source_link = source_links[0]
        if parsed_source_link.scheme or parsed_source_link.netloc:
            raise ValidationFailure(
                f"CSV line {line}: formula source after Markdown line "
                f"{source_line} must be a local link: {raw_source_target!r}"
            )
        resolved_source_target = (
            note_path.parent / unquote(parsed_source_link.path)
        ).resolve()
        if resolved_source_target != formula_source_path.resolve():
            raise ValidationFailure(
                f"CSV line {line}: formula source after Markdown line "
                f"{source_line} must point to the current note's "
                f"formulas/{FORMULA_SOURCE_FILE}"
            )
        fragment_match = FORMULA_SOURCE_FRAGMENT_RE.fullmatch(
            parsed_source_link.fragment
        )
        if fragment_match is None:
            raise ValidationFailure(
                f"CSV line {line}: formula source after Markdown line "
                f"{source_line} requires an exact #Lbegin-Lend fragment"
            )
        anchor_begin = int(fragment_match.group("begin"))
        anchor_end = int(fragment_match.group("end"))
        if anchor_begin > anchor_end:
            raise ValidationFailure(
                f"CSV line {line}: formula source after Markdown line "
                f"{source_line} has a reversed line anchor"
            )
        if not (
            paper_url in source_block
            or "**[源码]" in source_block
            or "**[判断]" in source_block
        ):
            raise ValidationFailure(
                f"CSV line {line}: formula attribution after Markdown line "
                f"{source_line} needs official-paper, [源码], or [判断] provenance"
            )
        return anchor_begin, anchor_end

    for line_index, (source_line, rendered_line) in enumerate(top_lines):
        matches = list(MARKDOWN_IMAGE_RE.finditer(rendered_line))
        if len(matches) > 1:
            raise ValidationFailure(
                f"CSV line {line}: Markdown line {source_line} contains multiple "
                "images; put each figure/table on its own line"
            )
        picture_match = FORMULA_PICTURE_RE.fullmatch(rendered_line)
        if picture_match is not None:
            if matches:
                raise ValidationFailure(
                    f"CSV line {line}: Markdown line {source_line} cannot mix a "
                    "formula <picture> with Markdown image syntax"
                )

            alt = picture_match.group("alt").strip()
            if len(alt.removeprefix(FORMULA_ALT_PREFIX).strip()) < 8:
                raise ValidationFailure(
                    f"CSV line {line}: formula picture on Markdown line "
                    f"{source_line} requires descriptive alt text beginning "
                    f"with {FORMULA_ALT_PREFIX!r}"
                )

            resolved_themes: dict[str, tuple[Path, Path]] = {}
            for theme in ("light", "dark"):
                raw_target = picture_match.group(theme)
                parsed = urlsplit(raw_target)
                if (
                    parsed.scheme
                    or parsed.netloc
                    or parsed.query
                    or parsed.fragment
                ):
                    raise ValidationFailure(
                        f"CSV line {line}: formula {theme} image must be a plain "
                        f"local path: {raw_target!r}"
                    )

                decoded_target = unquote(parsed.path)
                resolved = (note_path.parent / decoded_target).resolve()
                try:
                    relative = resolved.relative_to(root)
                except ValueError as exc:
                    raise ValidationFailure(
                        f"CSV line {line}: formula image escapes repository root: "
                        f"{raw_target!r}"
                    ) from exc
                if not resolved.is_file():
                    raise ValidationFailure(
                        f"CSV line {line}: local formula image does not exist: "
                        f"{raw_target!r}"
                    )
                if (
                    relative.parts[:-1] != expected_formula_root
                    or resolved.suffix.casefold() != ".png"
                ):
                    raise ValidationFailure(
                        f"CSV line {line}: formula images must live directly under "
                        f"{('/'.join(expected_formula_root))}/ as PNG pairs: "
                        f"{relative.as_posix()}"
                    )
                expected_suffix = f"-{theme}"
                if (
                    not resolved.stem.endswith(expected_suffix)
                    or not re.fullmatch(
                        r"[a-z0-9-]+",
                        resolved.stem[: -len(expected_suffix)],
                    )
                ):
                    raise ValidationFailure(
                        f"CSV line {line}: formula {theme} image must end in "
                        f"{expected_suffix}.png: {relative.as_posix()}"
                    )
                image_size = resolved.stat().st_size
                if not 1024 <= image_size <= 3 * 1024 * 1024:
                    raise ValidationFailure(
                        f"CSV line {line}: formula image must be 1 KiB–3 MiB: "
                        f"{relative.as_posix()} ({image_size} bytes)"
                    )
                resolved_themes[theme] = (resolved, relative)

            light_path, light_relative = resolved_themes["light"]
            dark_path, dark_relative = resolved_themes["dark"]
            light_name = light_path.stem.removesuffix("-light")
            dark_name = dark_path.stem.removesuffix("-dark")
            if light_name != dark_name:
                raise ValidationFailure(
                    f"CSV line {line}: formula light/dark images on Markdown line "
                    f"{source_line} do not form one named pair"
                )

            display_width = int(picture_match.group("width"))
            display_height = int(picture_match.group("height"))
            if not (
                FORMULA_MIN_DISPLAY_WIDTH
                <= display_width
                <= FORMULA_MAX_DISPLAY_WIDTH
                and FORMULA_MIN_DISPLAY_HEIGHT
                <= display_height
                <= FORMULA_MAX_DISPLAY_HEIGHT
            ):
                raise ValidationFailure(
                    f"CSV line {line}: formula display size on Markdown line "
                    f"{source_line} must be {FORMULA_MIN_DISPLAY_WIDTH}–"
                    f"{FORMULA_MAX_DISPLAY_WIDTH} px wide and "
                    f"{FORMULA_MIN_DISPLAY_HEIGHT}–{FORMULA_MAX_DISPLAY_HEIGHT} "
                    f"px high, got {display_width}x{display_height}"
                )

            light_dimensions = png_dimensions(light_path)
            dark_dimensions = png_dimensions(dark_path)
            if light_dimensions != dark_dimensions:
                raise ValidationFailure(
                    f"CSV line {line}: formula light/dark PNG dimensions differ: "
                    f"{light_relative.as_posix()} is "
                    f"{light_dimensions[0]}x{light_dimensions[1]}, "
                    f"{dark_relative.as_posix()} is "
                    f"{dark_dimensions[0]}x{dark_dimensions[1]}"
                )
            pixel_width, pixel_height = light_dimensions
            if (
                abs(pixel_width - 2 * display_width) > 1
                or abs(pixel_height - 2 * display_height) > 1
            ):
                raise ValidationFailure(
                    f"CSV line {line}: formula PNG pair on Markdown line "
                    f"{source_line} must have 2x pixel density; declared "
                    f"{display_width}x{display_height}, stored "
                    f"{pixel_width}x{pixel_height}"
                )

            source_block = source_block_after(
                line_index,
                source_line,
                f"> {FORMULA_SOURCE_LABEL}",
            )
            anchor_begin, anchor_end = formula_source_anchor(
                source_block,
                source_line,
            )
            formula_images.append(
                FormulaPicture(
                    name=light_name,
                    light_path=light_path,
                    dark_path=dark_path,
                    source_line=source_line,
                    anchor_begin=anchor_begin,
                    anchor_end=anchor_end,
                    display_width=display_width,
                    display_height=display_height,
                )
            )
            continue

        for match in matches:
            alt = match.group("alt").strip()
            if not alt:
                raise ValidationFailure(
                    f"CSV line {line}: every note image requires descriptive alt text"
                )

            raw_target = match.group("target").strip("<>")
            parsed = urlsplit(raw_target)
            if parsed.scheme or parsed.netloc:
                raise ValidationFailure(
                    f"CSV line {line}: indexed notes cannot hotlink images; "
                    f"store {raw_target!r} under assets/notes/"
                )

            decoded_target = unquote(parsed.path)
            resolved = (note_path.parent / decoded_target).resolve()
            try:
                relative = resolved.relative_to(root)
            except ValueError as exc:
                raise ValidationFailure(
                    f"CSV line {line}: image escapes repository root: {raw_target!r}"
                ) from exc

            if not resolved.is_file():
                raise ValidationFailure(
                    f"CSV line {line}: local image does not exist: {raw_target!r}"
                )
            if relative.parts[:3] != expected_asset_root:
                raise ValidationFailure(
                    f"CSV line {line}: note images must live under the current note's "
                    f"asset directory {('/'.join(expected_asset_root))}/: "
                    f"{relative.as_posix()}"
                )

            is_formula = relative.parts[:4] == expected_formula_root
            if is_formula:
                raise ValidationFailure(
                    f"CSV line {line}: formula assets must use the exact compact "
                    "light/dark <picture> pair format, not Markdown image syntax"
                )
            if resolved.suffix.casefold() not in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".svg",
            }:
                raise ValidationFailure(
                    f"CSV line {line}: unsupported note image format: "
                    f"{relative.as_posix()}"
                )
            image_size = resolved.stat().st_size
            if not 1024 <= image_size <= 3 * 1024 * 1024:
                raise ValidationFailure(
                    f"CSV line {line}: note image must be 1 KiB–3 MiB: "
                    f"{relative.as_posix()} ({image_size} bytes)"
                )

            source_block = source_block_after(
                line_index,
                source_line,
                "> **原图出处：**",
            )

            has_figure = bool(FIGURE_ID_RE.search(source_block))
            has_table = bool(TABLE_ID_RE.search(source_block))
            if has_figure == has_table:
                raise ValidationFailure(
                    f"CSV line {line}: attribution after Markdown line {source_line} "
                    "must contain exactly one numeric Figure or Table identifier"
                )
            if not PDF_PAGE_RE.search(source_block):
                raise ValidationFailure(
                    f"CSV line {line}: attribution after Markdown line {source_line} "
                    "requires a numeric PDF page"
                )
            if paper_url not in source_block:
                raise ValidationFailure(
                    f"CSV line {line}: attribution after Markdown line {source_line} "
                    "must link the indexed official paper PDF"
                )
            if IMAGE_RIGHTS_NOTICE not in source_block:
                raise ValidationFailure(
                    f"CSV line {line}: attribution after Markdown line {source_line} "
                    f"must include the rights notice {IMAGE_RIGHTS_NOTICE!r}"
                )

            kind = "Figure" if has_figure else "Table"
            source_kinds.append((source_line, kind))
            paper_images.append((resolved, source_line, kind))

    if not paper_images:
        raise ValidationFailure(
            f"CSV line {line}: every deep-reading note requires locally stored, "
            "attributed paper figures and tables"
        )
    if paper_source_label_count != len(paper_images):
        raise ValidationFailure(
            f"CSV line {line}: every paper-image source label must correspond "
            f"one-to-one with a local paper image ({paper_source_label_count} labels, "
            f"{len(paper_images)} images)"
        )
    if formula_source_label_count != len(formula_images):
        raise ValidationFailure(
            f"CSV line {line}: every formula source label must correspond one-to-one "
            f"with a local formula PNG pair ({formula_source_label_count} labels, "
            f"{len(formula_images)} pairs)"
        )
    if formula_images:
        source_path = formula_source_path
        if not source_path.is_file():
            raise ValidationFailure(
                f"CSV line {line}: missing canonical formula source "
                f"{source_path.relative_to(ROOT).as_posix()}"
            )
        source_blocks = validate_formula_source(source_path, line)
        source_names = set(source_blocks)
        referenced_names = {picture.name for picture in formula_images}
        if len(referenced_names) != len(formula_images):
            raise ValidationFailure(
                f"CSV line {line}: every formula TeX block must be referenced by "
                "exactly one light/dark picture pair"
            )
        expected_disk_names = {
            f"{name}-{theme}.png"
            for name in referenced_names
            for theme in ("light", "dark")
        }
        disk_names = {path.name for path in formula_directory.glob("*.png")}
        if (
            referenced_names != source_names
            or expected_disk_names != disk_names
        ):
            raise ValidationFailure(
                f"CSV line {line}: formula picture references, TeX blocks, and "
                "on-disk light/dark PNG pairs must match exactly; legacy base PNGs "
                "and extra or missing theme images are not allowed"
            )
        source_lines = source_path.read_text(encoding="utf-8").splitlines()
        for picture in formula_images:
            begin_marker = f"% BEGIN {picture.name}"
            end_marker = f"% END {picture.name}"
            anchor_is_exact = (
                picture.anchor_begin <= len(source_lines)
                and picture.anchor_end <= len(source_lines)
                and source_lines[picture.anchor_begin - 1].strip() == begin_marker
                and source_lines[picture.anchor_end - 1].strip() == end_marker
            )
            if not anchor_is_exact:
                raise ValidationFailure(
                    f"CSV line {line}: formula source link after Markdown line "
                    f"{picture.source_line} does not exactly anchor {begin_marker!r} "
                    f"through {end_marker!r}"
                )
        manifest_path = formula_directory / FORMULA_MANIFEST_FILE
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValidationFailure(
                f"CSV line {line}: formula manifest is missing or invalid"
            ) from exc
        manifest_formulas = manifest.get("formulas")
        if manifest.get("version") != 2 or not isinstance(manifest_formulas, dict):
            raise ValidationFailure(
                f"CSV line {line}: unsupported formula manifest schema"
            )
        if set(manifest_formulas) != referenced_names:
            raise ValidationFailure(
                f"CSV line {line}: formula manifest stems do not match note assets"
            )
        pictures_by_name = {picture.name: picture for picture in formula_images}
        for name, body in source_blocks.items():
            entry = manifest_formulas.get(name)
            picture = pictures_by_name[name]
            width, height = png_dimensions(picture.light_path)
            expected_source_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
            expected_light_hash = hashlib.sha256(
                picture.light_path.read_bytes()
            ).hexdigest()
            expected_dark_hash = hashlib.sha256(
                picture.dark_path.read_bytes()
            ).hexdigest()
            if (
                not isinstance(entry, dict)
                or entry.get("source_sha256") != expected_source_hash
                or entry.get("light_png_sha256") != expected_light_hash
                or entry.get("dark_png_sha256") != expected_dark_hash
                or entry.get("pixel_width") != width
                or entry.get("pixel_height") != height
                or entry.get("display_width") != picture.display_width
                or entry.get("display_height") != picture.display_height
            ):
                raise ValidationFailure(
                    f"CSV line {line}: formula manifest entry {name!r} is stale"
                )

    heading_positions = {
        content.strip(): source_line
        for source_line, content in top_lines
        if content.strip() in REQUIRED_NOTE_HEADINGS
    }
    figure_section_start = heading_positions[REQUIRED_NOTE_HEADINGS[0]]
    formula_section_start = heading_positions[REQUIRED_NOTE_HEADINGS[1]]
    result_section_start = heading_positions[REQUIRED_NOTE_HEADINGS[2]]
    code_section_start = heading_positions[REQUIRED_NOTE_HEADINGS[3]]
    if not any(
        kind == "Figure" and figure_section_start < image_line < formula_section_start
        for image_line, kind in source_kinds
    ):
        raise ValidationFailure(
            f"CSV line {line}: Section 1 requires at least one attributed paper Figure"
        )
    if not any(
        kind == "Table" and result_section_start < image_line < code_section_start
        for image_line, kind in source_kinds
    ):
        raise ValidationFailure(
            f"CSV line {line}: Section 3 requires at least one attributed result Table"
        )

    numbered_labels = [
        (source_line, content)
        for source_line, content in top_lines
        if "**原文公式：**" in content
    ]
    unnumbered_labels = [
        (source_line, content)
        for source_line, content in top_lines
        if "**原文未编号公式：**" in content
    ]
    no_equation_labels = [
        (source_line, content)
        for source_line, content in top_lines
        if "**原文无必要公式：**" in content
    ]
    has_equations = bool(numbered_labels or unnumbered_labels)
    has_no_equations = bool(no_equation_labels)
    if has_equations == has_no_equations:
        raise ValidationFailure(
            f"CSV line {line}: choose exactly one formula mode: attributed original "
            "equations or an explicit no-indispensable-equation statement"
        )

    for source_line, _ in numbered_labels + unnumbered_labels + no_equation_labels:
        if not formula_section_start < source_line < result_section_start:
            raise ValidationFailure(
                f"CSV line {line}: original-formula declarations must appear in "
                f"Section 2, not Markdown line {source_line}"
            )

    for source_line, content in numbered_labels:
        if not NUMBERED_EQUATION_SOURCE_RE.search(content):
            raise ValidationFailure(
                f"CSV line {line}: numbered original formula on Markdown line "
                f"{source_line} requires a numeric Eq. identifier and PDF page"
            )
    for source_line, content in unnumbered_labels:
        if not UNNUMBERED_EQUATION_SOURCE_RE.search(content):
            raise ValidationFailure(
                f"CSV line {line}: unnumbered original formula on Markdown line "
                f"{source_line} requires a numeric PDF page"
            )

    if structure.top_level_math_blocks:
        raise ValidationFailure(
            f"CSV line {line}: indexed notes must not use live fenced math; "
            "render equations as cross-device formula PNG pairs"
        )

    if has_equations:
        if not formula_images:
            raise ValidationFailure(
                f"CSV line {line}: original equations require visible formula PNG pairs"
            )
        label_lines = sorted(
            source_line
            for source_line, _ in numbered_labels + unnumbered_labels
        )
        boundary_lines = sorted(
            source_line
            for source_line, content in top_lines
            if content.lstrip().startswith("#")
            or "**原文公式：**" in content
            or "**原文未编号公式：**" in content
        )
        for label_line in label_lines:
            next_boundary = next(
                (
                    boundary
                    for boundary in boundary_lines
                    if boundary > label_line
                ),
                10**9,
            )
            matching_images = [
                picture.source_line
                for picture in formula_images
                if label_line < picture.source_line < next_boundary
            ]
            if len(matching_images) != 1:
                raise ValidationFailure(
                    f"CSV line {line}: original formula label on Markdown line "
                    f"{label_line} must be followed by exactly one visible formula "
                    "PNG pair"
                )

    if formula_images:
        if top_text.count(FORMULA_IDENTITY_LEGEND) != 1:
            raise ValidationFailure(
                f"CSV line {line}: note with formulas requires exactly one variable "
                "identity legend that distinguishes field conventions, paper-defined "
                "symbols, and source/note rearrangements"
            )
        heading_lines = sorted(
            source_line
            for source_line, content in top_lines
            if content.lstrip().startswith("#")
        )
        for picture in formula_images:
            next_heading = next(
                (
                    heading_line
                    for heading_line in heading_lines
                    if heading_line > picture.source_line
                ),
                10**9,
            )
            teaching_block = "\n".join(
                content
                for source_line, content in top_lines
                if picture.source_line < source_line < next_heading
            )
            label_positions = [
                teaching_block.find(label) for label in FORMULA_TEACHING_LABELS
            ]
            if any(position < 0 for position in label_positions):
                missing = [
                    label
                    for label, position in zip(
                        FORMULA_TEACHING_LABELS, label_positions, strict=True
                    )
                    if position < 0
                ]
                raise ValidationFailure(
                    f"CSV line {line}: formula {picture.name!r} on Markdown line "
                    f"{picture.source_line} is missing beginner teaching fields: "
                    f"{', '.join(missing)}"
                )
            if label_positions != sorted(label_positions):
                raise ValidationFailure(
                    f"CSV line {line}: formula {picture.name!r} teaching fields must "
                    "follow mental picture, variable identity, change direction, plain "
                    "reading, and numeric example order"
                )
            mental_start, identity_start, change_start, plain_start, example_start = (
                label_positions
            )
            mental_text = teaching_block[mental_start:identity_start]
            identity_text = teaching_block[identity_start:change_start]
            change_text = teaching_block[change_start:plain_start]
            example_text = teaching_block[example_start:]
            if "[笔记解释]" not in mental_text or len(mental_text.strip()) < 45:
                raise ValidationFailure(
                    f"CSV line {line}: formula {picture.name!r} needs a substantive "
                    "[笔记解释] beginner mental picture"
                )
            if not any(tag in identity_text for tag in FORMULA_IDENTITY_TAGS):
                raise ValidationFailure(
                    f"CSV line {line}: formula {picture.name!r} must classify every "
                    "variable using the formula identity tags"
                )
            if len(identity_text.strip()) < 90:
                raise ValidationFailure(
                    f"CSV line {line}: formula {picture.name!r} variable identity "
                    "explanation is too short to audit"
                )
            if len(change_text.strip()) < 45:
                raise ValidationFailure(
                    f"CSV line {line}: formula {picture.name!r} needs a substantive "
                    "variable-change explanation"
                )
            if (
                "[笔记解释]" not in example_text
                or "不是论文实验" not in example_text
                or len(example_text.strip()) < 55
            ):
                raise ValidationFailure(
                    f"CSV line {line}: formula {picture.name!r} needs a numeric "
                    "[笔记解释] teaching example explicitly marked as not a paper experiment"
                )


def validate_rows(rows: list[dict[str, str]]) -> None:
    taxonomy = load_taxonomy()
    allowed_tracks = track_map(taxonomy)
    allowed_modalities = {
        value.casefold(): value for value in taxonomy["modalities"]
    }
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

        if row["primary_track"] not in allowed_tracks:
            raise ValidationFailure(
                f"CSV line {line}: primary_track must be one of "
                + ", ".join(allowed_tracks)
            )

        modalities = modality_list(row)
        if not modalities:
            raise ValidationFailure(
                f"CSV line {line}: modalities must contain at least one value"
            )
        normalized_modalities = [value.casefold() for value in modalities]
        if len(normalized_modalities) != len(set(normalized_modalities)):
            raise ValidationFailure(
                f"CSV line {line}: modalities contain duplicates"
            )
        invalid_modalities = [
            value
            for value in modalities
            if value.casefold() not in allowed_modalities
        ]
        if invalid_modalities:
            raise ValidationFailure(
                f"CSV line {line}: unsupported modalities: "
                + ", ".join(invalid_modalities)
            )

        topics = topic_list(row)
        if not 1 <= len(topics) <= 8:
            raise ValidationFailure(
                f"CSV line {line}: topics must contain between 1 and 8 tags"
            )
        normalized_topics = [topic.casefold() for topic in topics]
        if len(normalized_topics) != len(set(normalized_topics)):
            raise ValidationFailure(f"CSV line {line}: topics contain duplicates")
        if "autonomous driving" in normalized_topics:
            raise ValidationFailure(
                f"CSV line {line}: topics must be specific; remove "
                "'Autonomous Driving'"
            )
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
        try:
            structure = scan_markdown(note)
        except ValidationFailure as exc:
            raise ValidationFailure(f"CSV line {line}: {exc}") from exc
        for marker in NOTE_TEMPLATE_MARKERS:
            if marker in note:
                raise ValidationFailure(
                    f"CSV line {line}: note still contains template marker "
                    f"{marker!r}"
                )
        note_lines = [content for _, content in structure.top_level_lines]
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
                f"CSV line {line}: figure/formula/result/code/conclusion headings "
                "are out of order"
            )
        validate_translation_first_reading(
            note_path,
            line,
            structure=structure,
        )
        validate_selection_and_prior_art_contract(
            structure=structure,
            published_date=parsed_date,
            line=line,
            note_text=note,
        )
        validate_background_and_experiment_overview(
            structure=structure,
            published_date=parsed_date,
            line=line,
        )
        validate_architecture_reading(
            note_path,
            line,
            structure=structure,
            code_audit_status=row["code_audit_status"],
            repo_commit=row["repo_commit"],
            repo_url=row["repo_url"],
        )
        validate_note_assets(
            note_path,
            line,
            paper_url=row["paper_url"],
            structure=structure,
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


def validate_taste_rows(rows: list[dict[str, str]]) -> None:
    """Validate one portable-design card per indexed Beijing calendar day."""

    unique_dates: set[str] = set()
    unique_keys: set[str] = set()
    unique_modules: set[str] = set()
    unique_paths: set[str] = set()
    repository_root = ROOT.resolve()

    for row in rows:
        line = row["_line"]
        required = (
            "taste_key",
            "date",
            "module_name",
            "source_paper",
            "year",
            "venue",
            "publication_status",
            "paper_url",
            "mechanism_family",
            "transfer_targets",
            "note_path",
            "takeaway",
            "main_boundary",
        )
        missing = [field for field in required if not row[field]]
        if missing:
            raise ValidationFailure(
                f"Taste CSV line {line}: missing " + ", ".join(missing)
            )
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", row["taste_key"]):
            raise ValidationFailure(
                f"Taste CSV line {line}: taste_key must be a lowercase slug"
            )
        try:
            parsed_date = date.fromisoformat(row["date"])
        except ValueError as exc:
            raise ValidationFailure(
                f"Taste CSV line {line}: invalid ISO date"
            ) from exc
        if str(parsed_date.year) != row["date"][:4]:
            raise ValidationFailure(
                f"Taste CSV line {line}: invalid calendar year"
            )
        if not re.fullmatch(r"(?:19|20)\d{2}", row["year"]):
            raise ValidationFailure(
                f"Taste CSV line {line}: source-paper year must use YYYY"
            )
        if row["publication_status"] not in STATUS_LABELS:
            raise ValidationFailure(
                f"Taste CSV line {line}: publication_status must be Accepted or Preprint"
            )
        if row["publication_status"] == "Accepted" and not row["proceedings_url"]:
            raise ValidationFailure(
                f"Taste CSV line {line}: Accepted requires proceedings_url"
            )
        validate_url(row["paper_url"], "paper_url", line)
        validate_url(
            row["proceedings_url"],
            "proceedings_url",
            line,
            optional=True,
        )
        validate_url(row["repo_url"], "repo_url", line, optional=True)
        if bool(row["repo_url"]) != bool(row["repo_commit"]):
            raise ValidationFailure(
                f"Taste CSV line {line}: repo_url and repo_commit must appear together"
            )
        if row["repo_commit"] and not re.fullmatch(
            r"[0-9a-fA-F]{40}", row["repo_commit"]
        ):
            raise ValidationFailure(
                f"Taste CSV line {line}: repo_commit must be a full 40-character SHA"
            )
        if not 1 <= len(
            [item for item in row["transfer_targets"].split(";") if item.strip()]
        ) <= 8:
            raise ValidationFailure(
                f"Taste CSV line {line}: transfer_targets requires 1-8 semicolon-separated values"
            )
        if len(row["takeaway"]) > 160 or len(row["main_boundary"]) > 160:
            raise ValidationFailure(
                f"Taste CSV line {line}: takeaway/main_boundary must each be at most 160 characters"
            )

        note_posix = PurePosixPath(row["note_path"])
        expected_prefix = ("taste", row["date"][:4])
        if (
            note_posix.is_absolute()
            or ".." in note_posix.parts
            or note_posix.parts[:2] != expected_prefix
            or not DATED_NOTE_FILENAME_RE.fullmatch(note_posix.name)
        ):
            raise ValidationFailure(
                f"Taste CSV line {line}: note_path must be taste/YYYY/YYYY-MM-DD-slug.md"
            )
        note_path = (ROOT / note_posix).resolve()
        try:
            note_path.relative_to(repository_root)
        except ValueError as exc:
            raise ValidationFailure(
                f"Taste CSV line {line}: note_path escapes repository root"
            ) from exc
        if not note_path.is_file():
            raise ValidationFailure(
                f"Taste CSV line {line}: missing note {row['note_path']}"
            )
        note = read_text(note_path)
        if len(note) < 1200:
            raise ValidationFailure(
                f"Taste CSV line {line}: Taste card is too short for a design audit"
            )
        heading_positions = []
        for heading in TASTE_REQUIRED_HEADINGS:
            if note.count(heading) != 1:
                raise ValidationFailure(
                    f"Taste CSV line {line}: note requires exactly one {heading!r}"
                )
            heading_positions.append(note.index(heading))
        if heading_positions != sorted(heading_positions):
            raise ValidationFailure(
                f"Taste CSV line {line}: required headings are out of order"
            )
        for evidence_label in ("[论文]", "[源码]", "[判断]", "[未核验]"):
            if evidence_label not in note:
                raise ValidationFailure(
                    f"Taste CSV line {line}: note is missing {evidence_label}"
                )
        for identity in (
            row["module_name"],
            row["paper_url"],
            row["proceedings_url"],
            row["repo_commit"],
        ):
            if identity and identity not in note:
                raise ValidationFailure(
                    f"Taste CSV line {line}: note does not contain indexed identity {identity!r}"
                )

        expected_asset_root = (
            "assets",
            "taste",
            note_path.stem,
        )
        image_count = 0
        note_lines = note.splitlines()
        for line_index, note_line in enumerate(note_lines):
            matches = list(MARKDOWN_IMAGE_RE.finditer(note_line))
            if len(matches) > 1:
                raise ValidationFailure(
                    f"Taste CSV line {line}: put each image on its own Markdown line"
                )
            for match in matches:
                image_count += 1
                if not match.group("alt").strip():
                    raise ValidationFailure(
                        f"Taste CSV line {line}: every image requires descriptive alt text"
                    )
                raw_target = match.group("target").strip("<>")
                parsed = urlsplit(raw_target)
                if parsed.scheme or parsed.netloc:
                    raise ValidationFailure(
                        f"Taste CSV line {line}: Taste images must be local assets"
                    )
                resolved = (note_path.parent / unquote(parsed.path)).resolve()
                try:
                    relative = resolved.relative_to(repository_root)
                except ValueError as exc:
                    raise ValidationFailure(
                        f"Taste CSV line {line}: image escapes repository root"
                    ) from exc
                if not resolved.is_file() or relative.parts[:3] != expected_asset_root:
                    raise ValidationFailure(
                        f"Taste CSV line {line}: image must live under "
                        f"{'/'.join(expected_asset_root)}/"
                    )
                if resolved.suffix.casefold() != ".png":
                    raise ValidationFailure(
                        f"Taste CSV line {line}: explanatory images must be PNG"
                    )
                image_size = resolved.stat().st_size
                if not 1024 <= image_size <= 3 * 1024 * 1024:
                    raise ValidationFailure(
                        f"Taste CSV line {line}: image must be 1 KiB–3 MiB"
                    )
                next_index = line_index + 1
                while next_index < len(note_lines) and not note_lines[next_index].strip():
                    next_index += 1
                if next_index >= len(note_lines) or not note_lines[next_index].startswith(
                    "> **原图出处：**"
                ):
                    raise ValidationFailure(
                        f"Taste CSV line {line}: each image needs an immediately adjacent 原图出处 block"
                    )
                source_lines = []
                while next_index < len(note_lines) and note_lines[next_index].startswith(">"):
                    source_lines.append(note_lines[next_index])
                    next_index += 1
                source = "\n".join(source_lines)
                if (
                    not FIGURE_ID_RE.search(source)
                    or not PDF_PAGE_RE.search(source)
                    or row["paper_url"] not in source
                    or IMAGE_RIGHTS_NOTICE not in source
                ):
                    raise ValidationFailure(
                        f"Taste CSV line {line}: image source needs Figure number, PDF page, "
                        "indexed PDF link, and rights notice"
                    )
        if image_count < 1:
            raise ValidationFailure(
                f"Taste CSV line {line}: every card requires at least one explanatory figure"
            )

        normalized_values = (
            (unique_dates, row["date"], "date"),
            (unique_keys, row["taste_key"].casefold(), "taste_key"),
            (unique_modules, normalized_title(row["module_name"]), "module_name"),
            (unique_paths, row["note_path"].casefold(), "note_path"),
        )
        for seen, value, field in normalized_values:
            if value in seen:
                raise ValidationFailure(
                    f"Taste CSV line {line}: duplicate {field} {row[field]!r}"
                )
            seen.add(value)


def validate_taste_inventory(rows: list[dict[str, str]]) -> None:
    indexed = {row["note_path"] for row in rows}
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "taste").rglob("*.md")
        if DATED_NOTE_FILENAME_RE.fullmatch(path.name)
    }
    if indexed != actual:
        missing = sorted(indexed - actual)
        unindexed = sorted(actual - indexed)
        raise ValidationFailure(
            "Taste inventory mismatch; missing="
            f"{missing or 'none'}, unindexed={unindexed or 'none'}"
        )


def validate_public_markdown() -> None:
    paths = [
        README_PATH,
        ROOT / "SELECTION_POLICY.md",
        ROOT / "CONTRIBUTING.md",
    ]
    for directory in ("notes", "taste", "index", "templates", "docs"):
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


def modality_list(row: dict[str, str]) -> list[str]:
    return [item.strip() for item in row["modalities"].split(";") if item.strip()]


def track_map(taxonomy: dict[str, object]) -> dict[str, dict[str, str]]:
    return {
        track["id"]: track
        for track in taxonomy["tracks"]
    }


def track_name(row: dict[str, str], taxonomy: dict[str, object]) -> str:
    return track_map(taxonomy)[row["primary_track"]]["name"]


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


def render_stats(
    rows: list[dict[str, str]],
    taste_rows: list[dict[str, str]],
    taxonomy: dict[str, object],
) -> str:
    accepted = sum(row["publication_status"] == "Accepted" for row in rows)
    audited = sum(row["code_audit_status"] == "Audited" for row in rows)
    covered = len({row["primary_track"] for row in rows})
    track_total = len(taxonomy["tracks"])
    latest_date = max(rows[0]["date"], taste_rows[0]["date"])
    return (
        f"**{len(rows)} 篇精读** · **{accepted} 篇正式录用** · "
        f"**{audited} 篇关键源码已审** · "
        f"**{len(taste_rows)} 张算法 Taste 卡** · "
        f"**覆盖 {covered}/{track_total} 个感知主方向** · "
        f"最近更新：**{latest_date}**"
    )


def render_latest(
    row: dict[str, str],
    taxonomy: dict[str, object],
) -> str:
    note = root_link(row["note_path"])
    topics = " · ".join(md_escape(topic) for topic in topic_list(row))
    modalities = " + ".join(md_escape(item) for item in modality_list(row))
    primary = md_escape(track_name(row, taxonomy))
    identity = status_label(row)
    if row["publication_status"] == "Accepted":
        identity = f"[{identity}]({row['proceedings_url']})"
    return "\n".join(
        (
            "## ▶ 今日论文精读",
            "",
            f"### [{md_escape(row['title'])}]({note})",
            "",
            f"**{md_escape(row['venue'])} {row['year']}**",
            "",
            f"> {md_escape(row['takeaway'])}",
            "",
            "**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 "
            "→ 固定版本源码 → 证据边界",
            "",
            f"{identity} · **{primary}** · {modalities} · {topics} · "
            f"{code_audit_label(row)} · "
            f"**{md_escape(row['reproduction_status'])}**",
            "",
            f"[论文原文]({row['paper_url']}) · {code_link(row)}",
        )
    )


def taste_targets(row: dict[str, str]) -> list[str]:
    return [
        item.strip()
        for item in row["transfer_targets"].split(";")
        if item.strip()
    ]


def render_taste_latest(row: dict[str, str]) -> str:
    note = root_link(row["note_path"])
    targets = " · ".join(md_escape(item) for item in taste_targets(row))
    identity = status_label(row)
    if row["publication_status"] == "Accepted":
        identity = f"[{identity}]({row['proceedings_url']})"
    code = "无官方源码"
    if row["repo_url"]:
        code = (
            f"[固定实现 @ {row['repo_commit'][:8]}]"
            f"({row['repo_url']}/tree/{row['repo_commit']})"
        )
    return "\n".join(
        (
            "## 🧩 今日算法 Taste",
            "",
            f"### [{md_escape(row['module_name'])}]({note})",
            "",
            f"> {md_escape(row['takeaway'])}",
            "",
            f"**来自：** [{md_escape(row['source_paper'])}]({row['paper_url']})"
            f" · {identity} · **{md_escape(row['mechanism_family'])}**",
            "",
            f"**可迁移到：** {targets}",
            "",
            f"**先记边界：** {md_escape(row['main_boundary'])}",
            "",
            f"[看原理图、接口合同、适用场景与反证实验 →]({note}) · {code}",
        )
    )


def render_taste_index(rows: list[dict[str, str]]) -> str:
    latest = rows[0]
    lines = [
        "# 算法 Taste：可迁移设计卡",
        "",
        "[返回首页](../README.md) · [全部论文精读](../index/papers.md) · "
        "[13 类主题路线](../index/topics.md)",
        "",
        "> 这里每天只收一项真正值得迁移的设计：它可以是网络模块、主干网络、"
        "表示方式、训练单元或系统结构，但必须有明确瓶颈、可描述的接口、公开证据"
        "和失败边界。它不是又一份论文清单，也不把整篇论文包装成“即插即用”。",
        "",
        f"共 **{len(rows)}** 张设计卡；最近更新：**{latest['date']}**。",
        "",
        "## 怎么读一张卡",
        "",
        "1. 先判断它解决的瓶颈是否也存在于你的任务；",
        "2. 再检查输入、输出、shape、坐标系、梯度和算力接口；",
        "3. 最后看消融能支持到哪一层，并设计一个能推翻迁移假设的最小实验。",
        "",
        "## 全部设计卡",
    ]
    for row in rows:
        note = PurePosixPath(row["note_path"]).relative_to("taste").as_posix()
        targets = " · ".join(md_escape(item) for item in taste_targets(row))
        lines.extend(
            (
                "",
                f"### {row['date']} · [{md_escape(row['module_name'])}]({note})",
                "",
                f"**{md_escape(row['mechanism_family'])}** · 来自 "
                f"[{md_escape(row['source_paper'])}]({row['paper_url']}) "
                f"· {md_escape(row['venue'])} {row['year']}",
                "",
                f"> {md_escape(row['takeaway'])}",
                "",
                f"**可迁移到：** {targets}",
                "",
                f"**主要边界：** {md_escape(row['main_boundary'])}",
            )
        )
    lines.extend(
        (
            "",
            "## 收录边界",
            "",
            "- 优先正式录用论文、作者官方代码和可定位的受控比较；",
            "- 预印本必须显式标注，不用整模型主结果冒充单模块证据；",
            "- “可迁移”表示接口和设计逻辑值得测试，不表示零改动即可提升；",
            "- 未投稿方案、私有结果和可直接抢先实现的核心配方不进入公开卡片。",
            "",
        )
    )
    return "\n".join(lines)


def render_recent(rows: list[dict[str, str]], limit: int = 3) -> str:
    output = []
    for row in rows[:limit]:
        note = root_link(row["note_path"])
        output.append(
            f"- **{row['date']} · {md_escape(row['venue'])} {row['year']}** — "
            f"[{md_escape(row['title'])}]({note}) — "
            f"{code_audit_label(row)}；"
            f"**{md_escape(row['reproduction_status'])}**"
        )
    return "\n".join(output)


def render_papers_md(
    rows: list[dict[str, str]],
    taxonomy: dict[str, object],
) -> str:
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
        "每篇按“图 → 公式 → 结果 → 源码 → 结论”组织；"
        "“代码已审”不等于“结果已复现”。",
    ]
    for row in rows:
        note = index_link(row["note_path"])
        topics = " · ".join(md_escape(topic) for topic in topic_list(row))
        modalities = " + ".join(md_escape(item) for item in modality_list(row))
        primary = md_escape(track_name(row, taxonomy))
        lines.extend(
            (
                "",
                f"## {row['date']} · [{md_escape(row['title'])}]({note})",
                "",
                f"`{md_escape(row['venue'])} {row['year']}` · "
                f"`{status_label(row)}` · **{primary}** · "
                f"{modalities} · {topics}",
                "",
                f"> {md_escape(row['takeaway'])}",
                "",
                f"{md_escape(row['verification_stage'])}；"
                f"{code_audit_label(row)}；"
                f"**{md_escape(row['reproduction_status'])}**",
                "",
                f"[▶ 开始精读]({note}) · [论文原文]({row['paper_url']}) · "
                f"{code_link(row, '固定版本源码')}",
            )
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


def render_topics(
    rows: list[dict[str, str]],
    taxonomy: dict[str, object],
) -> str:
    by_track: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_modality: dict[str, list[dict[str, str]]] = defaultdict(list)
    by_topic: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_track[row["primary_track"]].append(row)
        for modality in modality_list(row):
            by_modality[modality].append(row)
        for topic in topic_list(row):
            by_topic[topic].append(row)

    large_model_tags = {
        value.casefold() for value in taxonomy["large_model_tags"]
    }
    large_model_rows = [
        row
        for row in rows
        if (
            row["primary_track"]
            in {"p11-vfm-vlm-llm-vla", "p12-world-models-generative-4d"}
            or any(topic.casefold() in large_model_tags for topic in topic_list(row))
        )
    ]

    def paper_line(row: dict[str, str], *, include_track: bool = False) -> str:
        note = index_link(row["note_path"])
        suffix = f" · {code_link(row, '代码')}" if row["repo_url"] else ""
        modalities = " + ".join(md_escape(item) for item in modality_list(row))
        track = (
            f" · {md_escape(track_name(row, taxonomy))}"
            if include_track
            else ""
        )
        return (
            f"- {row['date']} · [{md_escape(row['title'])}]({note}) — "
            f"{md_escape(row['venue'])} {row['year']} · "
            f"{status_label(row)}{track} · {modalities} · "
            f"[论文]({row['paper_url']}){suffix}"
        )

    lines = [
        "## 13 个方向一分钟速览",
        "",
        "下面先用一句话说明每个方向到底研究什么；需要查看具体任务边界、"
        "阅读问题和已收录论文时，再进入后面的对应章节。",
        "",
    ]
    for track in taxonomy["tracks"]:
        lines.append(
            f"- **{track['id'].split('-', 1)[0].upper()} · "
            f"{md_escape(track['name'])}：** {md_escape(track['intro'])}"
        )

    lines.extend(
        (
            "",
            "## 全方向覆盖总表",
            "",
            "> 这里列出完整分类，而不是只显示已经读过的热门方向。"
            "“0 篇”表示本仓库尚未覆盖，不代表学界没有相关工作。",
            "",
            "| 编号 | 自动驾驶感知主方向 | 已精读 | 最近更新 | 覆盖状态 |",
            "|---|---|---:|---|---|",
        )
    )
    for track in taxonomy["tracks"]:
        track_rows = sorted(
            by_track.get(track["id"], []),
            key=lambda row: (row["date"], row["paper_key"]),
            reverse=True,
        )
        latest = track_rows[0]["date"] if track_rows else "—"
        status = "已有锚点" if track_rows else "待覆盖"
        lines.append(
            f"| {track['id'].split('-', 1)[0].upper()} | "
            f"[{md_escape(track['name'])}](#{track['id']}) | "
            f"{len(track_rows)} | {latest} | {status} |"
        )

    lines.extend(
        (
            "",
            "## 按 13 个主方向精读",
            "",
            "每篇论文只有一个主方向，避免在目录中重复；传感器、任务、"
            "表示、可靠性和大模型关系通过后面的交叉索引补充。",
        )
    )
    for track in taxonomy["tracks"]:
        track_rows = sorted(
            by_track.get(track["id"], []),
            key=lambda row: (row["date"], row["paper_key"]),
            reverse=True,
        )
        lines.extend(
            (
                "",
                f"<a id=\"{track['id']}\"></a>",
                f"### {track['id'].split('-', 1)[0].upper()} · "
                f"{md_escape(track['name'])}（{len(track_rows)}）",
                "",
                f"**范围：** {md_escape(track['scope'])}",
                "",
                f"**阅读时追问：** {md_escape(track['question'])}",
                "",
            )
        )
        if track_rows:
            lines.extend(paper_line(row) for row in track_rows)
        else:
            lines.append("- 尚无完成精读；每日选文会优先检查这一覆盖缺口。")

    lines.extend(("", "## 与大模型结合的感知论文", ""))
    if large_model_rows:
        for row in sorted(
            large_model_rows,
            key=lambda item: (item["date"], item["paper_key"]),
            reverse=True,
        ):
            lines.append(paper_line(row, include_track=True))
    else:
        lines.append(
            "- 尚无完成精读。VFM、VLM、LLM、VLA 与世界模型只有在"
            "具有明确感知贡献或感知评测时才进入这里。"
        )

    lines.extend(("", "## 按输入模态浏览", ""))
    for modality in taxonomy["modalities"]:
        modality_rows = sorted(
            by_modality.get(modality, []),
            key=lambda row: (row["date"], row["paper_key"]),
            reverse=True,
        )
        lines.extend((f"### {md_escape(modality)}（{len(modality_rows)}）", ""))
        if modality_rows:
            lines.extend(
                paper_line(row, include_track=True) for row in modality_rows
            )
        else:
            lines.append("- 尚无完成精读。")
        lines.append("")

    lines.extend(("<details>", "<summary><strong>展开细任务与方法标签</strong></summary>", ""))
    for topic in sorted(by_topic, key=str.casefold):
        topic_rows = sorted(
            by_topic[topic],
            key=lambda row: (row["date"], row["paper_key"]),
            reverse=True,
        )
        lines.extend((f"### {md_escape(topic)}（{len(topic_rows)}）", ""))
        lines.extend(paper_line(row, include_track=True) for row in topic_rows)
        lines.append("")
    lines.extend(("</details>", ""))
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


def expected_files(
    rows: list[dict[str, str]],
    taste_rows: list[dict[str, str]],
) -> dict[Path, str]:
    taxonomy = load_taxonomy()
    readme = read_text(README_PATH)
    readme = replace_block(
        readme,
        "STATS",
        render_stats(rows, taste_rows, taxonomy),
    )
    readme = replace_block(readme, "LATEST", render_latest(rows[0], taxonomy))
    readme = replace_block(readme, "TASTE", render_taste_latest(taste_rows[0]))
    readme = replace_block(readme, "RECENT", render_recent(rows))

    topics = read_text(TOPICS_MD_PATH)
    topics = replace_block(topics, "TOPICS", render_topics(rows, taxonomy))

    targets = {
        README_PATH: readme.rstrip() + "\n",
        PAPERS_MD_PATH: render_papers_md(rows, taxonomy).rstrip() + "\n",
        TOPICS_MD_PATH: topics.rstrip() + "\n",
        TASTE_MD_PATH: render_taste_index(taste_rows).rstrip() + "\n",
    }
    try:
        radar_targets, _counts = research_radar.expected_files()
    except research_radar.ValidationFailure as exc:
        raise ValidationFailure(f"research radar: {exc}") from exc
    targets.update(radar_targets)
    return targets


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def validate_dated_note_inventory(
    rows: list[dict[str, str]],
    *,
    root: Path | None = None,
) -> None:
    """Require every dated note under ``notes/`` to be indexed exactly once."""

    repository_root = root or ROOT
    notes_root = repository_root / "notes"
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        counts[row["note_path"]] += 1

    dated_notes = sorted(
        path.relative_to(repository_root).as_posix()
        for path in notes_root.rglob("*.md")
        if DATED_NOTE_FILENAME_RE.fullmatch(path.name)
    )
    failures = [
        (path, counts.get(path, 0))
        for path in dated_notes
        if counts.get(path, 0) != 1
    ]
    if failures:
        details = ", ".join(
            f"{path} ({count} CSV entries)" for path, count in failures
        )
        raise ValidationFailure(
            "every dated note under notes/ must be indexed exactly once: "
            + details
        )


def main() -> int:
    args = parse_args()
    try:
        rows = load_rows()
        rows.sort(key=lambda row: (row["date"], row["paper_key"]), reverse=True)
        taste_rows = load_taste_rows()
        taste_rows.sort(
            key=lambda row: (row["date"], row["taste_key"]),
            reverse=True,
        )
        validate_rows(rows)
        validate_taste_rows(taste_rows)
        validate_dated_note_inventory(rows)
        validate_taste_inventory(taste_rows)
        validate_open_questions_contract()
        validate_public_markdown()
        targets = expected_files(rows, taste_rows)

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
        print(f"OK: validated {len(taste_rows)} indexed Taste card(s)")
        return 0
    except ValidationFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
