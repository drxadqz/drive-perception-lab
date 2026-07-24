#!/usr/bin/env python3
"""Render compact cross-device formula PNGs from a reviewable TeX source file.

GitHub's web interface can execute MathJax, but GitHub's native mobile
renderers do not always provide the same behavior.  The public notes therefore
use tightly cropped, explicitly sized PNGs for display equations and ordinary
mathematical text for inline notation.  Each formula gets a light image and a
dark image with identical geometry; the light image remains a readable fallback
if a renderer ignores GitHub's theme-aware ``picture`` element.

The script requires a local LaTeX installation, pdftocairo, and Pillow.  It is
an authoring tool, not a CI dependency; generated PNGs are committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
FORMULA_ROOT = ROOT / "assets" / "notes"
OUTPUT_SCALE = 2
HORIZONTAL_PADDING = 28
VERTICAL_PADDING = 20
MIN_DISPLAY_WIDTH = 96
MAX_DISPLAY_WIDTH = 720
MIN_DISPLAY_HEIGHT = 36
MAX_DISPLAY_HEIGHT = 180
LIGHT_BACKGROUND = "#ffffff"
LIGHT_FOREGROUND = "#1f2328"
DARK_BACKGROUND = "#0d1117"
DARK_FOREGROUND = "#f0f6fc"
BLOCK_RE = re.compile(
    r"^% BEGIN (?P<name>[a-z0-9-]+)\n"
    r"(?P<body>.*?)"
    r"^% END (?P=name)\s*$",
    re.MULTILINE | re.DOTALL,
)

DOCUMENT = r"""\documentclass[border=18pt]{standalone}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{xcolor}
\begin{document}
\color{black}
{\Large
\(\displaystyle
%s
\)
}
\end{document}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Render to a temporary directory and compare pixels with committed PNGs.",
    )
    parser.add_argument(
        "--note-key",
        help=(
            "Render only assets/notes/<note-key>/formulas. "
            "Without this option every formula directory is processed."
        ),
    )
    return parser.parse_args()


def formula_directories(note_key: str | None) -> list[Path]:
    if note_key is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*", note_key):
            raise RuntimeError(f"Unsafe note key: {note_key!r}")
        directories = [FORMULA_ROOT / note_key / "formulas"]
    else:
        directories = sorted(
            path.parent for path in FORMULA_ROOT.glob("*/formulas/source.tex")
        )
    missing = [
        directory.relative_to(ROOT).as_posix()
        for directory in directories
        if not (directory / "source.tex").is_file()
    ]
    if missing:
        raise RuntimeError(
            "Formula directory has no source.tex: " + ", ".join(missing)
        )
    if not directories:
        raise RuntimeError("No formula source directories found")
    return directories


def formula_blocks(source_path: Path) -> list[tuple[str, str]]:
    source = source_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    blocks = [
        (match.group("name"), match.group("body").strip())
        for match in BLOCK_RE.finditer(source)
    ]
    if not blocks:
        raise RuntimeError(f"No formula blocks found in {source_path}")
    names = [name for name, _ in blocks]
    if len(names) != len(set(names)):
        raise RuntimeError("Formula source contains duplicate block names")
    return blocks


def require_command(name: str) -> str:
    command = shutil.which(name)
    if not command:
        raise RuntimeError(f"Required authoring command not found: {name}")
    return command


