#!/usr/bin/env python3
"""Validate and build the protocol-aware SOTA and transfer-opportunity radars.

The two CSV files are the machine-readable sources of truth.  Human-facing
pages deliberately use narrow cards instead of wide Markdown tables so they
remain readable on GitHub mobile and iPad layouts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOTA_CSV_PATH = ROOT / "index" / "sota.csv"
TRANSFER_CSV_PATH = ROOT / "index" / "transfer.csv"
TRANSFER_ZH_PATH = ROOT / "index" / "transfer_zh.json"
TAXONOMY_PATH = ROOT / "index" / "taxonomy.json"
SOTA_MD_PATH = ROOT / "sota" / "README.md"
TRANSFER_MD_PATH = ROOT / "transfer" / "README.md"

SOTA_FIELDS = (
    "snapshot_date",
    "sota_key",
    "primary_track",
    "task",
    "benchmark",
    "dataset_version",
    "split",
    "modalities",
    "protocol",
    "record_kind",
    "method",
    "year",
    "publication_status",
    "venue",
    "metric",
    "metric_direction",
    "value",
    "unit",
    "secondary_metrics",
    "paper_url",
    "proceedings_url",
    "leaderboard_url",
    "code_url",
    "verification_note",
    "boundary",
)

TRANSFER_FIELDS = (
    "snapshot_date",
    "candidate_key",
    "source_domain",
    "method",
    "source_year",
    "source_venue",
    "source_status",
    "source_proceedings_url",
    "paper_url",
    "repo_url",
    "repo_commit",
    "license",
    "source_task",
    "source_evidence",
    "ad_target_track",
    "ad_target_task",
    "transfer_interface",
    "adaptation_hypothesis",
    "query_problem",
    "query_mechanism",
    "query_synonym",
    "search_sources",
    "closest_works",
    "coverage_verdict",
    "collision_level",
    "highlight",
    "priority_score",
    "next_refresh",
    "minimum_test",
    "rollback_baseline",
    "falsifier",
    "main_failure",
    "public_boundary",
)

SOTA_KINDS = {
    "OfficialLeaderboardSnapshot",
    "PaperReportedFrontier",
    "BenchmarkAnchor",
    "NoSingleLeaderboard",
}
SOTA_STATUSES = {"Accepted", "Preprint", "LeaderboardSubmission", "Benchmark"}
METRIC_DIRECTIONS = {"higher", "lower", "mixed", "not-applicable"}
TRANSFER_STATUSES = {"Accepted", "Preprint"}
TRANSFER_VERDICTS = {
    "[已覆盖]",
    "[部分覆盖]",
    "[本次检索未找到直接覆盖]",
    "[检索受阻]",
}
HIGHLIGHT_VERDICT = "[本次检索未找到直接覆盖]"
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
PROHIBITED_NOVELTY_RE = re.compile(
    r"学界无人|从未有人|没有任何人|绝对首次|确定空白|肯定空白|尚无任何"
)
PUBLIC_BOUNDARY_PHRASE = "截至日期，在列明范围内本次未找到直接覆盖"
LIST_SEPARATOR = ";;"
TRANSFER_ZH_FIELDS = (
    "summary",
    "target",
    "source_evidence",
    "transfer_interface",
    "adaptation_hypothesis",
    "minimum_test",
    "rollback_baseline",
    "falsifier",
    "main_failure",
)


class ValidationFailure(RuntimeError):
    """Raised when a radar source or generated page violates the contract."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate sources and fail when generated pages are stale",
    )
    return parser.parse_args()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def load_taxonomy() -> dict[str, object]:
    return json.loads(read_text(TAXONOMY_PATH))


def load_csv(path: Path, expected_fields: tuple[str, ...]) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != expected_fields:
            raise ValidationFailure(
                f"{path.relative_to(ROOT).as_posix()} header does not match the "
                "current schema"
            )
        return [
            {field: (value or "").strip() for field, value in row.items()}
            for row in reader
        ]


def load_sota_rows() -> list[dict[str, str]]:
    return load_csv(SOTA_CSV_PATH, SOTA_FIELDS)


def load_transfer_rows() -> list[dict[str, str]]:
    return load_csv(TRANSFER_CSV_PATH, TRANSFER_FIELDS)


