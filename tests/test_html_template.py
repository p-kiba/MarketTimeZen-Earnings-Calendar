from pathlib import Path
import os
import shutil
import subprocess
import unittest

from html_template import COMMON_CSS, build_common_js, build_controls


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class CalendarNavigationTemplateTests(unittest.TestCase):
    def test_controls_include_accessible_month_navigation(self):
        controls = build_controls("us", "Search...")

        self.assertIn('id="monthNav"', controls)
        self.assertIn('id="monthSelect"', controls)
        self.assertIn('onclick="changeMonth(-1)"', controls)
        self.assertIn('onclick="changeMonth(1)"', controls)
        self.assertIn('aria-label="Displayed month"', controls)

    def test_common_javascript_builds_month_weeks_and_preserves_the_query(self):
        javascript = build_common_js()

        self.assertIn("function buildWeeksForMonth(monthKey)", javascript)
        self.assertIn("function initializeCalendarNavigation()", javascript)
        self.assertIn("function selectMonth(monthKey)", javascript)
        self.assertIn("params.set('month', selectedMonth)", javascript)
        self.assertIn('data-week-index="${currentWeek}"', javascript)

    def test_generated_pages_include_the_shared_navigation(self):
        pages = [
            (
                "index.html",
                build_controls(
                    "us", "Search by symbol (e.g., AAPL, TSLA)..."
                ),
            ),
            (
                "japan.html",
                build_controls(
                    "jp", "Search by symbol or name (7203, SONY)..."
                ),
            ),
        ]

        for filename, controls in pages:
            with self.subTest(filename=filename):
                html = (REPOSITORY_ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(f"<style>\n{COMMON_CSS}\n</style>", html)
                self.assertIn(controls, html)
                self.assertIn(build_common_js(), html)

    @unittest.skipUnless(shutil.which("node"), "Node.js is required")
    def test_month_calculations_cover_year_end_and_leap_day(self):
        script = """
const NativeDate = Date;
let fixedNow = '2027-01-01T00:30:00+09:00';
class FixedDate extends NativeDate {
  constructor(...args) {
    super(...(args.length ? args : [fixedNow]));
  }
}
FixedDate.UTC = NativeDate.UTC;
FixedDate.parse = NativeDate.parse;
global.Date = FixedDate;
let replacedUrl = '';
const elements = {
  monthSelect: { innerHTML: '', value: '', options: [], appendChild(option) { this.options.push(option); } },
  prevMonth: { disabled: false },
  nextMonth: { disabled: false }
};
global.window = {
  location: { search: '', pathname: '/index.html', hash: '' },
  history: { replaceState(_state, _title, url) { replacedUrl = url; } },
  addEventListener() {}
};
global.document = {
  addEventListener() {},
  getElementById(id) { return elements[id]; },
  createElement() { return { value: '', textContent: '' }; }
};
let earningsData = [];
let currentMode = 'monthly';
let currentWeek = 0;
let weeks = [];
let availableMonths = [];
let selectedMonth = '';
let calendarSeedMonths = [];
let calendarHistoryStartMonth = '2026-07';
let targetSymbols = [];
function renderCalendar() {}
""" + build_common_js() + """
function assert(condition, message) {
  if (!condition) throw new Error(message);
}
assert(shiftMonth('2026-12', 1) === '2027-01', 'year rollover failed');
assert(shiftMonth('2027-01', -1) === '2026-12', 'reverse rollover failed');
assert(getLocalDateKey() === '2027-01-01', 'local date boundary failed');
assert(
  JSON.stringify(enumerateMonths('2026-11', '2027-02')) ===
    JSON.stringify(['2026-11', '2026-12', '2027-01', '2027-02']),
  'month enumeration failed'
);
const january = buildWeeksForMonth('2027-01');
assert(january[0][4] === '2027-01-01', 'weekday alignment failed');
const august = buildWeeksForMonth('2026-08');
assert(august[0][0] === '2026-08-03', 'empty leading week was not removed');
const leapFebruary = buildWeeksForMonth('2028-02').flat();
assert(leapFebruary.includes('2028-02-29'), 'leap day is missing');
assert(buildWeeksForMonth('2028-02').every(week => week.length === 5), 'week width failed');
fixedNow = '2026-08-11T00:30:00+09:00';
window.location.search = '?month=2026-07';
earningsData = [
  { symbol: 'AAPL', date: '2026-07-30' },
  { symbol: 'AAPL', date: '2026-08-05' },
  { symbol: 'AAPL', date: '2026-09-01' }
];
targetSymbols = ['AAPL'];
calendarSeedMonths = ['2026-08', '2026-09'];
initializeCalendarNavigation();
assert(
  JSON.stringify(availableMonths) === JSON.stringify(['2026-07', '2026-08', '2026-09']),
  'partial history month was not exposed'
);
assert(selectedMonth === '2026-07', 'requested partial month was not selected');
assert(replacedUrl === '', 'valid partial month unexpectedly changed the URL');
"""

        subprocess.run(
            [shutil.which("node"), "-"],
            input=script,
            text=True,
            check=True,
            capture_output=True,
            env={**os.environ, "TZ": "Asia/Tokyo"},
        )

    @unittest.skipUnless(shutil.which("node"), "Node.js is required")
    def test_generated_page_scripts_compile(self):
        script = """
const fs = require('fs');
for (const filename of process.argv.slice(2)) {
  const html = fs.readFileSync(filename, 'utf8');
  const match = html.match(/<script>([\\s\\S]*)<\\/script>/);
  if (!match) throw new Error(`script missing from ${filename}`);
  new Function(match[1]);
}
"""
        subprocess.run(
            [
                shutil.which("node"),
                "-e",
                script,
                str(REPOSITORY_ROOT / "index.html"),
                str(REPOSITORY_ROOT / "japan.html"),
            ],
            text=True,
            check=True,
            capture_output=True,
        )


if __name__ == "__main__":
    unittest.main()
