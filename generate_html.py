import os
import json
import pandas as pd
import requests
from datetime import date as date_type, datetime, timedelta
from earnings_utils import (
    deduplicate_earnings,
    load_existing_earnings,
    reconcile_earnings,
    write_earnings_atomically,
)
from html_template import build_html_head, build_header, build_controls, build_common_js

API_KEY = os.getenv("FINNHUB_API_KEY", "YOUR_API_KEY")

# TARGET_MONTHLY と TARGET_WEEKLY の定義
TARGET_MONTHLY = [
    # Tech Giants & Major Tech
    "AAPL", "MSFT", "GOOGL", "META", "AMZN", "NFLX", "TSLA", "NVDA", "IBM", "ORCL", "CSCO",
    "ADBE", "CRM", "INTC", "SNOW", "PANW", "PLTR",
    
    # Semiconductors
    "AMD", "TSM", "ASML", "QCOM", "AVGO", "TXN", "AMAT", "LRCX", "MU", "ARM", "ANET",
    "MRVL", "NXPI", "ADI", "ON", "MPWR",
    
    # Finance & Banks
    "JPM", "BAC", "WFC", "C", "MS", "GS", "BLK", "SCHW", "AXP", "V", "MA",
    "BNY", "USB", "PNC", "TFC", "TRV", "IBKR", "SYF", "KEY", "MTB", "HBAN",
    "RF", "ZION", "ALLY", "SOFI", "COF", "KKR", "BX",
    
    # Healthcare & Pharma
    "JNJ", "LLY", "UNH", "ABBV", "MRK", "PFE", "TMO", "ABT", "CVS", "HUM", "ELV",
    "ISRG", "REGN", "GILD", "BIIB", "AMGN", "ZTS", "AZN", "HCA",
    
    # Consumer Discretionary
    "DIS", "NKE", "SBUX", "MCD", "CMG", "TGT", "HD", "LOW", "BKNG", "MAR",
    "GM", "F", "ABNB", "UBER", "LYFT", "ETSY", "LULU",
    
    # Consumer Staples
    "PG", "KO", "PEP", "COST", "WMT", "MDLZ", "CL", "KDP", "WEN",
    
    # Energy
    "XOM", "CVX", "COP", "SLB", "BP", "OXY", "EOG", "MPC",
    
    # Industrial & Transportation
    "BA", "CAT", "GE", "HON", "RTX", "UPS", "FDX", "UNP", "CSX", "NSC",
    "GD", "LMT", "DE", "ITW", "DOV", "WM", "URI", "FAST",
    "AAL", "UAL", "DAL", "ALK",
    
    # Communication Services
    "VZ", "T", "TMUS", "CMCSA", "CHTR",
    
    # Materials & Industrials
    "NEM", "FCX", "NUE", "CLF", "STLD", "APD", "LIN", "ECL", "BALL", "CCK",
    
    # REITs & Real Estate
    "AMT", "PLD", "EQIX", "PSA", "AGNC",
    
    # FinTech & Payments
    "PYPL", "SQ", "COIN", "HOOD",
    
    # Other Notable
    "SPOT", "RDFN", "OPEN", "DUOL", "UPST", "ENPH", "GLW", "CBOE", "VRT", "CTLT",
    "KMI", "ENB", "RMBS", "WHR", "GNTX", "GFF", "SENS", "CLOV", "EVLV", "SIGA",
    "VIA", "FAST", "ERIC", "ACI", "LII", "PGNY", "INFY", "ALV", "WTFC", "RLI",
    "BOKF", "APH", "CLFD", "CNI", "LYB", "FET", "NVST", "EXAS", "SNDK", "NU", "DLO",

       # Additional Tech
    "ADBE", "CRM", "ORCL", "CSCO", "IBM", "SNOW", "PLTR", "PANW", "CRWD", "ZS",
    "DDOG", "NET", "MDB", "WDAY", "NOW", "TEAM", "ZM", "DOCU", "OKTA", "TWLO",
    "ARM", "SHOP", "SQ", "PYPL", "COIN", "RBLX", "U", "SPOT", "ABNB", "UBER", "LYFT",
    
    # Additional Semiconductors
    "MU", "MCHP", "NXPI", "ADI", "MRVL", "ON", "MPWR", "SWKS", "QRVO", "WOLF",
    
    # Additional Finance
    "BNY", "TFC", "USB", "PNC", "TRV", "AIG", "MET", "PRU", "ALL", "CB",
    "RF", "KEY", "HBAN", "MTB", "FITB", "CFG", "ZION", "ALLY", "SOFI",
    "IBKR", "SYF", "COF", "DFS", "KKR", "BX", "APO",
    
    # Additional Healthcare
    "CVS", "CI", "HUM", "ELV", "ISRG", "REGN", "VRTX", "GILD", "BIIB", "AMGN",
    "ZTS", "ILMN", "DXCM", "EW", "SYK", "BSX", "MDT", "HOLX",
    
    # Biotech
    "MRNA", "BNTX", "NVAX", "EXAS", "TDOC", "VEEV",
    
    # Consumer Discretionary
    "BKNG", "MAR", "HLT", "EXPE", "LVS", "MGM", "WYNN", "CCL", "RCL", "NCLH",
    "GM", "F", "RIVN", "LCID", "NIO", "LI", "XPEV",
    "ETSY", "EBAY", "W", "CHWY", "RVLV", "LULU", "DECK", "CROX", "TPR",
    
    # Consumer Staples
    "PG", "KO", "PEP", "COST", "WMT", "KR", "MDLZ", "CL", "GIS", "K", "HSY",
    "EL", "CLX", "CHD", "MO", "PM", "BTI",
    
    # Energy
    "OXY", "MPC", "VLO", "PSX", "HES", "DVN", "FANG", "BP", "SHEL", "TTE", "E",
    
    # Industrial
    "UNP", "CSX", "NSC", "GD", "LMT", "NOC", "DE", "EMR", "ITW", "MMM",
    "WM", "RSG", "URI", "FAST", "PCAR", "ODFL", "JBHT", "CHRW",
    "AAL", "UAL", "DAL", "LUV", "ALK",
    
    # Real Estate / REITs
    "AMT", "PLD", "EQIX", "PSA", "O", "WELL", "DLR", "SPG", "VICI", "AVB",
    
    # Materials
    "LIN", "APD", "ECL", "DD", "DOW", "NEM", "FCX", "NUE", "STLD", "CLF",
    "ALB", "MP", "LAC", "BALL", "CCK", "PKG",
    
    # Telecom
    "CMCSA", "CHTR", "LUMN",
    
    # Utilities
    "NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL", "WEC", "ES",
    
    # Other Notable
    "RDFN", "OPEN", "COIN", "HOOD", "UPST", "AFRM", "BNPL",
    "DUOL", "BMBL", "MTCH", "PINS", "SNAP", "TWTR",
    "ENPH", "SEDG", "RUN", "FSLR", "PLUG", "BE", "CLNE",
    "AGNC", "NLY", "STWD", "ARR",
    "NOK", "SPCX", "FIG", "SNPS", "COHR", "RIOT",
    
    # Additional broad coverage
    "BRK-B", "KLAC", "GEV", "DELL", "WDC", "TJX", "APP", "CDNS", "TER", "STX",
    "AMKR", "LSCC", "OLED", "LITE", "FLEX", "HPQ", "HPE", "SMCI", "MSTR", "INTU",
    "FTNT", "ADSK", "EA", "TTWO", "GDDY", "HUBS", "ROP", "PTC", "PAYC", "DT",
    "ESTC", "S", "IOT", "PATH", "MANH", "TYL", "CDW", "ETN", "PH", "TT",
    "IR", "CARR", "OTIS", "JCI", "ROK", "XYL", "PWR", "VST", "CEG", "AXON",
    "LHX", "TDG", "TXT", "HWM", "GNRC", "SPGI", "MCO", "ICE", "CME", "NDAQ",
    "STT", "AMP", "PGR", "AFL", "ACGL", "HIG", "AON", "AJG", "BRO", "RJF",
    "TROW", "DHR", "MCK", "COR", "CAH", "BMY", "GSK", "NVO", "NVS", "RMD",
    "IDXX", "ALNY", "ARGX", "GEHC", "WAT", "A", "IQV", "ZBH", "WST", "ROST",
    "AZO", "ORLY", "TSCO", "ULTA", "YUM", "DPZ", "MNST", "CELH", "KMB", "SYY",
    "DG", "DLTR", "BBY", "GME", "DKNG", "WMB", "LNG", "TRGP", "EQT", "HAL",
    "BKR", "SHW", "PPG", "MLM", "VMC", "CF", "MOS", "DHI", "LEN", "PHM",
    "TOL",
]