def load_transfer_zh() -> dict[str, dict[str, str]]:
    payload = json.loads(read_text(TRANSFER_ZH_PATH))
    if not isinstance(payload, dict):
        raise ValidationFailure("index/transfer_zh.json must be an object")
    return payload


def parse_date(value: str, field: str, line: int) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationFailure(
            f"CSV line {line}: {field} must use YYYY-MM-DD"
        ) from exc


def validate_url(value: str, field: str, line: int, *, required: bool = True) -> None:
    if not value:
        if required:
            raise ValidationFailure(f"CSV line {line}: {field} is required")
        return
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValidationFailure(f"CSV line {line}: {field} must be a public HTTP(S) URL")
    if parsed.hostname in {"localhost", "127.0.0.1"}:
        raise ValidationFailure(f"CSV line {line}: {field} cannot be local")


def split_list(value: str) -> list[str]:
    return [item.strip() for item in value.split(LIST_SEPARATOR) if item.strip()]


def track_maps(taxonomy: dict[str, object]) -> tuple[set[str], dict[str, str]]:
    tracks = taxonomy["tracks"]
    assert isinstance(tracks, list)
    ids = {str(track["id"]) for track in tracks}
    names = {str(track["id"]): str(track["name"]) for track in tracks}
    return ids, names


def validate_sota_rows(
    rows: list[dict[str, str]], taxonomy: dict[str, object] | None = None
) -> None:
    if not rows:
        raise ValidationFailure("index/sota.csv must contain at least one record")
    taxonomy = taxonomy or load_taxonomy()
    allowed_tracks, _ = track_maps(taxonomy)
    allowed_modalities = set(taxonomy["modalities"])
    keys: set[str] = set()
    covered_tracks: set[str] = set()

    for line, row in enumerate(rows, start=2):
        missing = [field for field in SOTA_FIELDS if field not in row]
        if missing:
            raise ValidationFailure(f"CSV line {line}: missing fields {', '.join(missing)}")
        for field in (
            "snapshot_date",
            "sota_key",
            "primary_track",
            "task",
            "benchmark",
            "protocol",
            "record_kind",
            "method",
            "year",
            "publication_status",
            "venue",
            "metric",
            "metric_direction",
            "paper_url",
            "verification_note",
            "boundary",
        ):
            if not row[field]:
                raise ValidationFailure(f"CSV line {line}: {field} is required")

        parse_date(row["snapshot_date"], "snapshot_date", line)
        try:
            year = int(row["year"])
        except ValueError as exc:
            raise ValidationFailure(f"CSV line {line}: year must be an integer") from exc
        if not 2010 <= year <= 2100:
            raise ValidationFailure(f"CSV line {line}: implausible year {year}")
        if row["sota_key"] in keys:
            raise ValidationFailure(f"CSV line {line}: duplicate sota_key")
        keys.add(row["sota_key"])
        if row["primary_track"] not in allowed_tracks:
            raise ValidationFailure(f"CSV line {line}: unknown primary_track")
        covered_tracks.add(row["primary_track"])

        modalities = {item.strip() for item in row["modalities"].split(";") if item.strip()}
        if not modalities or not modalities <= allowed_modalities:
            raise ValidationFailure(f"CSV line {line}: invalid modalities")
        if row["record_kind"] not in SOTA_KINDS:
            raise ValidationFailure(f"CSV line {line}: invalid record_kind")
        if row["publication_status"] not in SOTA_STATUSES:
            raise ValidationFailure(f"CSV line {line}: invalid publication_status")
        if row["metric_direction"] not in METRIC_DIRECTIONS:
            raise ValidationFailure(f"CSV line {line}: invalid metric_direction")
        if len(row["protocol"]) < 18:
            raise ValidationFailure(f"CSV line {line}: protocol is not specific enough")

        validate_url(row["paper_url"], "paper_url", line)
        validate_url(row["proceedings_url"], "proceedings_url", line, required=False)
        validate_url(row["leaderboard_url"], "leaderboard_url", line, required=False)
        validate_url(row["code_url"], "code_url", line, required=False)
        if row["publication_status"] == "Accepted" and not row["proceedings_url"]:
            raise ValidationFailure(f"CSV line {line}: Accepted requires proceedings_url")

        kind = row["record_kind"]
        if kind == "OfficialLeaderboardSnapshot":
            if not row["leaderboard_url"] or not row["value"]:
                raise ValidationFailure(
                    f"CSV line {line}: official leaderboard snapshots need a URL and value"
                )
        elif kind in {"PaperReportedFrontier", "BenchmarkAnchor"}:
            if not row["value"]:
                raise ValidationFailure(
                    f"CSV line {line}: {kind} needs an explicit reported value"
                )
        elif kind == "NoSingleLeaderboard":
            if row["value"]:
                raise ValidationFailure(
                    f"CSV line {line}: NoSingleLeaderboard cannot carry a ranking value"
                )
            if "无单一可比 SOTA" not in row["boundary"]:
                raise ValidationFailure(
                    f"CSV line {line}: no-single-leaderboard boundary must be explicit"
                )

    missing_tracks = sorted(allowed_tracks - covered_tracks)
    if missing_tracks:
        raise ValidationFailure(
            "index/sota.csv must cover every taxonomy track; missing "
            + ", ".join(missing_tracks)
        )


