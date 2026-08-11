import unittest
from datetime import date

from earnings_utils import (
    deduplicate_earnings,
    merge_earnings_history,
    reconcile_earnings,
    sort_earnings,
)


class DeduplicateEarningsTests(unittest.TestCase):
    def test_keeps_only_the_first_record_for_each_symbol_and_date(self):
        first_aapl = {
            "symbol": "AAPL",
            "date": "2026-07-30",
            "quarter": 2,
        }
        duplicate_aapl = {
            "symbol": "AAPL",
            "date": "2026-07-30",
            "quarter": 3,
        }
        msft = {
            "symbol": "MSFT",
            "date": "2026-07-30",
            "quarter": 2,
        }

        result = deduplicate_earnings([first_aapl, duplicate_aapl, msft])

        self.assertEqual(result, [first_aapl, msft])

    def test_keeps_the_same_symbol_on_different_dates(self):
        first_date = {"symbol": "AAPL", "date": "2026-07-30"}
        second_date = {"symbol": "AAPL", "date": "2026-10-29"}

        result = deduplicate_earnings([first_date, second_date])

        self.assertEqual(result, [first_date, second_date])

    def test_sorts_records_deterministically_after_deduplication(self):
        records = [
            {"symbol": "MSFT", "date": "2026-08-20"},
            {"symbol": "TGT", "date": "2026-08-19"},
            {"symbol": "AAPL", "date": "2026-08-20"},
            {"symbol": "MSFT", "date": "2026-08-20", "quarter": 3},
        ]

        result = sort_earnings(records)

        self.assertEqual(
            result,
            [
                {"symbol": "TGT", "date": "2026-08-19"},
                {"symbol": "AAPL", "date": "2026-08-20"},
                {"symbol": "MSFT", "date": "2026-08-20"},
            ],
        )


class MergeEarningsHistoryTests(unittest.TestCase):
    WINDOW_START = date(2026, 8, 1)
    WINDOW_END = date(2026, 9, 30)

    def merge(self, previous, snapshot, preserve_through=None):
        return merge_earnings_history(
            previous,
            snapshot,
            window_start=self.WINDOW_START,
            window_end=self.WINDOW_END,
            preserve_through=preserve_through,
        )

    def test_replaces_the_current_window_and_preserves_history(self):
        historical = {
            "symbol": "7203.T",
            "date": "2026-07-31",
            "name_ja": "トヨタ自動車",
        }
        stale_current = {"symbol": "8306.T", "date": "2026-08-04"}
        latest_current = {
            "symbol": "8306.T",
            "date": "2026-08-05",
            "name_ja": "三菱UFJ",
        }

        result = self.merge(
            [historical, stale_current],
            [latest_current],
        )

        self.assertEqual(result, [historical, latest_current])

    def test_ignores_snapshot_records_outside_the_authoritative_window(self):
        historical = {"symbol": "7203.T", "date": "2026-07-31"}
        unexpected = {"symbol": "9984.T", "date": "2026-10-01"}

        result = self.merge([historical], [unexpected])

        self.assertEqual(result, [historical])

    def test_is_idempotent_across_repeated_monthly_merges(self):
        july = {"symbol": "7203.T", "date": "2026-07-31"}
        august = {"symbol": "8306.T", "date": "2026-08-05"}
        first = self.merge([july], [august])

        second = self.merge(first, [august, august])

        self.assertEqual(second, [july, august])

    def test_preserves_completed_dates_inside_the_current_window(self):
        completed = {
            "symbol": "7203.T",
            "date": "2026-08-05",
            "name_ja": "トヨタ自動車",
        }
        stale_future = {"symbol": "8306.T", "date": "2026-08-20"}
        latest_future = {"symbol": "9984.T", "date": "2026-08-25"}

        result = self.merge(
            [completed, stale_future],
            [latest_future],
            preserve_through=date(2026, 8, 10),
        )

        self.assertEqual(result, [completed, latest_future])

    def test_snapshot_refreshes_metadata_for_a_preserved_date(self):
        previous = {
            "symbol": "7203.T",
            "date": "2026-08-05",
            "name_ja": "old",
        }
        refreshed = {
            "symbol": "7203.T",
            "date": "2026-08-05",
            "name_ja": "トヨタ自動車",
        }

        result = self.merge(
            [previous],
            [refreshed],
            preserve_through=date(2026, 8, 10),
        )

        self.assertEqual(result, [refreshed])