ASSETS_DIR = "assets/logos/us"
DATA_FILE = "earnings_data.json"
# 2026-07 is intentionally available as a partial history month (July 27-31).
HISTORY_START_MONTH = "2026-07"

print(f"📊 TARGET_MONTHLY: {len(TARGET_MONTHLY)} symbols")

# 欠損値を0に置き換える
def clean_record(record):
    return {k: (0 if v is None else v) for k, v in record.items()}


today = datetime.now()

# 今月の1日
month_start = today.replace(day=1)

# 月初の週の月曜日まで遡る
while month_start.weekday() != 0:  # 0 = Monday
    month_start -= timedelta(days=1)

# 翌月を計算
if today.month == 12:
    next_month = today.replace(year=today.year + 1, month=1, day=1)
else:
    next_month = today.replace(month=today.month + 1, day=1)

# 翌月の末日を計算
if next_month.month == 12:
    next_month_end = next_month.replace(year=next_month.year + 1, month=1, day=1) - timedelta(days=1)
else:
    next_month_end = next_month.replace(month=next_month.month + 1, day=1) - timedelta(days=1)

print(f"📅 Period: {month_start.strftime('%Y-%m-%d')} to {next_month_end.strftime('%Y-%m-%d')}")

# 月～金のみの日付リストを生成
weekday_dates = []
current = month_start
while current <= next_month_end:
    if current.weekday() < 5:  # 0-4 = Mon-Fri
        weekday_dates.append(current)
    current += timedelta(days=1)