def validate_closest_works(value: str, line: int, *, highlighted: bool) -> None:
    works = split_list(value)
    minimum = 3 if highlighted else 1
    if not minimum <= len(works) <= 7:
        raise ValidationFailure(
            f"CSV line {line}: closest_works must contain {minimum}-7 entries"
        )
    for work in works:
        if "|" not in work:
            raise ValidationFailure(
                f"CSV line {line}: each closest work must be Name|URL"
            )
        name, url = (part.strip() for part in work.split("|", 1))
        if not name:
            raise ValidationFailure(f"CSV line {line}: closest work name is empty")
        validate_url(url, "closest_works URL", line)


def validate_transfer_rows(
    rows: list[dict[str, str]], taxonomy: dict[str, object] | None = None
) -> None:
    if not rows:
        raise ValidationFailure("index/transfer.csv must contain at least one candidate")
    taxonomy = taxonomy or load_taxonomy()
    allowed_tracks, _ = track_maps(taxonomy)
    keys: set[str] = set()
    methods: set[str] = set()
    highlighted_count = 0

    for line, row in enumerate(rows, start=2):
        for field in TRANSFER_FIELDS:
            if field not in row:
                raise ValidationFailure(f"CSV line {line}: missing field {field}")
            if not row[field]:
                raise ValidationFailure(f"CSV line {line}: {field} is required")

        snapshot = parse_date(row["snapshot_date"], "snapshot_date", line)
        refresh = parse_date(row["next_refresh"], "next_refresh", line)
        try:
            source_year = int(row["source_year"])
            score = float(row["priority_score"])
        except ValueError as exc:
            raise ValidationFailure(
                f"CSV line {line}: source_year and priority_score must be numeric"
            ) from exc
        if source_year < 2023:
            raise ValidationFailure(
                f"CSV line {line}: transfer source must be recent (2023 or later)"
            )
        if not 0 <= score <= 10:
            raise ValidationFailure(f"CSV line {line}: priority_score must be 0-10")
        if row["candidate_key"] in keys or row["method"].casefold() in methods:
            raise ValidationFailure(f"CSV line {line}: duplicate candidate or method")
        keys.add(row["candidate_key"])
        methods.add(row["method"].casefold())

        if row["source_status"] not in TRANSFER_STATUSES:
            raise ValidationFailure(f"CSV line {line}: invalid source_status")
        if row["source_status"] == "Accepted" and not row["source_proceedings_url"]:
            raise ValidationFailure(f"CSV line {line}: Accepted requires proceedings URL")
        if row["ad_target_track"] not in allowed_tracks:
            raise ValidationFailure(f"CSV line {line}: invalid ad_target_track")
        if row["coverage_verdict"] not in TRANSFER_VERDICTS:
            raise ValidationFailure(f"CSV line {line}: invalid coverage_verdict")
        if row["highlight"] not in {"yes", "no"}:
            raise ValidationFailure(f"CSV line {line}: highlight must be yes or no")
        highlighted = row["highlight"] == "yes"
        if highlighted:
            highlighted_count += 1
            if row["coverage_verdict"] != HIGHLIGHT_VERDICT:
                raise ValidationFailure(
                    f"CSV line {line}: highlighted candidates need the scoped no-direct-hit verdict"
                )
            if refresh <= snapshot or refresh > snapshot + timedelta(days=30):
                raise ValidationFailure(
                    f"CSV line {line}: highlighted candidate must be rechecked within 30 days"
                )
            if PUBLIC_BOUNDARY_PHRASE not in row["public_boundary"]:
                raise ValidationFailure(
                    f"CSV line {line}: highlighted public boundary is not scoped"
                )
        if row["coverage_verdict"] == "[检索受阻]" and highlighted:
            raise ValidationFailure(
                f"CSV line {line}: a search-blocked candidate cannot be highlighted"
            )

        for field in (
            "source_proceedings_url",
            "paper_url",
            "repo_url",
        ):
            validate_url(row[field], field, line)
        if "github.com" not in urlsplit(row["repo_url"]).netloc.casefold():
            raise ValidationFailure(f"CSV line {line}: repo_url must identify GitHub source")
        if not SHA_RE.fullmatch(row["repo_commit"]):
            raise ValidationFailure(f"CSV line {line}: repo_commit must be a full 40-char SHA")
        if len(row["license"]) < 3:
            raise ValidationFailure(f"CSV line {line}: license must be explicit")

        queries = [
            row["query_problem"].casefold(),
            row["query_mechanism"].casefold(),
            row["query_synonym"].casefold(),
        ]
        if len(set(queries)) != 3 or any(len(query) < 12 for query in queries):
            raise ValidationFailure(
                f"CSV line {line}: three distinct, substantive query families are required"
            )
        if len(split_list(row["search_sources"])) < 4:
            raise ValidationFailure(
                f"CSV line {line}: search_sources must name at least four dated sources"
            )
        validate_closest_works(row["closest_works"], line, highlighted=highlighted)

        joined = " ".join(row.values())
        if PROHIBITED_NOVELTY_RE.search(joined):
            raise ValidationFailure(
                f"CSV line {line}: prohibited absolute novelty language"
            )

    if highlighted_count == 0:
        raise ValidationFailure("the transfer radar needs at least one reviewable opportunity")


