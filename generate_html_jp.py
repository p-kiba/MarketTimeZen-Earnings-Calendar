import json
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from earnings_utils import (
    load_existing_earnings,
    merge_earnings_history,
    sort_earnings,
    write_earnings_atomically,
)
from html_template import build_html_head, build_header, build_controls, build_common_js

# 日本株の銘柄リスト（時価総額順）
TARGET_JP = [
    # 時価総額上位
    "7203.T",  # トヨタ自動車
    "8306.T",  # 三菱UFJ
    "9984.T",  # ソフトバンクグループ
    "8035.T",  # 東京エレクトロン
    "6861.T",  # キーエンス
    "6501.T",  # 日立製作所
    "9432.T",  # NTT
    "8316.T",  # 三井住友FG
    "7974.T",  # 任天堂
    "6758.T",  # ソニーグループ

    # 製造・自動車
    "7267.T",  # ホンダ
    "7201.T",  # 日産自動車
    "7752.T",  # リコー
    "6752.T",  # パナソニック
    "6702.T",  # 富士通

    # 半導体・テクノロジー
    "6723.T",  # ルネサスエレクトロニクス
    "6645.T",  # オムロン
    "6954.T",  # ファナック
    "6971.T",  # 京セラ
    "6594.T",  # 日本電産（ニデック）
    "4063.T",  # 信越化学工業
    "6920.T",  # レーザーテック
    "7735.T",  # SCREENホールディングス
    "6857.T",  # アドバンテスト

    # 金融
    "8411.T",  # みずほFG
    "8604.T",  # 野村ホールディングス
    "8308.T",  # りそなホールディングス
    "8355.T",  # 静岡銀行
    "8253.T",  # クレディセゾン
    "8750.T",  # 第一生命ホールディングス
    "8725.T",  # MS&ADインシュアランス
    "8630.T",  # SOMPOホールディングス

    # 通信
    "9433.T",  # KDDI
    "9434.T",  # ソフトバンク
    "9613.T",  # NTTデータ
    "9766.T",  # コナミグループ
    "4689.T",  # LINEヤフー
    "3659.T",  # ネクソン

    # 医薬品
    "4502.T",  # 武田薬品
    "4519.T",  # 中外製薬

    # 小売・消費
    "9983.T",  # ファーストリテイリング
    "4911.T",  # 資生堂
    "2914.T",  # JT

    # 商社
    "8001.T",  # 伊藤忠商事
    "8002.T",  # 丸紅
    "8015.T",  # 豊田通商
    "8031.T",  # 三井物産
    "8053.T",  # 住友商事
    "8058.T",  # 三菱商事

    # 重工・インフラ
    "7011.T",  # 三菱重工業
    "7012.T",  # 川崎重工業
    "7013.T",  # IHI
    "9501.T",  # 東京電力HD
    "9502.T",  # 中部電力
    "9503.T",  # 関西電力
    "9508.T",  # 九州電力
    "9531.T",  # 東京ガス
    "9532.T",  # 大阪ガス

    # 金融追加
    "7182.T",  # ゆうちょ銀行
    "7186.T",  # コンコルディアFG
    "7337.T",  # ひろぎんHD
    "8410.T",  # セブン銀行
    "8424.T",  # 芙蓉総合リース
    "8585.T",  # オリエントコーポ
    "8591.T",  # オリックス
    "8766.T",  # 東京海上HD
    "8795.T",  # T&D HD

    # 不動産
    "8801.T",  # 三井不動産
    "8802.T",  # 三菱地所
    "8830.T",  # 住友不動産
    "3289.T",  # 東急不動産HD

    # 建設
    "1801.T",  # 大成建設
    "1802.T",  # 大林組
    "1803.T",  # 清水建設
    "1925.T",  # 大和ハウス
    "1928.T",  # 積水ハウス

    # 素材・化学
    "3402.T",  # 東レ
    "3407.T",  # 旭化成
    "4004.T",  # レゾナック
    "4188.T",  # 三菱ケミカル
    "4452.T",  # 花王
    "4902.T",  # コニカミノルタ
    "5108.T",  # ブリヂストン
    "5332.T",  # TOTO
    "5333.T",  # 日本ガイシ

    # 機械・精密
    "6301.T",  # コマツ
    "6305.T",  # 日立建機
    "6367.T",  # ダイキン工業
    "6471.T",  # 日本精工
    "6479.T",  # ミネベアミツミ
    "6503.T",  # 三菱電機
    "6640.T",  # I-PEX
    "6724.T",  # セイコーエプソン
    "7731.T",  # ニコン
    "7741.T",  # HOYA
    "7751.T",  # キヤノン
    "7832.T",  # バンダイナムコ

    # IT・通信
    "3626.T",  # TIS
    "4307.T",  # 野村総合研究所
    "4324.T",  # 電通グループ
    "4385.T",  # メルカリ
    "4704.T",  # トレンドマイクロ
    "4755.T",  # 楽天グループ
    "6098.T",  # リクルートHD
    "6701.T",  # NEC
    "6753.T",  # シャープ

    # 輸送
    "9020.T",  # JR東日本
    "9021.T",  # JR西日本
    "9022.T",  # JR東海
    "9101.T",  # 日本郵船
    "9104.T",  # 商船三井
    "9107.T",  # 川崎汽船

    # 小売・消費
    "2502.T",  # アサヒ
    "2503.T",  # キリン
    "2801.T",  # キッコーマン
    "2802.T",  # 味の素
    "2871.T",  # ニチレイ
    "3086.T",  # Jフロント
    "3092.T",  # ZOZO
    "3382.T",  # セブン&アイ
    "7453.T",  # 良品計画
    "8267.T",  # イオン
    "9843.T",  # ニトリHD

    # エンタメ・ネット
    "4661.T",  # オリエンタルランド
    "3774.T",  # インターネットイニシアティブ（IIJ）
    "3635.T",  # コーエーテクモ
    "3769.T",  # GMOペイメントゲートウェイ
    "3903.T",  # gumi
    "3938.T",  # LINE WORKS
    "6460.T",  # セガサミーHD
    "9697.T",  # カプコン


    # EC・サービス
    "3064.T",  # MonotaRO
    "3391.T",  # ツルハHD
    "3563.T",  # FOOD & LIFE（スシロー）
    "4684.T",  # オービック
    "4732.T",  # USS
    "6196.T",  # ストライク
    "6532.T",  # ベイカレント
    "6856.T",  # 堀場製作所

    # 医療・ヘルスケア
    "2413.T",  # エムスリー
    "4543.T",  # テルモ
    "4568.T",  # 第一三共
    "7747.T",  # 朝日インテック

    # 消費財
    "2229.T",  # カルビー
    "2269.T",  # 明治HD
    "2579.T",  # コカ・コーラBJH
    "2809.T",  # キユーピー
    "4922.T",  # コーセー

    # 住宅・内需
    "1878.T",  # 大東建託
    "2127.T",  # 日本M&A
    "2875.T",  # 東洋水産
]

