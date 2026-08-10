import unittest

from earnings_utils import deduplicate_earnings


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


if __name__ == "__main__":
    unittest.main()