def validate_transfer_zh(
    rows: list[dict[str, str]], localization: dict[str, dict[str, str]]
) -> None:
    expected_keys = {row["candidate_key"] for row in rows}
    if set(localization) != expected_keys:
        missing = sorted(expected_keys - set(localization))
        extra = sorted(set(localization) - expected_keys)
        raise ValidationFailure(
            "index/transfer_zh.json keys must match transfer.csv; "
            f"missing={missing}, extra={extra}"
        )
    for key, card in localization.items():
        if not isinstance(card, dict) or tuple(card) != TRANSFER_ZH_FIELDS:
            raise ValidationFailure(
                f"index/transfer_zh.json {key}: fields must follow the current schema"
            )
        for field, value in card.items():
            minimum = 4 if field == "target" else 12
            if not isinstance(value, str) or len(value.strip()) < minimum:
                raise ValidationFailure(
                    f"index/transfer_zh.json {key}: {field} is not substantive"
                )
        joined = " ".join(card.values())
        if PROHIBITED_NOVELTY_RE.search(joined):
            raise ValidationFailure(
                f"index/transfer_zh.json {key}: prohibited absolute novelty language"
            )


def md_escape(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]")


def link(label: str, url: str) -> str:
    return f"[{label}]({url})" if url else label


def record_label(kind: str) -> str:
    return {
        "OfficialLeaderboardSnapshot": "官方榜单快照",
        "PaperReportedFrontier": "论文自报前沿",
        "BenchmarkAnchor": "协议锚点",
        "NoSingleLeaderboard": "无单一总榜",
    }[kind]


def direction_label(direction: str) -> str:
    return {
        "higher": "越高越好",
        "lower": "越低越好",
        "mixed": "需分项判断",
        "not-applicable": "不适用单一方向",
    }[direction]