ASSETS_DIR = "assets/logos/ja"
DATA_FILE = "earnings_data_jp.json"
HISTORY_FILE = "earnings_history_jp.json"
# 2026-07 contains only the spillover week; 2026-08 is the first complete month.
HISTORY_START_MONTH = "2026-08"
UNDECIDED_DATE_LABELS = {"未定_Undecided"}


def normalize_jpx_code(value):
    """Return a stable JPX security code, or an empty string for blank cells."""
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    text = str(value).strip()
    return "" if text.lower() in {"", "nan", "none"} else text

# =====================
# 取得対象期間
# （今月のカレンダー開始〜翌月末）
# =====================
today = datetime.now()

month_start = today.replace(day=1)

# 月初の週の月曜日まで戻す
while month_start.weekday() != 0:
    month_start -= timedelta(days=1)

# 翌月1日
if today.month == 12:
    next_month = today.replace(year=today.year + 1, month=1, day=1)
else:
    next_month = today.replace(month=today.month + 1, day=1)

# 翌月末
if next_month.month == 12:
    next_month_end = (next_month.replace(year=next_month.year + 1, month=1, day=1) - timedelta(days=1))
else:
    next_month_end = (next_month.replace(month=next_month.month + 1, day=1) - timedelta(days=1))

period_start = month_start.date()
period_end = next_month_end.date()

print(f"📅 Period: {period_start} to {period_end}")

weeks = []
current = month_start
while current.date() <= period_end:
    week = [current + timedelta(days=i) for i in range(5)]
    weeks.append(week)
    current += timedelta(days=7)

# =====================
# JPXページ取得
# =====================
PAGE_URL = "https://www.jpx.co.jp/listing/event-schedules/financial-announcement/"
BASE_URL = "https://www.jpx.co.jp/listing/event-schedules/financial-announcement/tvdivq0000001ofb-att/"
headers  = {"User-Agent": "Mozilla/5.0"}

response = requests.get(PAGE_URL, headers=headers)
response.encoding = response.apparent_encoding
soup = BeautifulSoup(response.text, "html.parser")

matches = sorted(set(
    a["href"].split("/")[-1]
    for a in soup.find_all("a", href=True)
    if "kessan" in a["href"] and a["href"].endswith(".xlsx")
))
print("📄 Found files:", matches)
if not matches:
    raise Exception("決算ファイルが見つかりません")

# =====================
# 全xlsx読み込み
# =====================
dfs = []
failed_files = []
for file in matches:
    try:
        df = pd.read_excel(BASE_URL + file, engine="openpyxl", header=4)
        df.columns = ["date", "code", "name_ja", "name_en", "fiscal_year_end",
                      "industry_ja", "industry_en", "type", "fiscal_period",
                      "market_ja", "market_en"]
        dfs.append(df)
        print(f"⬇️ Loaded: {file}")
    except Exception as e:
        failed_files.append(file)
        print(f"❌ Failed: {file} - {e}")

if failed_files:
    raise RuntimeError(
        "一部の決算ファイルを読み込めなかったため、既存データを保持します: "
        + ", ".join(failed_files)
    )

