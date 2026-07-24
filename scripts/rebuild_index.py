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
    "## 1. 看图：论文到底做了什么",
    "## 2. 读公式：核心机制怎样表达",
    "## 3. 看结果：证据是否支持主张",
    "## 4. 对源码：公式如何落地",
    "## 5. 记结论：贡献、边界与开放问题",
)

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
FIGURE_ID_RE = re.compile(r"\bFigure\s+S?\d+[A-Za-z]?\b")
TABLE_ID_RE = re.compile(r"\bTable\s+S?\d+[A-Za-z]?\b")
PDF_PAGE_RE = re.compile(r"\bPDF p\.\s*\d+\b")
IMAGE_RIGHTS_NOTICE = "原图版权归原作者及其他权利人"
FORMULA_ALT_PREFIX = "公式："
FORMULA_SOURCE_LABEL = "**公式来源：**"
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
    topics = " · ".join(md_escape(topic) for topic in topic_list(row))
    identity = status_label(row)
    if row["publication_status"] == "Accepted":
        identity = f"[{identity}]({row['proceedings_url']})"
    return "\n".join(
        (
            f"## ▶ [开始今天的精读：{md_escape(row['title'])}"
            f"（{md_escape(row['venue'])} {row['year']}）]({note})",
            "",
            f"> {md_escape(row['takeaway'])}",
            "",
            "**进入后按这一条路线读：** 原文图 → 标准公式 → 关键结果 "
            "→ 固定版本源码 → 证据边界",
            "",
            f"{identity} · {topics} · "
            f"{code_audit_label(row)} · "
            f"**{md_escape(row['reproduction_status'])}**",
            "",
            f"[论文原文]({row['paper_url']}) · {code_link(row)}",
        )
    )


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
        "每篇按“图 → 公式 → 结果 → 源码 → 结论”组织；"
        "“代码已审”不等于“结果已复现”。",
    ]
    for row in rows:
        note = index_link(row["note_path"])
        topics = " · ".join(md_escape(topic) for topic in topic_list(row))
        lines.extend(
            (
                "",
                f"## {row['date']} · [{md_escape(row['title'])}]({note})",
                "",
                f"`{md_escape(row['venue'])} {row['year']}` · "
                f"`{status_label(row)}` · {topics}",
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