def metric_explanation(metric: str, kind: str) -> str:
    if kind == "NoSingleLeaderboard":
        return "这里比较的是一组评价轴，不存在一个能代表整个方向的冠军数字。"
    normalized = metric.casefold()
    if normalized == "nds":
        return "NDS 把检测 mAP 与位置、尺度、方向、速度和属性误差合成一分；总分上涨不等于每个类别和误差项都改善。"
    if normalized == "amota":
        return "AMOTA 汇总多个召回水平下的跟踪表现；它不单独说明身份切换、每类稳定性或安全后果。"
    if "miou" in normalized:
        return "mIoU 先算每一类预测区域与真值区域的交并比再做类别平均，不等于所有点或体素的总体正确率。"
    if normalized == "pq":
        return "PQ 同时受实例识别与分割质量影响；一个总分不能告诉你错误主要来自漏检还是轮廓不准。"
    if normalized == "pat":
        return "PAT 同时看全景分割与跨帧关联；它的总分不能替代逐类 PQ、跟踪质量或错误传播分析。"
    if "minade" in normalized:
        return "MinADE 从多条候选轨迹中取最接近真值的一条；它不保证概率校准，也不保证与其他交通参与者交互合理。"
    if "latency" in normalized:
        return "时延只在指定硬件、软件、精度和输入规模下成立；它不是跨设备不变的模型属性。"
    if "gain" in normalized:
        return "这是相对指定对照的点数增益，不是该数据集所有公开配置中的绝对最高值。"
    return "该数字只回答列明协议中的一个问题，不能脱离数据、输入和评测设置外推为闭环安全。"


def render_sota(rows: list[dict[str, str]], taxonomy: dict[str, object]) -> str:
    snapshots = sorted({row["snapshot_date"] for row in rows}, reverse=True)
    latest = snapshots[0]
    official_count = sum(
        row["record_kind"] == "OfficialLeaderboardSnapshot" for row in rows
    )
    by_track: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_track[row["primary_track"]].append(row)

    lines = [
        "# 自动驾驶感知 SOTA 与指标雷达",
        "",
        f"> **快照日期：{latest}。** 当前收录 {len(rows)} 个协议卡，其中 "
        f"{official_count} 个来自官方动态榜单。这里的 SOTA 只表示列明协议内的"
        "可比较前沿，不是把不同传感器、数据划分、外部数据或指标混成总排名。",
        "",
        "[返回首页](../README.md) · [查看机器索引](../index/sota.csv) · "
        "[查看方法与日更规则](../docs/research-radar-methodology.md)",
        "",
        "## 先学会读这张雷达",
        "",
        "- **官方榜单快照：** 榜单在快照日公开的提交结果；它不自动证明论文已正式录用，也不表示本仓库独立复现。",
        "- **论文自报前沿：** 数字来自正式论文中的指定对照；跨论文配置不同，不能直接接在官方榜单后声称更强。",
        "- **协议锚点：** 用来理解当前常用数据集与指标，不冒充全任务第一。",
        "- **无单一总榜：** 该方向同时含多种任务或评测轴；强行给一个冠军会误导，因此保留评价菜单和代表性入口。",
        "- **指标不是什么：** NDS、mAP、mIoU、PQ、AMOTA 或时延各自只回答一部分问题；离线分数更高不等于每类都改善，更不等于闭环安全。",
        "",
        "## 13 个主方向",
        "",
    ]

    tracks = taxonomy["tracks"]
    assert isinstance(tracks, list)
    for number, track in enumerate(tracks, start=1):
        track_id = str(track["id"])
        track_name = str(track["name"])
        lines.extend((f"### P{number:02d} · {track_name}", ""))
        for row in sorted(
            by_track[track_id],
            key=lambda item: (item["record_kind"] == "NoSingleLeaderboard", item["task"]),
        ):
            value = (
                f"{row['value']} {row['unit']}".strip()
                if row["value"]
                else "不设单一排名值"
            )
            sources = [link("论文", row["paper_url"])]
            if row["proceedings_url"]:
                sources.append(link("正式录用", row["proceedings_url"]))
            if row["leaderboard_url"]:
                sources.append(link("官方榜单", row["leaderboard_url"]))
            if row["code_url"]:
                sources.append(link("代码", row["code_url"]))
            lines.extend(
                (
                    f"#### {md_escape(row['method'])} · {md_escape(row['task'])}",
                    "",
                    f"**证据身份：** {record_label(row['record_kind'])} · "
                    f"{row['publication_status']} · {row['venue']} · {row['year']}",
                    "",
                    f"**严格协议：** {row['benchmark']} · {row['dataset_version']} · "
                    f"{row['split']} · {row['modalities'].replace(';', ' + ')} · "
                    f"{row['protocol']}",
                    "",
                    f"**主指标：** {row['metric']}（{direction_label(row['metric_direction'])}）"
                    f"= **{value}**",
                    "",
                )
            )
            if row["secondary_metrics"]:
                lines.extend((f"**同时报告：** {row['secondary_metrics']}", ""))
            lines.extend(
                (
                    f"**第一次看这个指标：** {metric_explanation(row['metric'], row['record_kind'])}",
                    "",
                    f"**核验：** {row['verification_note']}",
                    "",
                    f"**边界：** {row['boundary']}",
                    "",
                    "**入口：** " + " · ".join(sources),
                    "",
                )
            )

    lines.extend(
        (
            "## 日更原则",
            "",
            "每天先刷新可机器读取的官方榜单，再核对近期正式论文。若协议、榜单或"
            "论文身份无法从官方入口确认，只保留旧快照并标注受阻，不用聚合站数字"
            "覆盖官方证据。每次更新与当日精读、Taste 共用分支、PR 和公开验收。",
            "",
        )
    )
    return "\n".join(lines)