def render_one(
    *,
    name: str,
    body: str,
    light_destination: Path,
    dark_destination: Path,
    pdflatex: str,
    pdftocairo: str,
) -> None:
    with tempfile.TemporaryDirectory(prefix="formula-render-") as temporary:
        temporary_path = Path(temporary)
        tex_path = temporary_path / f"{name}.tex"
        tex_path.write_text(DOCUMENT % body, encoding="utf-8", newline="\n")

        latex_result = subprocess.run(
            [
                pdflatex,
                "-halt-on-error",
                "-interaction=nonstopmode",
                f"-output-directory={temporary_path}",
                str(tex_path),
            ],
            check=False,
            cwd=temporary_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if latex_result.returncode:
            raise RuntimeError(
                f"LaTeX failed for {name}:\n{latex_result.stdout}"
            )
        pdf_path = temporary_path / f"{name}.pdf"
        raw_prefix = temporary_path / f"{name}-raw"
        subprocess.run(
            [
                pdftocairo,
                "-png",
                "-singlefile",
                "-r",
                "260",
                str(pdf_path),
                str(raw_prefix),
            ],
            check=True,
            cwd=temporary_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        with Image.open(raw_prefix.with_suffix(".png")) as raw:
            rgba = raw.convert("RGBA")
            white = Image.new("RGBA", rgba.size, "white")
            white.alpha_composite(rgba)
            rgb = white.convert("RGB")
            ink_mask = ImageOps.invert(rgb.convert("L"))
            ink_box = ink_mask.getbbox()
            if ink_box is None:
                raise RuntimeError(f"Rendered formula contains no visible ink: {name}")
            left, top, right, bottom = ink_box
            crop_box = (
                max(0, left - HORIZONTAL_PADDING),
                max(0, top - VERTICAL_PADDING),
                min(rgb.width, right + HORIZONTAL_PADDING),
                min(rgb.height, bottom + VERTICAL_PADDING),
            )
            cropped_mask = ink_mask.crop(crop_box)
            pixel_width, pixel_height = cropped_mask.size
            display_width = round(pixel_width / OUTPUT_SCALE)
            display_height = round(pixel_height / OUTPUT_SCALE)
            if not MIN_DISPLAY_WIDTH <= display_width <= MAX_DISPLAY_WIDTH:
                raise RuntimeError(
                    f"Formula {name} would display {display_width}px wide; "
                    "adjust the TeX or add an explicit aligned line break"
                )
            if not MIN_DISPLAY_HEIGHT <= display_height <= MAX_DISPLAY_HEIGHT:
                raise RuntimeError(
                    f"Formula {name} would display {display_height}px high; "
                    "adjust the TeX layout"
                )

            light = Image.new("RGB", cropped_mask.size, LIGHT_BACKGROUND)
            light.paste(LIGHT_FOREGROUND, mask=cropped_mask)
            dark = Image.new("RGB", cropped_mask.size, DARK_BACKGROUND)
            dark.paste(DARK_FOREGROUND, mask=cropped_mask)

            light_destination.parent.mkdir(parents=True, exist_ok=True)
            light.save(light_destination, format="PNG", optimize=True)
            dark.save(dark_destination, format="PNG", optimize=True)


def same_pixels(left: Path, right: Path) -> bool:
    if not left.is_file() or not right.is_file():
        return False
    with Image.open(left) as left_image, Image.open(right) as right_image:
        return (
            left_image.mode == right_image.mode
            and left_image.size == right_image.size
            and left_image.tobytes() == right_image.tobytes()
        )


def build_manifest(
    blocks: list[tuple[str, str]],
    formula_directory: Path,
) -> dict[str, object]:
    formulas: dict[str, object] = {}
    for name, body in blocks:
        light_path = formula_directory / f"{name}-light.png"
        dark_path = formula_directory / f"{name}-dark.png"
        with Image.open(light_path) as image:
            width, height = image.size
        with Image.open(dark_path) as dark_image:
            dark_size = dark_image.size
        if dark_size != (width, height):
            raise RuntimeError(f"Theme variants have different geometry: {name}")
        formulas[name] = {
            "source_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "light_png_sha256": hashlib.sha256(
                light_path.read_bytes()
            ).hexdigest(),
            "dark_png_sha256": hashlib.sha256(dark_path.read_bytes()).hexdigest(),
            "pixel_width": width,
            "pixel_height": height,
            "display_width": round(width / OUTPUT_SCALE),
            "display_height": round(height / OUTPUT_SCALE),
        }
    return {
        "version": 2,
        "profile": {
            "layout": "content-sized-2x",
            "output_scale": OUTPUT_SCALE,
            "horizontal_padding": HORIZONTAL_PADDING,
            "vertical_padding": VERTICAL_PADDING,
            "minimum_display_width": MIN_DISPLAY_WIDTH,
            "maximum_display_width": MAX_DISPLAY_WIDTH,
            "minimum_display_height": MIN_DISPLAY_HEIGHT,
            "maximum_display_height": MAX_DISPLAY_HEIGHT,
            "light_background": LIGHT_BACKGROUND,
            "light_foreground": LIGHT_FOREGROUND,
            "dark_background": DARK_BACKGROUND,
            "dark_foreground": DARK_FOREGROUND,
        },
        "formulas": formulas,
    }


def process_formula_directory(
    *,
    formula_directory: Path,
    check: bool,
    pdflatex: str,
    pdftocairo: str,
) -> None:
    source_path = formula_directory / "source.tex"
    manifest_path = formula_directory / "manifest.json"
    blocks = formula_blocks(source_path)

    if check:
        with tempfile.TemporaryDirectory(prefix="formula-check-") as temporary:
            rendered_dir = Path(temporary)
            failures: list[str] = []
            for name, body in blocks:
                light_candidate = rendered_dir / f"{name}-light.png"
                dark_candidate = rendered_dir / f"{name}-dark.png"
                render_one(
                    name=name,
                    body=body,
                    light_destination=light_candidate,
                    dark_destination=dark_candidate,
                    pdflatex=pdflatex,
                    pdftocairo=pdftocairo,
                )
                light_committed = formula_directory / f"{name}-light.png"
                dark_committed = formula_directory / f"{name}-dark.png"
                if not (
                    same_pixels(light_candidate, light_committed)
                    and same_pixels(dark_candidate, dark_committed)
                ):
                    failures.append(name)
            if failures:
                raise RuntimeError(
                    "Committed formula PNGs are missing or stale: "
                    + ", ".join(failures)
                )
        expected_manifest = build_manifest(blocks, formula_directory)
        try:
            committed_manifest = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            raise RuntimeError("Formula manifest is missing or invalid") from exc
        if committed_manifest != expected_manifest:
            raise RuntimeError("Formula manifest is stale; render assets again")
        print(
            f"OK: {len(blocks)} compact light/dark formula pairs match "
            f"{source_path.relative_to(ROOT)}"
        )
        return

    for name, body in blocks:
        render_one(
            name=name,
            body=body,
            light_destination=formula_directory / f"{name}-light.png",
            dark_destination=formula_directory / f"{name}-dark.png",
            pdflatex=pdflatex,
            pdftocairo=pdftocairo,
        )
    manifest = build_manifest(blocks, formula_directory)
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"Rendered {len(blocks)} compact light/dark formula pairs in "
        f"{formula_directory.relative_to(ROOT)}"
    )


def main() -> int:
    args = parse_args()
    pdflatex = require_command("pdflatex")
    pdftocairo = require_command("pdftocairo")
    directories = formula_directories(args.note_key)
    for directory in directories:
        process_formula_directory(
            formula_directory=directory,
            check=args.check,
            pdflatex=pdflatex,
            pdftocairo=pdftocairo,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