# 週ごとに分割(月曜から金曜までの5日間)
weeks = []
current_week = []
for date in weekday_dates:
    # 月曜日から新しい週を開始
    if date.weekday() == 0:
        if current_week:  # 前の週があれば保存
            weeks.append(current_week)
        current_week = [date]
    else:
        current_week.append(date)
if current_week:
    weeks.append(current_week)

print(f"📅 Total weeks: {len(weeks)}")

# 前回の予定と最新API応答を照合するため、上書き前のデータを保持する
previous_data = load_existing_earnings(DATA_FILE)

# APIからデータ取得（週単位）
all_data = []
successful_ranges = []
for week in weeks:
    if not week:
        continue
    
    from_date = week[0].strftime("%Y-%m-%d")
    to_date = week[-1].strftime("%Y-%m-%d")
    
    url = f"https://finnhub.io/api/v1/calendar/earnings?from={from_date}&to={to_date}&token={API_KEY}"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or "earningsCalendar" not in payload:
            raise ValueError("earningsCalendar is missing from the API response")

        week_data = payload["earningsCalendar"]
        if not isinstance(week_data, list):
            raise ValueError("earningsCalendar must be an array")

        cleaned_week_data = []
        for record in week_data:
            if not isinstance(record, dict):
                raise ValueError("earningsCalendar contains a non-object record")
            if record.get("symbol") not in TARGET_MONTHLY:
                continue
            if not isinstance(record.get("date"), str):
                raise ValueError("an earnings record is missing its date")
            record_date = date_type.fromisoformat(record["date"])
            if not week[0].date() <= record_date <= week[-1].date():
                raise ValueError("an earnings record is outside the requested range")
            cleaned_week_data.append(clean_record(record))

        all_data.extend(cleaned_week_data)
        successful_ranges.append((week[0].date(), week[-1].date()))
        print(f"取得完了: {from_date} - {to_date} ({len(week_data)}件)")
    except Exception as e:
        print(f"エラー: {from_date} - {to_date} - {e}")

# 同一銘柄の同一日に対するレコードはカード1枚分として扱う
raw_data_count = len(all_data)
all_data = deduplicate_earnings(all_data)
duplicate_count = raw_data_count - len(all_data)
if duplicate_count:
    print(f"重複 {duplicate_count} 件を除外しました")

if successful_ranges:
    all_data = reconcile_earnings(
        previous_data,
        all_data,
        today=today.date(),
        window_start=month_start.date(),
        window_end=next_month_end.date(),
        successful_ranges=successful_ranges,
    )