def render_closest_works(value: str) -> list[str]:
    rendered = []
    for work in split_list(value):
        name, url = (part.strip() for part in work.split("|", 1))
        rendered.append(f"- [{name}]({url})")
    return rendered


def transfer_card(row: dict[str, str], zh: dict[str, str]) -> list[str]:
    commit_link = f"{row['repo_url']}/tree/{row['repo_commit']}"
    verdict = row["coverage_verdict"]
    lines = [
        f"### {md_escape(row['method'])} → {md_escape(zh['target'])}",
        "",
        f"**检索结论：** {verdict} · {row['collision_level']} · "
        f"优先级 {row['priority_score']}/10 · 下次复核 {row['next_refresh']}",
        "",
        f"**30 秒画面：** {zh['summary']}",
        "",
        f"**源领域与证据：** {row['source_domain']}；{zh['source_evidence']}",
        "",
        f"**迁移接口：** {zh['transfer_interface']}",
        "",
        f"**适配假设：** [判断] {zh['adaptation_hypothesis']}",
        "",
        "**三路检索式：**",
        "",
        f"- 问题词：{row['query_problem']}",
        f"- 机制词：{row['query_mechanism']}",
        f"- 同义/邻域词：{row['query_synonym']}",
        "",
        f"**检索来源：** {row['search_sources'].replace(LIST_SEPARATOR, ' · ')}",
        "",
        "**最接近工作：**",
        "",
        *render_closest_works(row["closest_works"]),
        "",
        f"**最小接入实验：** {zh['minimum_test']}",
        "",
        f"**回滚基线：** {zh['rollback_baseline']}",
        "",
        f"**什么会推翻它：** {zh['falsifier']}",
        "",
        f"**最大失效条件：** {zh['main_failure']}",
        "",
        f"**公开边界：** {row['public_boundary']}",
        "",
        f"**源论文与代码：** [论文]({row['paper_url']}) · "
        f"[正式入口]({row['source_proceedings_url']}) · "
        f"[官方代码 @ {row['repo_commit'][:8]}]({commit_link}) · "
        f"许可证 {row['license']}。这里只核验仓库身份、固定 SHA 与许可证，"
        "没有运行源码或证明迁移收益。",
        "",
    ]
    return lines


