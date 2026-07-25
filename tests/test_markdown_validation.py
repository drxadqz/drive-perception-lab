from __future__ import annotations

import json
import re
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
        cls.formula_directory = cls.formula_source_path.parent
        cls.formula_manifest_path = (
            cls.formula_directory / rebuild.FORMULA_MANIFEST_FILE
        )
        cls.formula_manifest = cls.formula_manifest_path.read_text(
            encoding="utf-8"
        )
        cls.first_formula_picture = next(
            line
            for line in cls.note.splitlines()
            if rebuild.FORMULA_PICTURE_RE.fullmatch(line)
        )
        cls.first_formula_match = rebuild.FORMULA_PICTURE_RE.fullmatch(
            cls.first_formula_picture
        )
        assert cls.first_formula_match is not None
        cls.first_formula_stem = Path(
            cls.first_formula_match.group("light")
        ).name.removesuffix("-light.png")
        cls.first_formula_width = int(cls.first_formula_match.group("width"))
        cls.first_formula_height = int(cls.first_formula_match.group("height"))
        source_link_match = re.search(
            r"\[可复制 TeX\]\((?P<target>[^)\n]+source\.tex"
            r"#L[1-9]\d*-L[1-9]\d*)\)",
            cls.note,
        )
        assert source_link_match is not None
        cls.first_formula_source_link = source_link_match.group(0)
        cls.first_formula_source_target = source_link_match.group("target")

    def validate_mutation(
        self,
        note: str,
        *,
        formula_source: str | None = None,
        formula_manifest: str | None = None,
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
            if (
                formula_manifest is not None
                and path.resolve() == self.formula_manifest_path.resolve()
            ):
                return formula_manifest
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
        formula_manifest: str | None = None,
    ) -> None:
        with self.assertRaises(rebuild.ValidationFailure):
            self.validate_mutation(
                note,
                formula_source=formula_source,
                formula_manifest=formula_manifest,
            )

    def hide_method_section(self, opener: str, closer: str) -> str:
        method_heading = self.note.index("## 1. 看图")
        formula_heading = self.note.index("## 2. 读公式")
        image_match = re.search(
            r"^!\[[^\n]+\]\([^)]+\)$",
            self.note[method_heading:formula_heading],
            re.MULTILINE,
        )
        assert image_match is not None
        image_start = method_heading + image_match.start()
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

    def test_formula_picture_requires_exact_one_line_markup(self) -> None:
        malformed = self.first_formula_picture.replace(
            '<p align="center">',
            '<p align="center" >',
            1,
        )
        mutated = self.note.replace(self.first_formula_picture, malformed, 1)
        self.assert_mutation_fails(mutated)

    def test_arbitrary_html_image_is_rejected(self) -> None:
        mutated = self.note.replace(
            "## 2. 读公式：核心机制怎样表达",
            '<img src="../../assets/notes/2026-07-24-st-occ/'
            'figure-2-overview.png" alt="not allowed">\n\n'
            "## 2. 读公式：核心机制怎样表达",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_picture_requires_both_existing_theme_images(self) -> None:
        dark_name = Path(self.first_formula_match.group("dark")).name
        mutated = self.note.replace(
            dark_name,
            f"{self.first_formula_stem}-missing-dark.png",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_picture_theme_stems_must_match(self) -> None:
        dark_name = Path(self.first_formula_match.group("dark")).name
        mutated = self.note.replace(
            dark_name,
            "different-formula-dark.png",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_picture_display_bounds_and_2x_density_are_enforced(self) -> None:
        dimensions = (
            f'width="{self.first_formula_width}" '
            f'height="{self.first_formula_height}"'
        )
        with self.subTest("display bounds"):
            malformed = self.first_formula_picture.replace(
                dimensions,
                f'width="721" height="{self.first_formula_height}"',
                1,
            )
            mutated = self.note.replace(self.first_formula_picture, malformed, 1)
            self.assert_mutation_fails(mutated)
        with self.subTest("2x density"):
            malformed = self.first_formula_picture.replace(
                dimensions,
                f'width="{self.first_formula_width + 1}" '
                f'height="{self.first_formula_height}"',
                1,
            )
            mutated = self.note.replace(self.first_formula_picture, malformed, 1)
            self.assert_mutation_fails(mutated)

    def test_formula_picture_theme_dimensions_must_match(self) -> None:
        original_dimensions = rebuild.png_dimensions

        def mismatched_dimensions(path: Path) -> tuple[int, int]:
            width, height = original_dimensions(path)
            if path.name == f"{self.first_formula_stem}-dark.png":
                return width + 2, height
            return width, height

        with mock.patch.object(
            rebuild,
            "png_dimensions",
            side_effect=mismatched_dimensions,
        ):
            self.assert_mutation_fails(self.note)

    def test_formula_manifest_must_use_v2_pair_hashes_and_dimensions(self) -> None:
        manifest = json.loads(self.formula_manifest)
        manifest["version"] = 1
        self.assert_mutation_fails(
            self.note,
            formula_manifest=json.dumps(manifest),
        )

        manifest = json.loads(self.formula_manifest)
        entry = manifest["formulas"][self.first_formula_stem]
        entry["dark_png_sha256"] = "0" * 64
        self.assert_mutation_fails(
            self.note,
            formula_manifest=json.dumps(manifest),
        )

        manifest = json.loads(self.formula_manifest)
        entry = manifest["formulas"][self.first_formula_stem]
        entry["display_width"] += 1
        self.assert_mutation_fails(
            self.note,
            formula_manifest=json.dumps(manifest),
        )

    def test_legacy_or_extra_formula_png_is_rejected(self) -> None:
        original_glob = Path.glob

        def glob_with_legacy(path: Path, pattern: str):
            results = list(original_glob(path, pattern))
            if path.resolve() == self.formula_directory.resolve():
                results.append(path / f"{self.first_formula_stem}.png")
            return iter(results)

        with mock.patch.object(Path, "glob", new=glob_with_legacy):
            self.assert_mutation_fails(self.note)

    def test_formula_assets_cannot_cross_note_directories(self) -> None:
        dark_target = self.first_formula_match.group("dark")
        mutated = self.note.replace(
            dark_target,
            dark_target.replace(
                f"assets/notes/{self.note_path.stem}/",
                "assets/notes/another-note/",
                1,
            ),
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_source_link_is_required(self) -> None:
        mutated = self.note.replace(
            self.first_formula_source_link,
            "[可复制 TeX](../../assets/notes/another-note/"
            "formulas/copyable-source.txt)",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_source_link_must_be_unique(self) -> None:
        source_link = self.first_formula_source_link
        mutated = self.note.replace(
            source_link,
            f"{source_link} · {source_link}",
            1,
        )
        self.assert_mutation_fails(mutated)

    def test_formula_source_anchor_rejects_upstream_line_drift(self) -> None:
        marker = f"% BEGIN {self.first_formula_stem}"
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
        mutated = re.sub(
            r"Eq\. \(\d+\)",
            "Eq. (X)",
            self.note,
            count=1,
        )
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
        marker_match = re.search(
            r"^\*\*原文公式：\*\*[^\n]+$",
            self.note,
            re.MULTILINE,
        )
        assert marker_match is not None
        marker = marker_match.group(0)
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


class TranslationFirstReadingValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.future_path = (
            ROOT / "notes" / "2026" / "2026-07-26-future-paper.md"
        )
        cls.valid_note = """# 2026-07-26 — Future Paper

## 阅读起点：术语先导与摘要完整翻译

### 首次术语解释

- **鸟瞰视图（Bird's-eye view, BEV）**：把车辆周围的多视角观测转换到俯视坐标系中的统一空间表示。
- **占据状态（Occupancy）**：描述三维空间单元是否被物体占据以及可能所属语义类别的表示。
- **反事实推理（Counterfactual reasoning）**：分析没有实际发生的候选行为及其可能后果的推理过程。

专业名词均在首次出现时解释，并按照本文语境锁定标准中文译法与后续写法。

### 摘要完整专业中文翻译

<a id="abstract-a01"></a>
> **[原文翻译] Abstract · PDF p. 1 · A01**
>
> 本文研究复杂道路环境中的统一感知问题。现有系统往往把目标检测、场景表示和行为推理拆成彼此独立的任务，因此难以利用任务之间互补的信息。为解决这一问题，作者提出一种联合学习框架，把多视角视觉观测转换为结构化鸟瞰表示，并用显式查询连接交通参与者、道路结构和候选驾驶行为。该方法在多个公开数据集上进行训练和评测，在保持三维感知能力的同时改善了场景理解与行为推理结果。实验还表明，各监督信号之间的联合优化以及严格的时序对齐都对最终性能至关重要。

## 1. 看图：论文到底做了什么

图文教学内容。

## 2. 读公式：核心机制怎样表达

公式教学内容。

## 3. 看结果：证据是否支持主张

### 原文公开的实验配置

**统一来源锚点：** 论文 Section 4，PDF p. 6–8；[官方配置 @ 固定 SHA](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/config.py#L1-L20)。

| 配置项 | 公开值或做法 | 来源锚点 |
|---|---|---|
| 数据集与划分 | 使用公开训练集、验证集和官方测试划分 | 论文 Section 4.1，PDF p. 6 |
| 输入与预处理 | 使用六路环视相机并执行统一尺度预处理 | 论文 §4.1，PDF p. 6 |
| 优化器与训练周期 | 使用公开优化器参数和二十四轮训练 | 论文 Section 4.2，PDF p. 7 |
| 训练硬件与随机种子 | 作者没有报告随机种子和完整硬件型号 | [未核验] 原文未报告 |
| 指标与基线 | 使用官方感知、语言和规划评测脚本 | 论文 §4.3，PDF p. 8 |

### 原文公开的实验流程

**统一来源锚点：** 论文 Section 4，PDF p. 6–8；[运行入口 @ 固定 SHA](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/tools/run.py#L1-L20)。

1. **数据准备：** [论文] 校验标定、时序索引和官方划分（论文 Section 4.1，PDF p. 6）。
2. **训练阶段：** [源码] 生成统一表示并按公开损失训练（论文 Section 4.2，PDF p. 7）。
3. **验证与选模：** [未核验] 作者未报告完整的选模与重复实验策略。
4. **推理与后处理：** [论文] 按官方流程组装多视角输入（论文 §4.3，PDF p. 8）。
5. **最终评测：** [源码] 调用官方脚本计算全部主指标（论文 Section 4.3，PDF p. 8）。

## 4. 对源码：公式如何落地

源码核对内容。

## 5. 记结论：贡献、边界与开放问题

### 原文结论完整翻译

<a id="conclusion-c01"></a>
> **[原文翻译] Conclusion · PDF p. 12 · C01**
>
> 作者总结，统一的场景表示能够连接多视角感知、结构化环境理解和候选行为推理。通过在公开基准上的系统实验，该框架在主要感知指标上取得了具有竞争力的结果，并证明联合监督与时序对齐是性能提升的重要来源。作者同时强调，这些结果只覆盖所采用的数据分布与离线评测协议，不能直接等同于真实车辆中的闭环安全性。

### 原文局限与展望完整翻译

<a id="limitations-l01"></a>
> **[原文翻译] Limitations / Discussion · PDF p. 12 · L01**
>
> 作者指出，当前实验仍依赖规模有限且地域分布受限的数据，模型面对极端天气、罕见交通参与者和传感器异常时的可靠性尚未得到充分验证。

<a id="future-work-o01"></a>
> **[原文翻译] Future Work / Outlook · PDF p. 12 · O01**
>
> 未来工作将扩展跨城市和跨传感器评测，引入能够反映其他交通参与者反应的交互式闭环环境，并研究不确定性估计、失效检测以及更高效的部署方案。

### 笔记分析与研究启发

**[笔记解释]** 这项工作的关键接口使感知证据可以进入后续推理，而不只是并列训练多个任务。

**[判断]** 开放环指标仍可能受到数据集先验和自车状态捷径影响，因此正式复现时应加入跨区域压力测试、输入破坏实验和交互式闭环评测。这个研究启发属于笔记作者基于证据作出的分析，不能混写成论文作者的原始结论。
"""

    def validate(self, note: str, path: Path | None = None) -> None:
        rebuild.validate_translation_first_reading(
            path or self.future_path,
            "2",
            structure=rebuild.scan_markdown(note),
        )

    def assert_invalid(self, note: str) -> None:
        with self.assertRaises(rebuild.ValidationFailure):
            self.validate(note)

    def test_complete_translation_first_note_passes(self) -> None:
        self.validate(self.valid_note)

    def test_no_historical_note_is_exempt_from_translation_contract(self) -> None:
        with self.assertRaises(rebuild.ValidationFailure):
            rebuild.validate_translation_first_reading(
                ROOT / "notes" / "2026" / "2026-07-24-st-occ.md",
                "2",
                structure=rebuild.scan_markdown("# Legacy note\n"),
            )
        self.validate(
            self.valid_note,
            ROOT / "notes" / "2026" / "2026-07-23-compliant-backfill.md",
        )

    def test_any_note_cannot_keep_legacy_shape(self) -> None:
        self.assert_invalid(
            "# 2026-07-25 — Legacy shape\n\n"
            + "\n\n".join(rebuild.REQUIRED_NOTE_HEADINGS)
        )

    def test_every_required_subsection_is_enforced(self) -> None:
        for title in rebuild.REQUIRED_READING_SUBSECTIONS:
            with self.subTest(section=title):
                mutated = re.sub(
                    rf"^### (?:\d+(?:\.\d+)*[.)]?\s+)?{re.escape(title)}\n"
                    r".*?(?=^##{2,3} |\Z)",
                    "",
                    self.valid_note,
                    count=1,
                    flags=re.MULTILINE | re.DOTALL,
                )
                self.assert_invalid(mutated)

    def test_hidden_required_section_does_not_count(self) -> None:
        opener = self.valid_note.index("### 原文公开的实验配置")
        closer = self.valid_note.index("### 原文公开的实验流程")
        mutated = (
            self.valid_note[:opener]
            + "<details>\n<summary>hidden</summary>\n\n"
            + self.valid_note[opener:closer]
            + "</details>\n\n"
            + self.valid_note[closer:]
        )
        self.assert_invalid(mutated)

    def test_translation_requires_matching_stable_anchor(self) -> None:
        mutated = self.valid_note.replace(
            '<a id="abstract-a01"></a>',
            '<a id="abstract-a02"></a>',
            1,
        )
        self.assert_invalid(mutated)

    def test_translation_header_requires_numeric_pdf_page(self) -> None:
        mutated = self.valid_note.replace(
            "Abstract · PDF p. 1 · A01",
            "Abstract · 原文附近 · A01",
            1,
        )
        self.assert_invalid(mutated)
        section_name_only = self.valid_note.replace(
            "Abstract · PDF p. 1 · A01",
            "Abstract · Abstract · A01",
            1,
        )
        self.assert_invalid(section_name_only)

    def test_translation_and_reader_analysis_cannot_mix(self) -> None:
        mutated = self.valid_note.replace(
            "> 本文研究复杂道路环境",
            "> **[笔记解释]** [判断] 我认为。\n>\n> 本文研究复杂道路环境",
            1,
        )
        self.assert_invalid(mutated)

    def test_abstract_translation_cannot_be_a_short_summary(self) -> None:
        start = self.valid_note.index(
            "> 本文研究复杂道路环境中的统一感知问题"
        )
        end = self.valid_note.index("\n\n## 1.", start)
        mutated = (
            self.valid_note[:start]
            + "> 本文提出一种自动驾驶感知方法并进行了实验。"
            + self.valid_note[end:]
        )
        self.assert_invalid(mutated)

    def test_glossary_requires_explained_bilingual_terms(self) -> None:
        mutated = self.valid_note.replace(
            "- **反事实推理（Counterfactual reasoning）**："
            "分析没有实际发生的候选行为及其可能后果的推理过程。\n",
            "",
            1,
        )
        self.assert_invalid(mutated)

    def test_glossary_must_precede_abstract_translation(self) -> None:
        glossary_start = self.valid_note.index("### 首次术语解释")
        abstract_start = self.valid_note.index("### 摘要完整专业中文翻译")
        main_start = self.valid_note.index("## 1. 看图")
        glossary = self.valid_note[glossary_start:abstract_start]
        abstract = self.valid_note[abstract_start:main_start]
        mutated = (
            self.valid_note[:glossary_start]
            + abstract
            + glossary
            + self.valid_note[main_start:]
        )
        self.assert_invalid(mutated)

    def test_experiment_config_rows_need_specific_sources(self) -> None:
        mutated = self.valid_note.replace(
            "论文 Section 4.1，PDF p. 6",
            "论文实验部分附近",
            1,
        )
        self.assert_invalid(mutated)

    def test_mobile_config_bullets_need_their_own_specific_sources(self) -> None:
        config_start = self.valid_note.index(
            "### 原文公开的实验配置"
        )
        flow_start = self.valid_note.index(
            "### 原文公开的实验流程",
            config_start,
        )
        mobile_config = """### 原文公开的实验配置

**统一来源锚点：** 论文 Section 4，PDF p. 6–8；[官方配置 @ 固定 SHA](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/config.py#L1-L20)。

- **数据集与划分。** **[论文]** 使用官方训练与验证划分；来源：论文 Section 4.1，PDF p. 6。
- **输入与预处理。** **[论文]** 使用六路相机并统一缩放；
  来源：论文 §4.1，PDF p. 6。
- **模型初始化。** **[源码]** 使用公开预训练权重；来源：[固定 SHA 配置](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/config.py#L21-L30)。
- **优化器。** **[论文]** 使用作者报告的优化设置；来源：论文 Section 4.2，PDF p. 7。
- **训练周期。** **[源码]** 按公开配置完成训练；来源：[固定 SHA 配置](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/config.py#L31-L40)。
- **随机性。** **[未核验]** 原文未报告随机种子、重复次数或误差条。
- **推理设置。** **[源码]** 使用公开推理入口；来源：[固定 SHA 脚本](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/tools/run.py#L1-L20)。
- **指标与基线。** **[论文]** 使用官方评测协议；来源：论文 Section 4.3，PDF p. 8。

"""
        mobile_note = (
            self.valid_note[:config_start]
            + mobile_config
            + self.valid_note[flow_start:]
        )
        self.validate(mobile_note)
        mutated = mobile_note.replace(
            "来源：论文 Section 4.1，PDF p. 6。",
            "来源：论文实验部分附近。",
            1,
        )
        self.assert_invalid(mutated)

    def test_experiment_flow_requires_five_sourced_stages(self) -> None:
        mutated = self.valid_note.replace(
            "[源码] 调用官方脚本计算全部主指标",
            "调用官方脚本计算全部主指标",
            1,
        )
        self.assert_invalid(mutated)
        vague_source = self.valid_note.replace(
            "1. **数据准备：** [论文] 校验标定、时序索引和官方划分"
            "（论文 Section 4.1，PDF p. 6）。",
            "1. **数据准备：** [论文] 校验标定、时序索引和官方划分"
            "（论文实验部分附近）。",
            1,
        )
        self.assert_invalid(vague_source)

    def test_real_closing_section_can_replace_absent_conclusion(self) -> None:
        marker = "### 原文结论完整翻译\n\n"
        declaration = (
            "**原文缺失声明：** 论文没有独立 Conclusion；已检查真实收束章节 "
            "Discussion，本节忠实翻译该连续段落，不冒充、不改写为作者未设置"
            "的 Conclusion。\n\n"
        )
        discussion_note = self.valid_note.replace(
            marker,
            marker + declaration,
            1,
        ).replace(
            "[原文翻译] Conclusion · PDF p. 12 · C01",
            "[原文翻译] Discussion · §5 Discussion / PDF p. 12 · C01",
            1,
        )
        self.validate(discussion_note)
        self.assert_invalid(discussion_note.replace(declaration, "", 1))

    def test_every_dated_note_is_indexed_exactly_once(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            notes = root / "notes" / "2026"
            notes.mkdir(parents=True)
            dated = notes / "2026-07-26-paper.md"
            dated.write_text("# note\n", encoding="utf-8")
            (notes / "README.md").write_text("# guide\n", encoding="utf-8")
            row = {"note_path": "notes/2026/2026-07-26-paper.md"}

            rebuild.validate_dated_note_inventory([row], root=root)
            with self.assertRaises(rebuild.ValidationFailure):
                rebuild.validate_dated_note_inventory([], root=root)
            with self.assertRaises(rebuild.ValidationFailure):
                rebuild.validate_dated_note_inventory([row, row], root=root)

    def test_absent_future_work_requires_non_invention_declaration(self) -> None:
        start = self.valid_note.index('<a id="future-work-o01"></a>')
        end = self.valid_note.index("### 笔记分析与研究启发")
        declaration = (
            "**原文缺失声明：** 原文未单列独立的 Future Work 或展望；"
            "已检查结论与附录，本节不代写作者观点。\n\n"
        )
        mutated = self.valid_note[:start] + declaration + self.valid_note[end:]
        self.validate(mutated)
        self.assert_invalid(mutated.replace("不代写", "将补写", 1))

    def test_analysis_requires_existing_explanation_and_judgment_labels(self) -> None:
        mutated = self.valid_note.replace("**[判断]**", "**分析**", 1)
        self.assert_invalid(mutated)

    def test_real_st_occ_note_meets_the_new_contract(self) -> None:
        note_path = ROOT / "notes" / "2026" / "2026-07-24-st-occ.md"
        structure = rebuild.scan_markdown(
            note_path.read_text(encoding="utf-8")
        )
        rebuild.validate_translation_first_reading(
            note_path,
            "3",
            structure=structure,
        )
        rebuild.validate_architecture_reading(
            note_path,
            "3",
            structure=structure,
            code_audit_status="Audited",
            repo_commit="1633f62e2e6677a5fa474905977acfeca4e7819e",
            repo_url="https://github.com/matthew-leng/ST-Occ",
        )


class ArchitectureReadingValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.note_path = (
            ROOT / "notes" / "2026" / "2026-07-26-architecture-paper.md"
        )
        cls.valid_note = """# 2026-07-26 — Architecture Paper

## 1. 看图：论文到底做了什么

### 整体算法架构与创新设计

**原方法瓶颈：** **[论文]** 旧方法需要保存多份稠密历史表示，计算与显存会随序列长度持续增长。来源：论文 §1，PDF p. 1。

**主干网络与基线：** **[论文/源码]** 使用 ResNet-50、FPN 和公开单帧基线，先得到当前三维表示。来源：论文 §3.1，PDF p. 4；[固定 SHA 配置](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/config.py#L1-L20)。

**继承与新增边界：** **[论文/源码]** ResNet 与预测头沿用基线；本文只新增场景记忆和可信融合模块。来源：论文 §3.2，PDF p. 5；[固定 SHA 实现](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/model.py#L1-L20)。

**端到端信息流：** **[论文]** 多相机图像进入 backbone 和 encoder，当前表示读取历史状态，经新增模块融合后进入预测头并写回状态。来源：论文 Figure 2 / §3，PDF p. 4。

**总体训练方式：** **[论文/源码]** 先训练单帧分支，再联合优化分类损失、时序损失和状态更新路径。来源：论文 §3.4，PDF p. 6；[固定 SHA 配置](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/config.py#L21-L40)。

#### 创新模块 1：Scene Memory

**位置与接口：** 位于当前帧编码器和时序融合模块之间，负责跨帧保存可检索状态。

**输入：** 当前三维表示、历史场景状态、车辆位姿和有效位置掩码。

**内部变换：** 把局部网格映射到场景坐标，读取同一真实位置的历史，再按索引更新对应区域。

**输出：** 对齐后的历史表示，以及供下一帧继续使用的更新场景状态。

**为什么这样设计：** **[判断]** 这是本笔记根据前述瓶颈与论文结构所做的因果重建，不是作者原句：为了解决逐帧队列随时间增长的问题，用真实场景位置作为地址可以避免保存多份重复历史。

**训练信号：** **[论文]** 模块没有单独标签，通过最终分类损失和时序一致性损失联合训练。来源：论文 §3.4，PDF p. 6。

**作用与证据：** **[论文]** Table 2 的受控消融显示加入该模块后主指标提高，但论文没有把读取和写回再分别消融。来源：论文 Table 2，PDF p. 8。

**论文位置：** **[论文]** Figure 2 与 §3.2，PDF p. 4–5。

**源码入口：** **[源码]** [SceneMemory @ 固定 SHA](https://github.com/example/repo/blob/0123456789abcdef0123456789abcdef01234567/model.py#L41-L90)。

## 2. 读公式：核心机制怎样表达
"""

    def validate(
        self,
        note: str,
        *,
        repo_commit: str = "0123456789abcdef0123456789abcdef01234567",
        repo_url: str = "https://github.com/example/repo",
        code_audit_status: str = "Audited",
    ) -> None:
        rebuild.validate_architecture_reading(
            self.note_path,
            "2",
            structure=rebuild.scan_markdown(note),
            code_audit_status=code_audit_status,
            repo_commit=repo_commit,
            repo_url=repo_url,
        )

    def assert_invalid(self, note: str) -> None:
        with self.assertRaises(rebuild.ValidationFailure):
            self.validate(note)

    def test_complete_architecture_card_passes(self) -> None:
        self.validate(self.valid_note)

    def test_every_overview_field_is_required(self) -> None:
        for field in rebuild.ARCHITECTURE_OVERVIEW_LABELS:
            with self.subTest(field=field):
                mutated = re.sub(
                    rf"^\*\*{re.escape(field)}：\*\*.*?(?=^\*\*|^####)",
                    "",
                    self.valid_note,
                    count=1,
                    flags=re.MULTILINE | re.DOTALL,
                )
                self.assert_invalid(mutated)

    def test_every_module_field_is_required(self) -> None:
        for field in rebuild.ARCHITECTURE_MODULE_FIELDS:
            with self.subTest(field=field):
                mutated = re.sub(
                    rf"^\*\*{re.escape(field)}：\*\*.*?(?=^\*\*|^##)",
                    "",
                    self.valid_note,
                    count=1,
                    flags=re.MULTILINE | re.DOTALL,
                )
                self.assert_invalid(mutated)

    def test_design_rationale_must_be_causal(self) -> None:
        mutated = self.valid_note.replace(
            "**[判断]** 这是本笔记根据前述瓶颈与论文结构所做的因果重建，"
            "不是作者原句：为了解决逐帧队列随时间增长的问题，用真实场景"
            "位置作为地址可以避免保存多份重复历史。",
            "该模块使用真实场景位置作为地址，并且保存一份场景历史状态。",
            1,
        )
        self.assert_invalid(mutated)

    def test_design_rationale_accepts_sourced_paper_motivation(self) -> None:
        mutated = re.sub(
            r"(?m)^\*\*为什么这样设计：\*\*.*$",
            "**为什么这样设计：** **[论文]** 作者为了解决逐帧队列随时间"
            "增长的瓶颈，使用真实场景位置作为地址，从而避免保存多份重复"
            "历史。来源：论文 §3.2，PDF p. 5。",
            self.valid_note,
            count=1,
        )
        self.validate(mutated)

    def test_design_rationale_rejects_unlabeled_inference(self) -> None:
        mutated = self.valid_note.replace(
            "**[判断]** 这是本笔记根据前述瓶颈与论文结构所做的因果重建，"
            "不是作者原句：",
            "",
            1,
        )
        self.assert_invalid(mutated)

    def test_reconstructed_motivation_must_disclaim_author_wording(self) -> None:
        mutated = self.valid_note.replace(
            "这是本笔记根据前述瓶颈与论文结构所做的因果重建，不是作者原句",
            "本文笔记判断上述内容完全来自作者，并根据前述瓶颈做因果重建",
            1,
        )
        self.assert_invalid(mutated)

    def test_paper_motivation_needs_a_paper_anchor_not_only_code(self) -> None:
        mutated = re.sub(
            r"(?m)^\*\*为什么这样设计：\*\*.*$",
            "**为什么这样设计：** **[论文]** 作者为了解决逐帧队列增长，"
            "采用场景地址，从而避免重复历史。来源："
            "[固定 SHA](https://github.com/example/repo/blob/"
            "0123456789abcdef0123456789abcdef01234567/model.py#L1-L20)。",
            self.valid_note,
            count=1,
        )
        self.assert_invalid(mutated)

    def test_module_effect_requires_ablation_or_explicit_absence(self) -> None:
        mutated = self.valid_note.replace(
            "Table 2 的受控消融显示加入该模块后主指标提高，但论文没有把读取"
            "和写回再分别消融。来源：论文 Table 2，PDF p. 8。",
            "该模块很重要而且能够提高最终效果。来源：论文 §3，PDF p. 8。",
            1,
        )
        self.assert_invalid(mutated)

    def test_method_figure_cannot_masquerade_as_effect_evidence(self) -> None:
        mutated = re.sub(
            r"(?m)^\*\*作用与证据：\*\*.*$",
            "**作用与证据：** **[论文]** Figure 2 只画出该模块，笔记据此"
            "声称结果提高。来源：论文 Figure 2，PDF p. 4。",
            self.valid_note,
            count=1,
        )
        self.assert_invalid(mutated)

    def test_negative_control_word_is_not_empirical_evidence(self) -> None:
        mutated = re.sub(
            r"(?m)^\*\*作用与证据：\*\*.*$",
            "**作用与证据：** **[论文]** 作者没有做任何受控对照，但这个"
            "模块肯定有效。来源：论文 §3，PDF p. 4。",
            self.valid_note,
            count=1,
        )
        self.assert_invalid(mutated)

    def test_whole_system_result_cannot_replace_module_ablation(self) -> None:
        mutated = re.sub(
            r"(?m)^\*\*作用与证据：\*\*.*$",
            "**作用与证据：** **[论文]** 论文没有做该模块的独立消融；"
            "Table 2 只是整套系统主结果提高 1.0 点，因此仍不能把增益归因"
            "给该模块。来源：论文 Table 2，PDF p. 8。",
            self.valid_note,
            count=1,
        )
        self.assert_invalid(mutated)

    def test_explicit_absence_of_independent_ablation_passes(self) -> None:
        mutated = re.sub(
            r"(?m)^\*\*作用与证据：\*\*.*$",
            "**作用与证据：** **[未核验]** 原文未提供该模块的独立消融或"
            "受控对照，因此不能把整套系统增益单独归因给它。来源：论文 "
            "§3.2，PDF p. 5。",
            self.valid_note,
            count=1,
        )
        self.validate(mutated)

    def test_module_source_requires_fixed_sha(self) -> None:
        mutated = self.valid_note.replace(
            "https://github.com/example/repo/blob/"
            "0123456789abcdef0123456789abcdef01234567/model.py#L41-L90",
            "https://github.com/example/repo/blob/main/model.py",
            1,
        )
        self.assert_invalid(mutated)

    def test_fixed_sha_source_must_match_official_repository(self) -> None:
        mutated = self.valid_note.replace(
            "https://github.com/example/repo/blob/",
            "https://github.com/attacker/unrelated/blob/",
        )
        self.assert_invalid(mutated)

    def test_repo_commit_comparison_is_case_insensitive(self) -> None:
        self.validate(
            self.valid_note,
            repo_commit="0123456789ABCDEF0123456789ABCDEF01234567",
        )

    def test_fixed_sha_source_requires_source_provenance(self) -> None:
        mutated = self.valid_note.replace(
            "**源码入口：** **[源码]**",
            "**源码入口：**",
            1,
        )
        self.assert_invalid(mutated)

    def test_audited_note_cannot_claim_source_is_unavailable(self) -> None:
        mutated = re.sub(
            r"(?m)^\*\*源码入口：\*\*.*$",
            "**源码入口：** **[未核验]** 作者未提供官方源码，无法确认实现。",
            self.valid_note,
            count=1,
        )
        self.assert_invalid(mutated)

    def test_no_official_code_and_not_audited_are_distinct(self) -> None:
        no_official_code = re.sub(
            r"(?m)^\*\*源码入口：\*\*.*$",
            "**源码入口：** **[未核验]** 作者未提供官方源码，无法确认该创新"
            "单元在任何公开实现中的具体落点。",
            self.valid_note,
            count=1,
        )
        self.validate(
            no_official_code,
            repo_commit="",
            repo_url="",
            code_audit_status="NoOfficialCode",
        )
        with self.assertRaises(rebuild.ValidationFailure):
            self.validate(
                no_official_code,
                repo_commit="",
                repo_url="",
                code_audit_status="NotAudited",
            )

        pending_audit = re.sub(
            r"(?m)^\*\*源码入口：\*\*.*$",
            "**源码入口：** **[未核验]** 官方仓库存在，但尚未完成源码审计，"
            "当前不声称已经确认该模块的真实实现落点。",
            self.valid_note,
            count=1,
        )
        self.validate(
            pending_audit,
            repo_commit="",
            repo_url="https://github.com/example/repo",
            code_audit_status="NotAudited",
        )
        with self.assertRaises(rebuild.ValidationFailure):
            self.validate(
                pending_audit,
                repo_commit="",
                repo_url="",
                code_audit_status="NoOfficialCode",
            )

    def test_paper_location_requires_paper_provenance(self) -> None:
        mutated = self.valid_note.replace(
            "**论文位置：** **[论文]**",
            "**论文位置：** **[源码]**",
            1,
        )
        self.assert_invalid(mutated)

    def test_overview_fields_must_begin_their_own_paragraph(self) -> None:
        mutated = self.valid_note.replace(
            "\n\n**主干网络与基线：**",
            " **主干网络与基线：**",
            1,
        )
        self.assert_invalid(mutated)

    def test_module_fields_must_begin_their_own_paragraph(self) -> None:
        mutated = self.valid_note.replace(
            "\n\n**输入：**",
            " **输入：**",
            1,
        )
        self.assert_invalid(mutated)

    def test_overview_field_must_be_substantive_and_own_its_source(self) -> None:
        short = re.sub(
            r"(?m)^\*\*原方法瓶颈：\*\*.*$",
            "**原方法瓶颈：** **[论文]** 缺陷。来源：论文 §1，PDF p. 1。",
            self.valid_note,
            count=1,
        )
        self.assert_invalid(short)
        missing_anchor = re.sub(
            r"(?m)^\*\*原方法瓶颈：\*\*.*$",
            "**原方法瓶颈：** **[论文]** 旧方法需要保存多份稠密历史表示，"
            "计算、显存与状态重复会随序列长度不断增长，而且历史误差会被"
            "反复传播。",
            self.valid_note,
            count=1,
        )
        self.assert_invalid(missing_anchor)

    def _append_second_card(self, number: int = 2) -> str:
        start = self.valid_note.index("#### 创新模块 1：Scene Memory")
        end = self.valid_note.index("\n## 2. 读公式")
        card = self.valid_note[start:end]
        card = card.replace(
            "#### 创新模块 1：Scene Memory",
            f"#### 创新模块 {number}：Second Unit",
            1,
        )
        return self.valid_note[:end] + "\n\n" + card + self.valid_note[end:]

    def test_card_numbers_are_continuous_and_unique(self) -> None:
        self.validate(self._append_second_card(2))
        self.assert_invalid(self._append_second_card(1))
        self.assert_invalid(self._append_second_card(3))

    def test_card_names_are_unique_independent_of_number(self) -> None:
        duplicated_name = self._append_second_card(2).replace(
            "#### 创新模块 2：Second Unit",
            "#### 创新模块 2：Scene Memory",
            1,
        )
        self.assert_invalid(duplicated_name)

    def test_non_network_innovation_unit_is_supported(self) -> None:
        mutated = self.valid_note.replace(
            "#### 创新模块 1：Scene Memory",
            "#### 创新单元 1：Dataset Construction Protocol",
            1,
        )
        self.validate(mutated)

    def test_architecture_h3_must_have_section_one_as_parent(self) -> None:
        mutated = self.valid_note.replace(
            "### 整体算法架构与创新设计",
            "## 9. 临时附录\n\n### 整体算法架构与创新设计",
            1,
        )
        self.assert_invalid(mutated)

    def test_architecture_markdown_tables_are_rejected(self) -> None:
        mutated = self.valid_note.replace(
            "#### 创新模块 1：Scene Memory",
            "| 模块 | 输入 | 输出 |\n|---|---|---|\n| memory | 当前 | 历史 |\n\n"
            "#### 创新模块 1：Scene Memory",
            1,
        )
        self.assert_invalid(mutated)
        without_outer_pipes = self.valid_note.replace(
            "#### 创新模块 1：Scene Memory",
            "模块 | 输入 | 输出\n---|---|---\nmemory | 当前 | 历史\n\n"
            "#### 创新模块 1：Scene Memory",
            1,
        )
        self.assert_invalid(without_outer_pipes)
        one_hyphen_separator = self.valid_note.replace(
            "#### 创新模块 1：Scene Memory",
            "| 模块 | 输入 | 输出 |\n|-|-|-|\n| memory | 当前 | 历史 |\n\n"
            "#### 创新模块 1：Scene Memory",
            1,
        )
        self.assert_invalid(one_hyphen_separator)
        quoted_table = self.valid_note.replace(
            "#### 创新模块 1：Scene Memory",
            "> | 模块 | 输入 | 输出 |\n> |-|-|-|\n"
            "> | memory | 当前 | 历史 |\n\n"
            "#### 创新模块 1：Scene Memory",
            1,
        )
        self.assert_invalid(quoted_table)

    def test_architecture_html_table_is_rejected(self) -> None:
        mutated = self.valid_note.replace(
            "#### 创新模块 1：Scene Memory",
            "<table><tr><th>模块</th></tr><tr><td>memory</td></tr></table>\n\n"
            "#### 创新模块 1：Scene Memory",
            1,
        )
        self.assert_invalid(mutated)


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

    def test_notes_policy_rejects_obvious_math_code_pills(self) -> None:
        with mock.patch.object(
            math_lint,
            "requires_static_formula_assets",
            return_value=True,
        ):
            errors = self.lint_text(
                "状态 `M_t`，方差 `delta_p`，位置 `p + f`，"
                "比例 `12.18 / 8.68`。\n"
            )
        self.assertEqual(
            [error.rule for error in errors],
            ["MATH016", "MATH016", "MATH016", "MATH016"],
        )

    def test_standard_inline_notation_and_real_source_names_pass(self) -> None:
        with mock.patch.object(
            math_lint,
            "requires_static_formula_assets",
            return_value=True,
        ):
            text = (
                "状态 *M*<sub>*t*</sub>，方差 *δ*<sub>*p*</sub>，"
                "位置 *p* + ***f***<sub>*p*</sub>。\n"
                "源码字段 `global_feats`，函数 `update_global_single`，"
                "算子 `grid_sample`，方法 `__init__`，配置 `model.py`。\n"
                "源码字段 `s_i` 是实现中的原名。\n"
            )
            self.assertEqual(self.lint_text(text), [])

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


class PerceptionTaxonomyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = rebuild.load_taxonomy()
        cls.rows = rebuild.load_rows()

    def test_taxonomy_has_thirteen_ordered_tracks(self) -> None:
        tracks = self.taxonomy["tracks"]
        self.assertEqual(len(tracks), 13)
        self.assertEqual(
            [track["id"].split("-", 1)[0] for track in tracks],
            [f"p{number:02d}" for number in range(1, 14)],
        )
        for track in tracks:
            with self.subTest(track=track["id"]):
                self.assertTrue(track["intro"].strip())
                self.assertLessEqual(len(track["intro"]), 90)

    def test_every_paper_has_one_valid_track_and_modalities(self) -> None:
        allowed_tracks = {
            track["id"] for track in self.taxonomy["tracks"]
        }
        allowed_modalities = set(self.taxonomy["modalities"])
        for row in self.rows:
            with self.subTest(paper=row["paper_key"]):
                self.assertIn(row["primary_track"], allowed_tracks)
                self.assertTrue(rebuild.modality_list(row))
                self.assertTrue(
                    set(rebuild.modality_list(row)) <= allowed_modalities
                )

    def test_generated_topics_shows_zero_coverage_tracks_too(self) -> None:
        rendered = rebuild.render_topics(self.rows, self.taxonomy)
        for track in self.taxonomy["tracks"]:
            self.assertIn(track["name"], rendered)
            self.assertIn(track["intro"], rendered)
        self.assertIn("13 个方向一分钟速览", rendered)
        self.assertIn("待覆盖", rendered)
        self.assertIn("与大模型结合的感知论文", rendered)
        self.assertIn("按输入模态浏览", rendered)

    def test_coverage_count_is_derived_from_primary_tracks(self) -> None:
        expected = len({row["primary_track"] for row in self.rows})
        stats = rebuild.render_stats(self.rows, self.taxonomy)
        self.assertIn(
            f"覆盖 {expected}/{len(self.taxonomy['tracks'])} 个感知主方向",
            stats,
        )

    def test_invalid_track_and_modality_are_rejected(self) -> None:
        with self.subTest("track"):
            rows = [dict(row) for row in self.rows]
            rows[0]["primary_track"] = "p99-invented"
            with self.assertRaises(rebuild.ValidationFailure):
                rebuild.validate_rows(rows)
        with self.subTest("modality"):
            rows = [dict(row) for row in self.rows]
            rows[0]["modalities"] = "Imaginary Sensor"
            with self.assertRaises(rebuild.ValidationFailure):
                rebuild.validate_rows(rows)


if __name__ == "__main__":
    unittest.main()