class ReconcileEarningsTests(unittest.TestCase):
    TODAY = date(2026, 8, 10)
    WINDOW_START = date(2026, 7, 27)
    WINDOW_END = date(2026, 9, 30)
    AUGUST_17_WEEK = [(date(2026, 8, 17), date(2026, 8, 21))]

    def reconcile(self, previous, fetched, successful_ranges=None, today=None):
        return reconcile_earnings(
            previous,
            fetched,
            today=self.TODAY if today is None else today,
            window_start=self.WINDOW_START,
            window_end=self.WINDOW_END,
            successful_ranges=(
                self.AUGUST_17_WEEK
                if successful_ranges is None
                else successful_ranges
            ),
        )

    def test_marks_a_missing_future_earning_as_unconfirmed(self):
        previous = [{"symbol": "TGT", "date": "2026-08-19"}]

        result = self.reconcile(previous, [])

        self.assertEqual(
            result,
            [{"symbol": "TGT", "date": "2026-08-19", "status": "unconfirmed"}],
        )

    def test_treats_an_earning_on_today_as_future(self):
        previous = [{"symbol": "AAPL", "date": "2026-08-10"}]
        successful_ranges = [(date(2026, 8, 10), date(2026, 8, 14))]

        result = self.reconcile(previous, [], successful_ranges=successful_ranges)

        self.assertEqual(
            result,
            [{"symbol": "AAPL", "date": "2026-08-10", "status": "unconfirmed"}],
        )

    def test_marks_the_old_date_changed_when_a_new_date_is_found(self):
        previous = [{"symbol": "TGT", "date": "2026-08-19"}]
        fetched = [{"symbol": "TGT", "date": "2026-08-20"}]

        result = self.reconcile(previous, fetched)

        self.assertEqual(
            result,
            [
                {"symbol": "TGT", "date": "2026-08-19", "status": "changed"},
                {"symbol": "TGT", "date": "2026-08-20", "status": "confirmed"},
            ],
        )

    def test_restores_an_unconfirmed_date_when_it_reappears(self):
        previous = [
            {"symbol": "TGT", "date": "2026-08-19", "status": "unconfirmed"}
        ]
        fetched = [{"symbol": "TGT", "date": "2026-08-19", "hour": "bmo"}]

        result = self.reconcile(previous, fetched)

        self.assertEqual(
            result,
            [
                {
                    "symbol": "TGT",
                    "date": "2026-08-19",
                    "hour": "bmo",
                    "status": "confirmed",
                }
            ],
        )

    def test_restores_a_changed_date_when_the_original_date_reappears(self):
        previous = [
            {"symbol": "TGT", "date": "2026-08-19", "status": "changed"},
            {"symbol": "TGT", "date": "2026-08-20", "status": "confirmed"},
        ]
        fetched = [{"symbol": "TGT", "date": "2026-08-19"}]

        result = self.reconcile(previous, fetched)

        self.assertEqual(
            result,
            [
                {"symbol": "TGT", "date": "2026-08-19", "status": "confirmed"},
                {"symbol": "TGT", "date": "2026-08-20", "status": "changed"},
            ],
        )

    def test_keeps_a_changed_status_when_the_replacement_disappears(self):
        previous = [
            {"symbol": "TGT", "date": "2026-08-19", "status": "changed"},
            {"symbol": "TGT", "date": "2026-08-20", "status": "confirmed"},
        ]

        result = self.reconcile(previous, [])

        self.assertEqual(
            result,
            [
                {"symbol": "TGT", "date": "2026-08-19", "status": "changed"},
                {"symbol": "TGT", "date": "2026-08-20", "status": "unconfirmed"},
            ],
        )

    def test_preserves_status_when_the_api_range_failed(self):
        previous = [{"symbol": "TGT", "date": "2026-08-19"}]

        result = self.reconcile(previous, [], successful_ranges=[])

        self.assertEqual(
            result,
            [{"symbol": "TGT", "date": "2026-08-19", "status": "confirmed"}],
        )

    def test_only_updates_records_in_successfully_fetched_ranges(self):
        previous = [
            {"symbol": "AAPL", "date": "2026-08-12"},
            {"symbol": "TGT", "date": "2026-08-19"},
        ]
        successful_ranges = [(date(2026, 8, 17), date(2026, 8, 21))]

        result = self.reconcile(previous, [], successful_ranges=successful_ranges)

        self.assertEqual(
            result,
            [
                {"symbol": "AAPL", "date": "2026-08-12", "status": "confirmed"},
                {"symbol": "TGT", "date": "2026-08-19", "status": "unconfirmed"},
            ],
        )

    def test_does_not_change_an_old_date_when_its_range_failed(self):
        previous = [{"symbol": "TGT", "date": "2026-08-19"}]
        fetched = [{"symbol": "TGT", "date": "2026-08-12"}]
        successful_ranges = [(date(2026, 8, 10), date(2026, 8, 14))]

        result = self.reconcile(
            previous, fetched, successful_ranges=successful_ranges
        )

        self.assertEqual(
            result,
            [
                {"symbol": "TGT", "date": "2026-08-12", "status": "confirmed"},
                {"symbol": "TGT", "date": "2026-08-19", "status": "confirmed"},
            ],
        )

    def test_known_past_date_is_not_mistaken_for_a_new_date(self):
        previous = [
            {"symbol": "W", "date": "2026-08-04"},
            {"symbol": "W", "date": "2026-09-23"},
        ]
        fetched = [{"symbol": "W", "date": "2026-08-04"}]
        successful_ranges = [
            (date(2026, 8, 3), date(2026, 8, 7)),
            (date(2026, 9, 21), date(2026, 9, 25)),
        ]

        result = self.reconcile(
            previous, fetched, successful_ranges=successful_ranges
        )

        self.assertEqual(
            result,
            [
                {"symbol": "W", "date": "2026-08-04", "status": "confirmed"},
                {"symbol": "W", "date": "2026-09-23", "status": "unconfirmed"},
            ],
        )

    def test_marks_a_past_unconfirmed_date_changed_when_a_new_date_appears(self):
        previous = [
            {"symbol": "TGT", "date": "2026-08-10", "status": "unconfirmed"}
        ]
        fetched = [{"symbol": "TGT", "date": "2026-08-12"}]
        successful_ranges = [(date(2026, 8, 10), date(2026, 8, 14))]

        result = self.reconcile(
            previous,
            fetched,
            successful_ranges=successful_ranges,
            today=date(2026, 8, 11),
        )

        self.assertEqual(
            result,
            [
                {"symbol": "TGT", "date": "2026-08-10", "status": "changed"},
                {"symbol": "TGT", "date": "2026-08-12", "status": "confirmed"},
            ],
        )

    def test_preserves_a_past_unconfirmed_date_when_its_range_failed(self):
        previous = [
            {"symbol": "TGT", "date": "2026-08-10", "status": "unconfirmed"}
        ]
        fetched = [{"symbol": "TGT", "date": "2026-08-19"}]
        successful_ranges = [(date(2026, 8, 17), date(2026, 8, 21))]

        result = self.reconcile(
            previous,
            fetched,
            successful_ranges=successful_ranges,
            today=date(2026, 8, 11),
        )

        self.assertEqual(
            result,
            [
                {"symbol": "TGT", "date": "2026-08-10", "status": "unconfirmed"},
                {"symbol": "TGT", "date": "2026-08-19", "status": "confirmed"},
            ],
        )

    def test_does_not_treat_a_past_earning_as_a_changed_future_date(self):
        previous = [{"symbol": "AAPL", "date": "2026-07-30"}]
        fetched = [{"symbol": "AAPL", "date": "2026-09-01"}]
        successful_ranges = [(date(2026, 7, 27), date(2026, 7, 31))]

        result = self.reconcile(
            previous, fetched, successful_ranges=successful_ranges
        )

        self.assertEqual(
            result,
            [
                {"symbol": "AAPL", "date": "2026-07-30", "status": "confirmed"},
                {"symbol": "AAPL", "date": "2026-09-01", "status": "confirmed"},
            ],
        )

    def test_preserves_records_outside_the_current_generation_window(self):
        previous = [
            {"symbol": "AAPL", "date": "2026-07-24"},
            {
                "symbol": "TGT",
                "date": "2026-10-01",
                "status": "unconfirmed",
            },
        ]
        fetched = [{"symbol": "MSFT", "date": "2026-10-01"}]

        result = self.reconcile(previous, fetched)

        self.assertEqual(result, previous)

    def test_keeps_history_across_multiple_generation_windows(self):
        july = {"symbol": "AAPL", "date": "2026-07-30"}
        august = {"symbol": "MSFT", "date": "2026-08-20"}
        first = self.reconcile([july], [august])

        second = reconcile_earnings(
            first,
            [{"symbol": "NVDA", "date": "2026-10-15"}],
            today=date(2026, 9, 10),
            window_start=date(2026, 9, 1),
            window_end=date(2026, 10, 31),
            successful_ranges=[(date(2026, 10, 12), date(2026, 10, 16))],
        )

        self.assertEqual(
            second,
            [
                {"symbol": "AAPL", "date": "2026-07-30", "status": "confirmed"},
                {"symbol": "MSFT", "date": "2026-08-20", "status": "confirmed"},
                {"symbol": "NVDA", "date": "2026-10-15", "status": "confirmed"},
            ],
        )


if __name__ == "__main__":
    unittest.main()
