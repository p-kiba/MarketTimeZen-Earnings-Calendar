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

import pandas as pd


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class JpxPageResponse:
    text = (
        '<a href="/listing/event-schedules/financial-announcement/'
        'tvdivq0000001ofb-att/kessan_test.xlsx">test</a>'
    )
    apparent_encoding = "utf-8"
    encoding = "utf-8"


class PartialJpxPageResponse:
    text = (
        '<a href="/listing/event-schedules/financial-announcement/'
        'tvdivq0000001ofb-att/kessan_first.xlsx">first</a>'
        '<a href="/listing/event-schedules/financial-announcement/'
        'tvdivq0000001ofb-att/kessan_second.xlsx">second</a>'
    )
    apparent_encoding = "utf-8"
    encoding = "utf-8"


class GenerateJapanHtmlIntegrationTests(unittest.TestCase):
    def test_current_snapshot_is_merged_with_historical_records(self):
        now = datetime.now()
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        current_date = next_month
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)

        historical_date = (
            now.replace(day=1) - timedelta(days=10)
        ).date().isoformat()
        historical = {
            "date": historical_date,
            "symbol": "7203.T",
            "name_ja": "トヨタ自動車",
            "name_en": "Toyota Motor",
        }
        spreadsheet = pd.DataFrame(
            [
                [
                    current_date.date().isoformat(),
                    "7203",
                    "トヨタ自動車",
                    "Toyota Motor",
                    "2027-03-31",
                    "輸送用機器",
                    "Transportation Equipment",
                    "第1四半期",
                    "1Q",
                    "プライム",
                    "Prime",
                ]
            ]
        )

        original_directory = Path.cwd()
        with tempfile.TemporaryDirectory(prefix="earnings-jp-") as temp_dir:
            data_path = Path(temp_dir) / "earnings_data_jp.json"
            history_path = Path(temp_dir) / "earnings_history_jp.json"
            data_path.write_text(json.dumps([historical]), encoding="utf-8")

            try:
                os.chdir(temp_dir)
                sys.path.insert(0, str(REPOSITORY_ROOT))
                with patch("requests.get", return_value=JpxPageResponse()), patch(
                    "pandas.read_excel", return_value=spreadsheet
                ):
                    with contextlib.redirect_stdout(io.StringIO()):
                        runpy.run_path(
                            str(REPOSITORY_ROOT / "generate_html_jp.py"),
                            run_name="__main__",
                        )
            finally:
                os.chdir(original_directory)
                if sys.path[0] == str(REPOSITORY_ROOT):
                    sys.path.pop(0)

            snapshot = json.loads(data_path.read_text(encoding="utf-8"))
            self.assertEqual(len(snapshot), 1)
            self.assertEqual(
                snapshot[0]["date"], current_date.date().isoformat()
            )
            generated = json.loads(history_path.read_text(encoding="utf-8"))
            by_date = {record["date"]: record for record in generated}
            self.assertEqual(by_date[historical_date], historical)
            self.assertEqual(
                by_date[current_date.date().isoformat()]["symbol"], "7203.T"
            )
            self.assertTrue(data_path.read_text(encoding="utf-8").endswith("\n"))
            self.assertTrue(
                history_path.read_text(encoding="utf-8").endswith("\n")
            )
            self.assertEqual(
                list(Path(temp_dir).glob(".earnings_data_jp.*.tmp")), []
            )
            self.assertEqual(
                list(Path(temp_dir).glob(".earnings_history_jp.*.tmp")), []
            )
            generated_html = (Path(temp_dir) / "japan.html").read_text(
                encoding="utf-8"
            )
            self.assertIn('id="monthSelect"', generated_html)
            self.assertIn("initializeCalendarNavigation();", generated_html)
            self.assertIn("fetch('earnings_history_jp.json')", generated_html)

    def test_partial_spreadsheet_failure_does_not_rewrite_existing_data(self):
        original_data = '[{"symbol":"9999.T","date":"2026-08-05"}]\n'
        original_history = '[{"symbol":"7203.T","date":"2026-07-31"}]\n'
        spreadsheet = pd.DataFrame(
            [
                [
                    "2026-08-05",
                    "7203",
                    "トヨタ自動車",
                    "Toyota Motor",
                    "2027-03-31",
                    "輸送用機器",
                    "Transportation Equipment",
                    "第1四半期",
                    "1Q",
                    "プライム",
                    "Prime",
                ]
            ]
        )
        original_directory = Path.cwd()

        with tempfile.TemporaryDirectory(prefix="earnings-jp-partial-") as temp_dir:
            data_path = Path(temp_dir) / "earnings_data_jp.json"
            history_path = Path(temp_dir) / "earnings_history_jp.json"
            data_path.write_text(original_data, encoding="utf-8")
            history_path.write_text(original_history, encoding="utf-8")

            try:
                os.chdir(temp_dir)
                sys.path.insert(0, str(REPOSITORY_ROOT))
                with patch(
                    "requests.get", return_value=PartialJpxPageResponse()
                ), patch(
                    "pandas.read_excel",
                    side_effect=[spreadsheet, ValueError("temporary failure")],
                ):
                    with contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaisesRegex(
                            RuntimeError, "既存データを保持します"
                        ):
                            runpy.run_path(
                                str(REPOSITORY_ROOT / "generate_html_jp.py"),
                                run_name="__main__",
                            )
            finally:
                os.chdir(original_directory)
                if sys.path[0] == str(REPOSITORY_ROOT):
                    sys.path.pop(0)

            self.assertEqual(data_path.read_text(encoding="utf-8"), original_data)
            self.assertEqual(
                history_path.read_text(encoding="utf-8"), original_history
            )
            self.assertFalse((Path(temp_dir) / "japan.html").exists())
            self.assertEqual(
                list(Path(temp_dir).glob(".earnings_data_jp.*.tmp")), []
            )
            self.assertEqual(
                list(Path(temp_dir).glob(".earnings_history_jp.*.tmp")), []
            )

    def test_invalid_spreadsheet_row_does_not_rewrite_existing_data(self):
        original_data = '[{"symbol":"9999.T","date":"2026-08-05"}]\n'
        original_history = '[{"symbol":"7203.T","date":"2026-07-31"}]\n'
        spreadsheet = pd.DataFrame(
            [
                [
                    "not-a-date",
                    "7203",
                    "トヨタ自動車",
                    "Toyota Motor",
                    "2027-03-31",
                    "輸送用機器",
                    "Transportation Equipment",
                    "第1四半期",
                    "1Q",
                    "プライム",
                    "Prime",
                ]
            ]
        )
        original_directory = Path.cwd()

        with tempfile.TemporaryDirectory(prefix="earnings-jp-row-") as temp_dir:
            data_path = Path(temp_dir) / "earnings_data_jp.json"
            history_path = Path(temp_dir) / "earnings_history_jp.json"
            data_path.write_text(original_data, encoding="utf-8")
            history_path.write_text(original_history, encoding="utf-8")

            try:
                os.chdir(temp_dir)
                sys.path.insert(0, str(REPOSITORY_ROOT))
                with patch("requests.get", return_value=JpxPageResponse()), patch(
                    "pandas.read_excel", return_value=spreadsheet
                ):
                    with contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaisesRegex(
                            RuntimeError, "決算行を変換できなかった"
                        ):
                            runpy.run_path(
                                str(REPOSITORY_ROOT / "generate_html_jp.py"),
                                run_name="__main__",
                            )
            finally:
                os.chdir(original_directory)
                if sys.path[0] == str(REPOSITORY_ROOT):
                    sys.path.pop(0)

            self.assertEqual(data_path.read_text(encoding="utf-8"), original_data)
            self.assertEqual(
                history_path.read_text(encoding="utf-8"), original_history
            )
            self.assertFalse((Path(temp_dir) / "japan.html").exists())

    def test_known_undecided_and_footnote_rows_are_ignored(self):
        now = datetime.now()
        current_date = now.replace(day=1)
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)
        spreadsheet = pd.DataFrame(
            [
                [
                    current_date.date().isoformat(),
                    7203.0,
                    "トヨタ自動車",
                    "Toyota Motor",
                    "2027-03-31",
                    "輸送用機器",
                    "Transportation Equipment",
                    "第1四半期",
                    "1Q",
                    "プライム",
                    "Prime",
                ],
                [
                    "未定_Undecided",
                    "2502",
                    "アサヒグループHD",
                    "Asahi Group Holdings",
                    "2026-12-31",
                    "食料品",
                    "Foods",
                    "第2四半期",
                    "2Q",
                    "プライム",
                    "Prime",
                ],
                [
                    "注：発表日程は変更される場合があります",
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                ],
            ]
        )
        original_directory = Path.cwd()

        with tempfile.TemporaryDirectory(prefix="earnings-jp-known-rows-") as temp_dir:
            try:
                os.chdir(temp_dir)
                sys.path.insert(0, str(REPOSITORY_ROOT))
                with patch("requests.get", return_value=JpxPageResponse()), patch(
                    "pandas.read_excel", return_value=spreadsheet
                ):
                    with contextlib.redirect_stdout(io.StringIO()):
                        runpy.run_path(
                            str(REPOSITORY_ROOT / "generate_html_jp.py"),
                            run_name="__main__",
                        )
            finally:
                os.chdir(original_directory)
                if sys.path[0] == str(REPOSITORY_ROOT):
                    sys.path.pop(0)

            snapshot = json.loads(
                (Path(temp_dir) / "earnings_data_jp.json").read_text(
                    encoding="utf-8"
                )
            )
            history = json.loads(
                (Path(temp_dir) / "earnings_history_jp.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual([record["symbol"] for record in snapshot], ["7203.T"])
            self.assertEqual([record["symbol"] for record in history], ["7203.T"])

    def test_missing_date_on_a_populated_row_does_not_rewrite_data(self):
        now = datetime.now()
        current_date = now.replace(day=1)
        while current_date.weekday() >= 5:
            current_date += timedelta(days=1)
        original_data = '[{"symbol":"6758.T","date":"2026-08-05"}]\n'
        original_history = '[{"symbol":"6758.T","date":"2026-08-05"}]\n'
        spreadsheet = pd.DataFrame(
            [
                [
                    current_date.date().isoformat(),
                    "7203",
                    "トヨタ自動車",
                    "Toyota Motor",
                    "2027-03-31",
                    "輸送用機器",
                    "Transportation Equipment",
                    "第1四半期",
                    "1Q",
                    "プライム",
                    "Prime",
                ],
                [
                    None,
                    "6758",
                    "ソニーグループ",
                    "Sony Group",
                    "2027-03-31",
                    "電気機器",
                    "Electric Appliances",
                    "第1四半期",
                    "1Q",
                    "プライム",
                    "Prime",
                ],
            ]
        )
        original_directory = Path.cwd()

        with tempfile.TemporaryDirectory(prefix="earnings-jp-date-") as temp_dir:
            data_path = Path(temp_dir) / "earnings_data_jp.json"
            history_path = Path(temp_dir) / "earnings_history_jp.json"
            data_path.write_text(original_data, encoding="utf-8")
            history_path.write_text(original_history, encoding="utf-8")

            try:
                os.chdir(temp_dir)
                sys.path.insert(0, str(REPOSITORY_ROOT))
                with patch("requests.get", return_value=JpxPageResponse()), patch(
                    "pandas.read_excel", return_value=spreadsheet
                ):
                    with contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaisesRegex(
                            RuntimeError, "決算行を変換できなかった"
                        ):
                            runpy.run_path(
                                str(REPOSITORY_ROOT / "generate_html_jp.py"),
                                run_name="__main__",
                            )
            finally:
                os.chdir(original_directory)
                if sys.path[0] == str(REPOSITORY_ROOT):
                    sys.path.pop(0)

            self.assertEqual(data_path.read_text(encoding="utf-8"), original_data)
            self.assertEqual(
                history_path.read_text(encoding="utf-8"), original_history
            )
            self.assertFalse((Path(temp_dir) / "japan.html").exists())


if __name__ == "__main__":
    unittest.main()
