from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import lint_markdown_math as math_lint  # noqa: E402
import rebuild_index as rebuild  # noqa: E402


class IndexedNoteValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = rebuild.load_rows()
        cls.note_path = ROOT / cls.rows[0]["note_path"]
        cls.note = rebuild.read_text(cls.note_path)
        cls.paper_url = cls.rows[0]["paper_url"]
        cls.formula_source_path = (
            ROOT
            / "assets"
            / "notes"
            / cls.note_path.stem
            / "formulas"
            / rebuild.FORMULA_SOURCE_FILE
        )
        cls.formula_source = cls.formula_source_path.read_text(encoding="utf-8")

    def validate_mutation(
        self,
        note: str,
        *,
        formula_source: str | None = None,
    ) -> None:
        original_read_text = rebuild.read_text
        original_read_bytes = Path.read_bytes
        original_path_read_text = Path.read_text

        def patched_read_text(path: Path) -> str:
            if path.resolve() == self.note_path.resolve():
                return note
            return original_read_text(path)

        def patched_read_bytes(path: Path) -> bytes:
            if (
                formula_source is not None
                and path.resolve() == self.formula_source_path.resolve()
            ):
                return formula_source.encode("utf-8")
            return original_read_bytes(path)

        def patched_path_read_text(
            path: Path,
            *args: object,
            **kwargs: object,
        ) -> str:
            if (
                formula_source is not None
                and path.resolve() == self.formula_source_path.resolve()
            ):
                return formula_source
            return original_path_read_text(path, *args, **kwargs)

        with mock.patch.object(rebuild, "read_text", side_effect=patched_read_text):
            with mock.patch.object(Path, "read_bytes", new=patched_read_bytes):
                with mock.patch.object(
                    Path,
                    "read_text",
                    new=patched_path_read_text,
                ):
                    rebuild.validate_rows(self.rows)

    def assert_mutation_fails(
        self,
        note: str,
        *,
        formula_source: str | None = None,
    ) -> None:
        with self.assertRaises(rebuild.ValidationFailure):
            self.validate_mutation(note, formula_source=formula_source)

    def hide_method_section(self, opener: str, closer: str) -> str:
        image_start = self.note.index("![ST-Occ Figure 2")
        formula_heading = self.note.index("## 2. 读公式")
        return (
            self.note[:image_start]
            + opener
            + self.note[image_start:formula_heading]
            + closer
            + self.note[formula_heading:]
        )

    def test_current_note_passes(self) -> None:
        self.validate_mutation(self.note)

    def test_figures_hidden_in_fence_fail(self) -> None:
        self.assert_mutation_fails(self.hide_method_section("```\n", "```\n\n"))

    def test_figures_hidden_in_comment_fail(self) -> None:
        self.assert_mutation_fails(self.hide_method_section("<!--\n", "-->\n\n"))

    def test_figures_hidden_in_details_fail(self) -> None:
        self.assert_mutation_fails(
            self.hide_method_section(
                "<details>\n<summary>hidden</summary>\n\n",
                "</details>\n\n",
            )
        )

    def test_attribution_must_immediately_follow_image(self) -> None:
        mutated = self.note.replace(
            "\n\n> **原图出处：**",
            "\n\n### unrelated heading\n\n> **原图出处：**",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_attribution_requires_exact_official_pdf(self) -> None:
        mutated = self.note.replace(
            f"[官方 PDF]({self.paper_url})",
            "[官方 PDF](https://example.invalid/paper.pdf)",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_attribution_requires_rights_notice(self) -> None:
        mutated = self.note.replace(
            rebuild.IMAGE_RIGHTS_NOTICE,
            "rights omitted",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_attribution_must_immediately_follow_image(self) -> None:
        mutated = self.note.replace(
            "\n\n> **公式来源：**",
            "\n\n### unrelated heading\n\n> **公式来源：**",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_assets_cannot_cross_note_directories(self) -> None:
        mutated = self.note.replace(
            "assets/notes/2026-07-24-st-occ/formulas/"
            "eq-05-unified-memory-read.png",
            "assets/notes/another-note/formulas/"
            "eq-05-unified-memory-read.png",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_source_link_is_required(self) -> None:
        mutated = self.note.replace(
            "formulas/source.tex#L5-L9",
            "formulas/copyable-source.txt",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_source_link_must_be_unique(self) -> None:
        source_link = (
            "[可复制 TeX](../../assets/notes/2026-07-24-st-occ/"
            "formulas/source.tex#L5-L9)"
        )
        mutated = self.note.replace(source_link, f"{source_link} · {source_link}", 1)
        self.assert_mutation_fails(mutated)

    def test_formula_source_anchor_rejects_upstream_line_drift(self) -> None:
        marker = "% BEGIN eq-07-class-activation-update"
        shifted_source = self.formula_source.replace(
            marker,
            "% harmless upstream comment that shifts later line anchors\n" + marker,
            1,
        )
        with self.assertRaisesRegex(
            rebuild.ValidationFailure,
            "does not exactly anchor",
        ):
            self.validate_mutation(
                self.note,
                formula_source=shifted_source,
            )

    def test_external_images_are_rejected(self) -> None:
        mutated = self.note.replace(
            "## 2. 读公式：核心机制怎样表达",
            "![hotlink](https://example.com/figure.png)\n\n"
            "## 2. 读公式：核心机制怎样表达",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_numbered_formula_rejects_placeholder_identifier(self) -> None:
        mutated = self.note.replace("Eq. (5)", "Eq. (X)", 1)
        self.assert_mutation_fails(mutated)

    def test_formula_modes_are_exclusive(self) -> None:
        mutated = self.note.replace(
            "## 2. 读公式：核心机制怎样表达",
            "## 2. 读公式：核心机制怎样表达\n\n"
            "**原文无必要公式：** 本文没有关键公式。",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_original_formula_declaration_must_stay_in_section_two(self) -> None:
        marker = (
            "**原文公式：** 论文 Eq. (5)，PDF p. 4 / "
            "proceedings p. 26572。"
        )
        mutated = self.note.replace(marker, "公式见后文。", 1)
        mutated = mutated.replace(
            "## 4. 对源码：公式如何落地",
            "## 4. 对源码：公式如何落地\n\n" + marker,
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_unmatched_and_unclosed_details_fail(self) -> None:
        self.assert_mutation_fails(self.note + "\n</details>\n")
        self.assert_mutation_fails(self.note + "\n<details>\n")

    def test_html_tokens_inside_fenced_code_do_not_change_structure(self) -> None:
        mutated = self.note.replace(
            "多相机图像\n",
            "多相机图像\n</details>\n<!-- literal code example\n",
            1,
        )
        self.validate_mutation(mutated)

    def test_windows_drive_and_unc_note_paths_fail(self) -> None:
        for value in (
            r"notes/2026/C:\Windows/2026-07-24-x.md",
            r"notes/2026/\\server\share\2026-07-24-x.md",
        ):
            with self.subTest(value=value):
                with self.assertRaises(rebuild.ValidationFailure):
                    rebuild.safe_note_path(value, "2")


class MathLintRegressionTests(unittest.TestCase):
    def lint_text(self, text: str) -> list[math_lint.LintError]:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "note.md"
            path.write_text(text, encoding="utf-8")
            return math_lint.lint_path(path)

    def assert_lint_fails(self, text: str, rule: str | None = None) -> None:
        errors = self.lint_text(text)
        self.assertTrue(errors)
        if rule is not None:
            self.assertIn(rule, {error.rule for error in errors})

    def test_valid_inline_and_display_math_pass(self) -> None:
        text = (
            "Inline $`M_t`$.\n\n"
            "```math\n"
            "\\begin{aligned}\n"
            "x &= y + 1,\\\\\n"
            "z &= \\mathrm{mean}(x)\n"
            "\\end{aligned}\n"
            "```\n"
        )
        self.assertEqual(self.lint_text(text), [])

    def test_notes_policy_rejects_live_inline_and_display_math(self) -> None:
        with mock.patch.object(
            math_lint,
            "requires_static_formula_assets",
            return_value=True,
        ):
            errors = self.lint_text(
                "Inline $`M_t`$.\n\n"
                "```math\n"
                "M_t = 1\n"
                "```\n"
            )
        self.assertIn("MATH015", {error.rule for error in errors})

    def test_public_notes_and_template_have_zero_live_math(self) -> None:
        offenders = []
        for path in math_lint.markdown_paths():
            if not math_lint.requires_static_formula_assets(path):
                continue
            for error in math_lint.lint_path(path):
                if error.rule == "MATH015":
                    offenders.append(error.render())
        self.assertEqual(offenders, [])

    def test_github_forbidden_operatorname_fails(self) -> None:
        self.assert_lint_fails(
            "```math\n\\operatorname{softmax}(x)\n```\n",
            "MATH008",
        )
        self.assert_lint_fails(
            "Bad $`\\operatorname{DA}(x)`$.\n",
            "MATH008",
        )

    def test_github_safe_named_operators_pass(self) -> None:
        text = (
            "Inline $`\\mathrm{DA}(x)`$ and "
            "$`\\exp(\\mathrm{softplus}(x))`$.\n\n"
            "```math\n"
            "\\mathrm{softmax}(x)"
            "+\\mathrm{MLP}(x)"
            "+\\mathrm{STCV}_t"
            "+\\mathrm{mSTCV}"
            "+\\mathrm{mean}_i[x_i]\n"
            "```\n"
        )
        self.assertEqual(self.lint_text(text), [])

    def test_public_math_contains_no_operatorname(self) -> None:
        offenders = []
        for path in math_lint.markdown_paths():
            for error in math_lint.lint_path(path):
                if r"\operatorname" in error.message:
                    offenders.append(error.render())
        self.assertEqual(offenders, [])

    def test_inline_custom_macro_fails(self) -> None:
        self.assert_lint_fails("Bad $`\\method(x)`$.\n", "MATH008")
        self.assert_lint_fails("Bad $`\\foo{x}`$.\n", "MATH008")

    def test_nested_inline_delimiters_fail(self) -> None:
        self.assert_lint_fails("Bad $`\\(x\\)`$.\n", "MATH008")
        self.assert_lint_fails("Bad $`x=$y$`$.\n", "MATH008")

    def test_empty_or_unbalanced_display_math_fails(self) -> None:
        self.assert_lint_fails("```math\n\n```\n", "MATH013")
        self.assert_lint_fails("```math\nx_{i\n```\n", "MATH008")
        self.assert_lint_fails(
            "```math\n\\begin{aligned}\nx &= 1\n\\end{cases}\n```\n",
            "MATH008",
        )

    def test_raw_delimiters_fail(self) -> None:
        self.assert_lint_fails("Bad \\(x\\).\n", "MATH001")
        self.assert_lint_fails("Bad $$x$$.\n", "MATH002")
        self.assert_lint_fails("```math\nx=$y$\n```\n", "MATH008")

    def test_math_inside_details_and_broken_details_fail(self) -> None:
        self.assert_lint_fails(
            "<details>\n<summary>x</summary>\n```math\nx=1\n```\n</details>\n",
            "MATH012",
        )
        self.assert_lint_fails("</details>\n", "MATH014")
        self.assert_lint_fails("<details>\n", "MATH014")

    def test_html_tokens_inside_code_fence_are_ignored(self) -> None:
        text = "```text\n</details>\n<!-- literal code example\n```\n"
        self.assertEqual(self.lint_text(text), [])


if __name__ == "__main__":
    unittest.main()