else:
    all_data = previous_data
    print("API取得に成功した期間がないため、既存データを保持しました")

# JSONファイルに出力
if successful_ranges or not os.path.exists(DATA_FILE):
    write_earnings_atomically(DATA_FILE, all_data)
    print(f"合計 {len(all_data)} 件のデータを保存しました")
else:
    print(f"合計 {len(all_data)} 件の既存データを利用します")

# =====================
# HTML 生成
# =====================
symbols_json  = json.dumps(TARGET_MONTHLY)
calendar_seed_months_json = json.dumps([
    today.strftime("%Y-%m"),
    next_month.strftime("%Y-%m"),
])
history_start_month_json = json.dumps(HISTORY_START_MONTH)
date_str      = today.strftime('%B %d, %Y')
updated_str   = today.strftime('%Y-%m-%d %H:%M')

html = build_html_head("Earnings Calendar", lang="en")
html += "<body>\n"
html += build_header("Earnings Calendar", date_str)
html += build_controls(active_market="us", search_placeholder="Search by symbol (e.g., AAPL, TSLA)...")
html += '<div class="container" id="calendar"></div>\n'
html += f'<footer>Last updated: {updated_str}</footer>\n'

html += f"""<script>
let earningsData = [];
let currentMode = 'monthly';
let currentWeek = 0;
let weeks = [];
let availableMonths = [];
let selectedMonth = '';
let calendarSeedMonths = {calendar_seed_months_json};
let calendarHistoryStartMonth = {history_start_month_json};
let targetSymbols = {symbols_json};

{build_common_js()}

function deduplicateEarnings(data) {{
  const seen = new Set();
  return data.filter(e => {{
    const key = JSON.stringify([e.symbol, e.date]);
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  }});
}}

fetch('earnings_data.json')
  .then(res => res.json())
  .then(data => {{
    earningsData = deduplicateEarnings(
      data.filter(e => e.status !== 'changed')
    );
    initializeCalendarNavigation();
    renderCalendar();
    scrollToCurrentWeek();
  }});

function renderCalendar() {{
  const calendar = document.getElementById('calendar');
  calendar.innerHTML = '';

  const headerRow = document.createElement('div');
  headerRow.className = 'weekday-header';
  ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].forEach(day => {{
    const cell = document.createElement('div');
    cell.className = 'weekday-cell';
    cell.textContent = day;
    headerRow.appendChild(cell);
  }});
  calendar.appendChild(headerRow);

  if (currentMode === 'monthly') {{
    let renderedWeeks = 0;
    weeks.forEach((weekDates, weekIndex) => {{
      const hasEarnings = weekDates.some(dateStr =>
        dateStr.startsWith(selectedMonth) && earningsData.some(e =>
          e.date === dateStr && targetSymbols.includes(e.symbol)
        )
      );
      if (!hasEarnings) return;
      const weekRow = document.createElement('div');
      weekRow.className = 'week-row week-row-wrapper';
      weekRow.dataset.weekIndex = weekIndex;
      weekDates.forEach(dateStr => weekRow.appendChild(renderDay(dateStr)));
      calendar.appendChild(weekRow);
      renderedWeeks++;
    }});
    if (renderedWeeks === 0) appendEmptyMessage(calendar, 'No earnings data for this month');
  }} else {{
    const weekDates = weeks[currentWeek];
    const hasEarnings = weekDates && weekDates.some(dateStr =>
      dateStr.startsWith(selectedMonth) && earningsData.some(e =>
        e.date === dateStr && targetSymbols.includes(e.symbol)
      )
    );
    document.getElementById('weekLabel').textContent = `Week ${{currentWeek + 1}}: ${{formatDateRange(weeks[currentWeek])}}`;
    document.getElementById('prevWeek').disabled = currentWeek === 0;
    document.getElementById('nextWeek').disabled = currentWeek === weeks.length - 1;
    document.querySelectorAll('.week-dot').forEach((dot, idx) => dot.classList.toggle('active', idx === currentWeek));

    if (hasEarnings) {{
      const weekRow = document.createElement('div');
      weekRow.className = 'week-row';
      weekDates.forEach(dateStr => weekRow.appendChild(renderDay(dateStr)));
      calendar.appendChild(weekRow);
    }} else {{
      appendEmptyMessage(calendar, 'No earnings data for this week');
    }}
  }}
  if (document.getElementById('searchInput').value.trim()) searchSymbols();
}}

function appendEmptyMessage(calendar, message) {{
  const noDataDiv = document.createElement('div');
  noDataDiv.className = 'empty-calendar';
  noDataDiv.textContent = message;
  calendar.appendChild(noDataDiv);
}}

function renderDay(dateStr) {{
  const today = getLocalDateKey();
  const isOutsideMonth = !dateStr.startsWith(selectedMonth);
  const earnings = earningsData.filter(e =>
    !isOutsideMonth && e.date === dateStr && targetSymbols.includes(e.symbol)
  )
    .sort((a, b) => {{
      const ai = targetSymbols.indexOf(a.symbol), bi = targetSymbols.indexOf(b.symbol);
      if (ai === -1 && bi === -1) return a.symbol.localeCompare(b.symbol);
      if (ai === -1) return 1; if (bi === -1) return -1;
      return ai - bi;
    }});

  const dayDiv = document.createElement('div');
  dayDiv.className = 'day';
  if (isOutsideMonth) dayDiv.classList.add('outside-month');
  if (dateStr === today) dayDiv.classList.add('today');

  if (currentMode === 'monthly' && !isOutsideMonth) {{
    dayDiv.style.cursor = 'pointer';
    dayDiv.onclick = () => {{
      const weekIndex = weeks.findIndex(week => week.includes(dateStr));
      if (weekIndex !== -1) {{ currentWeek = weekIndex; switchMode('weekly'); }}
    }};
  }}

  const [, month, day] = dateStr.split('-');
  const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  const dateDiv = document.createElement('div');
  dateDiv.className = 'date';
  dateDiv.textContent = `${{monthNames[parseInt(month) - 1]}}, ${{parseInt(day)}}`;
  dayDiv.appendChild(dateDiv);

  if (earnings.length > 0) {{
    const logosDiv = document.createElement('div');
    logosDiv.className = 'logos';
    const displayEarnings = currentMode === 'monthly' ? earnings.slice(0, 9) : earnings;
    displayEarnings.forEach(e => {{
      const card = document.createElement('div');
      card.className = 'logo-card';
      if (favorites.includes(e.symbol)) card.classList.add('favorite');
      card.dataset.symbol = e.symbol;
      card.dataset.status = e.status || 'confirmed';
      if (e.status === 'unconfirmed') {{
        card.classList.add('unconfirmed');
        const statusText = `${{e.symbol}}: earnings date unconfirmed`;
        card.title = statusText;
        card.setAttribute('aria-label', statusText);
      }}
      card.addEventListener('click', ev => {{
        ev.stopPropagation();
        window.webkit.messageHandlers.favoriteHandler.postMessage({{ symbol: e.symbol }});
      }});
      const img = document.createElement('img');
      img.src = '{ASSETS_DIR}/' + e.symbol + '.png';
      img.alt = img.title = e.symbol;
      img.onerror = () => img.style.display = 'none';
      const symbolDiv = document.createElement('div');
      symbolDiv.className = 'symbol';
      symbolDiv.textContent = e.symbol;
      card.appendChild(img);
      card.appendChild(symbolDiv);
      logosDiv.appendChild(card);
    }});
    dayDiv.appendChild(logosDiv);
    if (currentMode === 'monthly' && earnings.length > 9) {{
      const moreDiv = document.createElement('div');
      moreDiv.className = 'more-count';
      moreDiv.textContent = `+${{earnings.length - 9}} more`;
      dayDiv.appendChild(moreDiv);
    }}
  }} else if (!isOutsideMonth) {{
    const noEarnings = document.createElement('div');
    noEarnings.className = 'no-earnings';
    noEarnings.textContent = 'No Earnings';
    dayDiv.appendChild(noEarnings);
  }}
  return dayDiv;
}}

function searchSymbols() {{
  const query = document.getElementById('searchInput').value.toUpperCase().trim();
  document.querySelectorAll('.logo-card').forEach(card => {{
    card.classList.toggle('hidden', query !== '' && !card.dataset.symbol.includes(query));
  }});
}}
</script>
</body>
</html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✅ index.html 生成完了")
