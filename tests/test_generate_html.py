import contextlib
from datetime import datetime, timedelta
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlparse

import requests


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class FailedResponse:
    def raise_for_status(self):
        raise requests.HTTPError("temporary failure")


class SuccessfulResponse:
    def __init__(self, records):
        self.records = records

    def raise_for_status(self):
        return None

    def json(self):
        return {"earningsCalendar": self.records}


class GenerateHtmlIntegrationTests(unittest.TestCase):
    def test_successful_response_reconciles_and_writes_atomically(self):
        now = datetime.now()
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        first_monday = next_month
        while first_monday.weekday() != 0:
            first_monday += timedelta(days=1)

        old_date = (first_monday + timedelta(days=2)).date().isoformat()
        new_date = (first_monday + timedelta(days=3)).date().isoformat()
        historical_date = (
            now.replace(day=1) - timedelta(days=10)
        ).date().isoformat()
        historical = {
            "symbol": "AAPL",
            "date": historical_date,
            "status": "confirmed",
        }
        previous = [historical, {"symbol": "TGT", "date": old_date}]

        def fake_get(url, timeout):
            self.assertEqual(timeout, 30)
            query = parse_qs(urlparse(url).query)
            from_date = query["from"][0]
            to_date = query["to"][0]
            records = (
                [{"symbol": "TGT", "date": new_date}]
                if from_date <= new_date <= to_date
                else []
            )
            return SuccessfulResponse(records)

        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="earnings-success-") as temp_dir:
            data_path = Path(temp_dir) / "earnings_data.json"
            data_path.write_text(json.dumps(previous), encoding="utf-8")

            try:
                os.chdir(temp_dir)
                sys.path.insert(0, str(REPOSITORY_ROOT))
                with patch("requests.get", side_effect=fake_get):
                    with contextlib.redirect_stdout(io.StringIO()):
                        runpy.run_path(
                            str(REPOSITORY_ROOT / "generate_html.py"),
                            run_name="__main__",
                        )
            finally:
                os.chdir(original_directory)
                if sys.path[0] == str(REPOSITORY_ROOT):
                    sys.path.pop(0)

            generated = json.loads(data_path.read_text(encoding="utf-8"))
            by_date = {record["date"]: record for record in generated}
            self.assertEqual(by_date[historical_date], historical)
            self.assertEqual(by_date[new_date]["status"], "confirmed")
            self.assertEqual(by_date[old_date]["status"], "changed")
            self.assertTrue(data_path.read_text(encoding="utf-8").endswith("\n"))
            self.assertEqual(list(Path(temp_dir).glob(".earnings_data.*.tmp")), [])
            generated_html = (Path(temp_dir) / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('id="monthSelect"', generated_html)
            self.assertIn("initializeCalendarNavigation();", generated_html)
            self.assertIn("function buildWeeksForMonth(monthKey)", generated_html)

    def test_total_api_failure_does_not_rewrite_existing_data(self):
        original = '[{"symbol":"TGT","date":"2026-08-19"}]\n'
        original_directory = Path.cwd()

        with tempfile.TemporaryDirectory(prefix="earnings-failure-") as temp_dir:
            data_path = Path(temp_dir) / "earnings_data.json"
            data_path.write_text(original, encoding="utf-8")

            try:
                os.chdir(temp_dir)
                sys.path.insert(0, str(REPOSITORY_ROOT))
                with patch("requests.get", return_value=FailedResponse()):
                    with contextlib.redirect_stdout(io.StringIO()):
                        runpy.run_path(
                            str(REPOSITORY_ROOT / "generate_html.py"),
                            run_name="__main__",
                        )
            finally:
                os.chdir(original_directory)
                if sys.path[0] == str(REPOSITORY_ROOT):
                    sys.path.pop(0)

            self.assertEqual(data_path.read_text(encoding="utf-8"), original)
            self.assertEqual(list(Path(temp_dir).glob(".earnings_data.*.tmp")), [])
            generated_html = (Path(temp_dir) / "index.html").read_text(
                encoding="utf-8"
            )
            self.assertIn(
                "data.filter(e => e.status !== 'changed')", generated_html
            )
            self.assertIn("card.classList.add('unconfirmed')", generated_html)


if __name__ == "__main__":
    unittest.main()