if not dfs:
    raise Exception("xlsx読み込み失敗")

df = pd.concat(dfs, ignore_index=True)
df = df.where(pd.notnull(df), None)
print(f"📊 Total rows: {len(df)}")

# =====================
# JSON形式へ変換・保存
# =====================
all_data = []
failed_rows = []
undecided_rows = []
ignored_note_rows = []
for row_index, row in df.iterrows():
    raw_date = row["date"]
    code = normalize_jpx_code(row["code"])
    if raw_date is None or pd.isna(raw_date):
        if code:
            failed_rows.append(str(row_index))
        continue

    raw_date_text = str(raw_date).strip()
    if raw_date_text in UNDECIDED_DATE_LABELS:
        if code:
            undecided_rows.append(str(row_index))
        else:
            ignored_note_rows.append(str(row_index))
        continue

    try:
        date_obj = pd.to_datetime(raw_date).date()
    except (TypeError, ValueError, OverflowError):
        if code:
            failed_rows.append(str(row_index))
        else:
            ignored_note_rows.append(str(row_index))
        continue

    if not period_start <= date_obj <= period_end:
        continue

    if not code:
        failed_rows.append(str(row_index))
        continue

    all_data.append({
        "date":            date_obj.strftime("%Y-%m-%d"),
        "symbol":          f"{code}.T",
        "name_ja":         row["name_ja"]         if pd.notna(row["name_ja"])         else "",
        "name_en":         row["name_en"]         if pd.notna(row["name_en"])         else "",
        "market":          row["market_ja"]       if pd.notna(row["market_ja"])       else "",
        "industry":        row["industry_ja"]     if pd.notna(row["industry_ja"])     else "",
        "fiscal_year_end": str(row["fiscal_year_end"]) if pd.notna(row["fiscal_year_end"]) else "",
        "fiscal_period":   row["fiscal_period"]   if pd.notna(row["fiscal_period"])   else "",
    })

if failed_rows:
    raise RuntimeError(
        "一部の決算行を変換できなかったため、既存データを保持します: "
        + ", ".join(failed_rows[:10])
    )
if undecided_rows:
    print(f"⏸️ Date undecided: {len(undecided_rows)} rows")
if ignored_note_rows:
    print(f"ℹ️ Ignored JPX note rows: {len(ignored_note_rows)} rows")

unique = sort_earnings(all_data)
target_symbols = set(TARGET_JP)
target_snapshot = [
    record for record in unique if record["symbol"] in target_symbols
]
if not unique or not target_snapshot:
    raise RuntimeError(
        "対象期間の表示データが空のため、既存データを保持します"
    )
if os.path.exists(HISTORY_FILE):
    previous_history = [
        record
        for record in load_existing_earnings(HISTORY_FILE)
        if record.get("symbol") in target_symbols
    ]
else:
    previous_history = [
        record
        for record in load_existing_earnings(DATA_FILE)
        if record.get("symbol") in target_symbols
    ]
history = merge_earnings_history(
    previous_history,
    target_snapshot,
    window_start=period_start,
    window_end=period_end,
    preserve_through=today.date(),
)
write_earnings_atomically(DATA_FILE, unique)
write_earnings_atomically(HISTORY_FILE, history)
print(f"\n✅ 全銘柄データ保存完了: {len(unique)} 件")
print(f"✅ 表示用履歴保存完了: {len(history)} 件")

# =====================
# HTML 生成
# =====================
symbols_json = json.dumps(TARGET_JP)
calendar_seed_months_json = json.dumps([
    today.strftime("%Y-%m"),
    next_month.strftime("%Y-%m"),
])
history_start_month_json = json.dumps(HISTORY_START_MONTH)
date_str     = today.strftime('%B %d, %Y')
updated_str  = today.strftime('%Y-%m-%d %H:%M')

html = build_html_head("Japan Earnings Calendar", lang="ja")
html += "<body>\n"
html += build_header("Japan Earnings Calendar", date_str)
html += build_controls(active_market="jp", search_placeholder="Search by symbol or name (7203, SONY)...")
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

fetch('earnings_history_jp.json')
  .then(res => res.json())
  .then(data => {{
    earningsData = data;
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
      card.dataset.symbol  = e.symbol;
      card.dataset.nameJa  = e.name_ja || '';
      card.dataset.nameEn  = e.name_en || '';
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
  const query     = document.getElementById('searchInput').value.trim();
  const queryUpper = query.toUpperCase();
  document.querySelectorAll('.logo-card').forEach(card => {{
    const symbol = (card.dataset.symbol || '').toUpperCase();
    const nameJa = (card.dataset.nameJa || '');
    const nameEn = (card.dataset.nameEn || '').toUpperCase();
    const match  = !query
      || symbol.includes(queryUpper)
      || nameJa.includes(query)
      || nameEn.includes(queryUpper);
    card.classList.toggle('hidden', !match);
  }});
}}
</script>
</body>
</html>
"""

with open("japan.html", "w", encoding="utf-8") as f:
    f.write(html)
print("✅ japan.html 生成完了")
