import unittest
from datetime import date

from earnings_utils import deduplicate_earnings, reconcile_earnings


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
                {"symbol": "TGT", "date": "2026-08-20", "status": "confirmed"},
                {"symbol": "TGT", "date": "2026-08-19", "status": "changed"},
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
                {"symbol": "TGT", "date": "2026-08-12", "status": "confirmed"},
                {"symbol": "TGT", "date": "2026-08-10", "status": "changed"},
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
                {"symbol": "TGT", "date": "2026-08-19", "status": "confirmed"},
                {"symbol": "TGT", "date": "2026-08-10", "status": "unconfirmed"},
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
                {"symbol": "AAPL", "date": "2026-09-01", "status": "confirmed"},
                {"symbol": "AAPL", "date": "2026-07-30", "status": "confirmed"},
            ],
        )

    def test_discards_records_outside_the_current_generation_window(self):
        previous = [{"symbol": "AAPL", "date": "2026-07-24"}]
        fetched = [{"symbol": "MSFT", "date": "2026-10-01"}]

        result = self.reconcile(previous, fetched)

        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
