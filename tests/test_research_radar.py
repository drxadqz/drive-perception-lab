from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import rebuild_research_radar as radar  # noqa: E402


class SotaRadarValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = radar.load_taxonomy()
        cls.rows = radar.load_sota_rows()

    def test_current_sota_index_covers_all_thirteen_tracks(self) -> None:
        radar.validate_sota_rows(self.rows, self.taxonomy)
        expected, _ = radar.track_maps(self.taxonomy)
        self.assertEqual({row["primary_track"] for row in self.rows}, expected)

    def test_official_leaderboard_snapshot_requires_value_and_url(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(
            row
            for row in rows
            if row["record_kind"] == "OfficialLeaderboardSnapshot"
        )
        target["value"] = ""
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_sota_rows(rows, self.taxonomy)

    def test_no_single_leaderboard_cannot_smuggle_in_rank_value(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(
            row for row in rows if row["record_kind"] == "NoSingleLeaderboard"
        )
        target["value"] = "99.9"
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_sota_rows(rows, self.taxonomy)

    def test_missing_taxonomy_track_is_rejected(self) -> None:
        rows = [
            row
            for row in copy.deepcopy(self.rows)
            if row["primary_track"] != "p13-data-generation-evaluation-deployment"
        ]
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_sota_rows(rows, self.taxonomy)

    def test_generated_sota_page_uses_protocol_cards_not_wide_tables(self) -> None:
        rendered = radar.render_sota(self.rows, self.taxonomy)
        for number in range(1, 14):
            self.assertIn(f"### P{number:02d}", rendered)
        self.assertNotRegex(rendered, r"(?m)^\|[^\n]+\|$")
        self.assertIn("无单一可比 SOTA", rendered)


class TransferRadarValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.taxonomy = radar.load_taxonomy()
        cls.rows = radar.load_transfer_rows()
        cls.localization = radar.load_transfer_zh()

    def test_current_transfer_index_passes(self) -> None:
        radar.validate_transfer_rows(self.rows, self.taxonomy)
        radar.validate_transfer_zh(self.rows, self.localization)
        self.assertGreaterEqual(
            sum(row["highlight"] == "yes" for row in self.rows),
            1,
        )

    def test_every_transfer_card_requires_beginner_chinese_copy(self) -> None:
        localization = copy.deepcopy(self.localization)
        localization.pop(next(iter(localization)))
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_zh(self.rows, localization)

    def test_localized_card_fields_must_be_substantive(self) -> None:
        localization = copy.deepcopy(self.localization)
        localization[next(iter(localization))]["minimum_test"] = "太短"
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_zh(self.rows, localization)

    def test_highlight_needs_scoped_no_direct_hit_verdict(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(row for row in rows if row["highlight"] == "yes")
        target["coverage_verdict"] = "[部分覆盖]"
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_rows(rows, self.taxonomy)

    def test_search_blocked_candidate_cannot_be_highlighted(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(row for row in rows if row["highlight"] == "yes")
        target["coverage_verdict"] = "[检索受阻]"
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_rows(rows, self.taxonomy)

    def test_full_source_commit_is_required(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["repo_commit"] = rows[0]["repo_commit"][:8]
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_rows(rows, self.taxonomy)

    def test_three_distinct_query_families_are_required(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(row for row in rows if row["highlight"] == "yes")
        target["query_mechanism"] = target["query_problem"]
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_rows(rows, self.taxonomy)

    def test_highlight_requires_three_to_seven_closest_works(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(row for row in rows if row["highlight"] == "yes")
        target["closest_works"] = target["closest_works"].split(
            radar.LIST_SEPARATOR
        )[0]
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_rows(rows, self.taxonomy)

    def test_absolute_novelty_language_is_rejected(self) -> None:
        rows = copy.deepcopy(self.rows)
        rows[0]["public_boundary"] = "学界无人做过这个方向。"
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_rows(rows, self.taxonomy)

    def test_highlight_recheck_cannot_exceed_thirty_days(self) -> None:
        rows = copy.deepcopy(self.rows)
        target = next(row for row in rows if row["highlight"] == "yes")
        target["next_refresh"] = "2026-09-05"
        with self.assertRaises(radar.ValidationFailure):
            radar.validate_transfer_rows(rows, self.taxonomy)

    def test_generated_pages_are_current(self) -> None:
        stale, counts = radar.sync(check=True)
        self.assertEqual(stale, [])
        self.assertEqual(counts["sota"], len(radar.load_sota_rows()))
        self.assertEqual(counts["transfer"], len(self.rows))


if __name__ == "__main__":
    unittest.main()