def render_transfer(
    rows: list[dict[str, str]],
    taxonomy: dict[str, object],
    localization: dict[str, dict[str, str]],
) -> str:
    del taxonomy
    latest = max(row["snapshot_date"] for row in rows)
    highlighted = sorted(
        (row for row in rows if row["highlight"] == "yes"),
        key=lambda row: float(row["priority_score"]),
        reverse=True,
    )
    collisions = sorted(
        (row for row in rows if row["highlight"] == "no"),
        key=lambda row: row["method"].casefold(),
    )
    lines = [
        "# 跨领域强算法迁移雷达",
        "",
        f"> **检索快照：{latest}。** 当前重点保留 {len(highlighted)} 个可做受控"
        f"验证的窄迁移假设，并公开 {len(collisions)} 个已覆盖或部分覆盖的碰撞项。"
        "“可迁移”只表示瓶颈和接口值得测试，不表示零改动必然提升，更不表示已达到自动驾驶 SOTA。",
        "",
        "[返回首页](../README.md) · [查看机器索引](../index/transfer.csv) · "
        "[查看检索与评分方法](../docs/research-radar-methodology.md)",
        "",
        "## 怎么读",
        "",
        "每个候选先把主张拆成问题、机制、洞见与场景，再用问题词、机制词、"
        "同义/邻域词检索。最接近论文必须回到官方 proceedings、作者项目或 arXiv "
        "原文；帖子、Awesome List 和榜单聚合页只用于召回。只有结论为"
        "“本次检索未找到直接覆盖”的候选可以高亮，而且 30 天内必须重查。",
        "",
        "## 值得做受控验证",
        "",
    ]
    for row in highlighted:
        lines.extend(transfer_card(row, localization[row["candidate_key"]]))
    lines.extend(("## 碰撞与已覆盖：为什么没有把它包装成机会", ""))
    for row in collisions:
        lines.extend(transfer_card(row, localization[row["candidate_key"]]))
    lines.extend(
        (
            "## 当前检索边界",
            "",
            "本轮自动多源检索中，OpenReview Python 客户端不可用，OpenAlex、DBLP "
            "部分请求出现 5xx；已用官方 CVF、ICLR/NeurIPS proceedings、OpenReview "
            "网页、arXiv、作者项目页、Semantic Scholar 与 Crossref 交叉补查。这个"
            "雷达因此给出的是可复查的有限范围结论，不是对整个学术史的绝对否定。"
            "新会议批次、预印本或仓库出现时，自动化必须重新跑碰撞检索；找到直接"
            "覆盖就降级或撤下候选。",
            "",
        )
    )
    return "\n".join(lines)


def expected_files() -> tuple[dict[Path, str], dict[str, int]]:
    taxonomy = load_taxonomy()
    sota_rows = load_sota_rows()
    transfer_rows = load_transfer_rows()
    transfer_zh = load_transfer_zh()
    validate_sota_rows(sota_rows, taxonomy)
    validate_transfer_rows(transfer_rows, taxonomy)
    validate_transfer_zh(transfer_rows, transfer_zh)
    targets = {
        SOTA_MD_PATH: render_sota(sota_rows, taxonomy).rstrip() + "\n",
        TRANSFER_MD_PATH: render_transfer(
            transfer_rows,
            taxonomy,
            transfer_zh,
        ).rstrip()
        + "\n",
    }
    counts = {
        "sota": len(sota_rows),
        "transfer": len(transfer_rows),
        "highlighted": sum(row["highlight"] == "yes" for row in transfer_rows),
    }
    return targets, counts


def sync(*, check: bool) -> tuple[list[Path], dict[str, int]]:
    targets, counts = expected_files()
    stale: list[Path] = []
    for path, expected in targets.items():
        current = read_text(path) if path.exists() else ""
        if current != expected:
            stale.append(path)
            if not check:
                write_text(path, expected)
    return stale, counts


def main() -> int:
    args = parse_args()
    try:
        stale, counts = sync(check=args.check)
        if args.check and stale:
            for path in stale:
                print(f"STALE: {path.relative_to(ROOT).as_posix()}", file=sys.stderr)
            print(
                "Run `python scripts/rebuild_research_radar.py` and commit the results.",
                file=sys.stderr,
            )
            return 1
        for path in stale:
            print(f"UPDATED: {path.relative_to(ROOT).as_posix()}")
        if not stale:
            print("OK: research-radar pages are current")
        print(f"OK: validated {counts['sota']} SOTA protocol record(s)")
        print(
            f"OK: validated {counts['transfer']} transfer record(s), "
            f"including {counts['highlighted']} highlighted candidate(s)"
        )
        return 0
    except ValidationFailure as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
