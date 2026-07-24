#!/usr/bin/env python3
"""Render cross-device formula PNGs from a reviewable TeX source file.

GitHub's web interface can execute MathJax, but GitHub's native mobile
renderers do not always provide the same behavior.  The public notes therefore
use opaque PNGs for display equations and ordinary text for inline notation.
This script keeps the PNGs reproducible and the underlying TeX copyable.

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

from PIL import Image, ImageChops


ROOT = Path(__file__).resolve().parents[1]
FORMULA_ROOT = ROOT / "assets" / "notes"
CANVAS_WIDTH = 2048
MAX_INK_WIDTH = 1856
MIN_INK_HEIGHT = 112
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
\definecolor{FormulaInk}{HTML}{1F2328}
\begin{document}
\color{FormulaInk}
\(\displaystyle
%s
\)
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
    destination: Path,
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
            difference = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white"))
            ink_box = difference.getbbox()
            if ink_box is None:
                raise RuntimeError(f"Rendered formula contains no visible ink: {name}")
            left, top, right, bottom = ink_box
            crop_box = (
                max(0, left - 28),
                max(0, top - 24),
                min(rgb.width, right + 28),
                min(rgb.height, bottom + 24),
            )
            cropped = rgb.crop(crop_box)
            ink_height = bottom - top
            requested_scale = max(1.6, MIN_INK_HEIGHT / max(1, ink_height))
            maximum_scale = MAX_INK_WIDTH / cropped.width
            if requested_scale > maximum_scale:
                projected_height = ink_height * maximum_scale
                raise RuntimeError(
                    f"Formula {name} would shrink to {projected_height:.1f}px "
                    f"ink height to fit; add an explicit aligned line break"
                )
            scale = requested_scale
            resized = cropped.resize(
                (
                    max(1, round(cropped.width * scale)),
                    max(1, round(cropped.height * scale)),
                ),
                Image.Resampling.LANCZOS,
            )
            canvas_height = max(240, resized.height + 96)
            padded = Image.new("RGB", (CANVAS_WIDTH, canvas_height), "white")
            padded.paste(
                resized,
                ((padded.width - resized.width) // 2, (padded.height - resized.height) // 2),
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            padded.save(
                destination,
                format="PNG",
                optimize=True,
                dpi=(260, 260),
            )


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
        png_path = formula_directory / f"{name}.png"
        with Image.open(png_path) as image:
            width, height = image.size
        formulas[name] = {
            "source_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "png_sha256": hashlib.sha256(png_path.read_bytes()).hexdigest(),
            "width": width,
            "height": height,
        }
    return {
        "version": 1,
        "profile": {
            "canvas_width": CANVAS_WIDTH,
            "minimum_height": 192,
            "maximum_height": 1536,
            "minimum_ink_height": MIN_INK_HEIGHT,
            "maximum_ink_width": MAX_INK_WIDTH,
            "background": "#ffffff",
            "foreground": "#1f2328",
            "dpi": 260,
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
                candidate = rendered_dir / f"{name}.png"
                render_one(
                    name=name,
                    body=body,
                    destination=candidate,
                    pdflatex=pdflatex,
                    pdftocairo=pdftocairo,
                )
                committed = formula_directory / f"{name}.png"
                if not same_pixels(candidate, committed):
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
        print(f"OK: {len(blocks)} formula PNGs match {source_path.relative_to(ROOT)}")
        return

    for name, body in blocks:
        render_one(
            name=name,
            body=body,
            destination=formula_directory / f"{name}.png",
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
        f"Rendered {len(blocks)} formula PNGs in "
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
