import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

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
    next_month_end = (
        next_month.replace(
            year=next_month.year + 1,
            month=1,
            day=1
        ) - timedelta(days=1)
    )
else:
    next_month_end = (
        next_month.replace(
            month=next_month.month + 1,
            day=1
        ) - timedelta(days=1)
    )

period_start = month_start.date()
period_end = next_month_end.date()

print(f"📅 Period: {period_start} to {period_end}")

# 週リスト生成（月〜金）
weeks = []

current = month_start

while current.date() <= period_end:
    week = []

    for i in range(5):  # Monday-Friday
        week.append(current + timedelta(days=i))

    weeks.append(week)

    current += timedelta(days=7)

# =====================
# JPXページ取得
# =====================
PAGE_URL = "https://www.jpx.co.jp/listing/event-schedules/financial-announcement/"
BASE_URL = "https://www.jpx.co.jp/listing/event-schedules/financial-announcement/tvdivq0000001ofb-att/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(PAGE_URL, headers=headers)
response.encoding = response.apparent_encoding
html = response.text

# =====================
# xlsxリンク抽出
# =====================
soup = BeautifulSoup(html, "html.parser")

matches = []

for a in soup.find_all("a", href=True):
    href = a["href"]

    if "kessan" in href and href.endswith(".xlsx"):
        filename = href.split("/")[-1]
        matches.append(filename)

matches = sorted(set(matches))

print("📄 Found files:")
for m in matches:
    print(" ", m)

if not matches:
    raise Exception("決算ファイルが見つかりません")

# =====================
# 全xlsx読み込み
# =====================
dfs = []

for file in matches:
    try:
        url = BASE_URL + file
        print(f"⬇️ Loading: {file}")

        df = pd.read_excel(
            url,
            engine="openpyxl",
            header=4
        )

        df.columns = [
            "date",
            "code",
            "name_ja",
            "name_en",
            "fiscal_year_end",
            "industry_ja",
            "industry_en",
            "type",
            "fiscal_period",
            "market_ja",
            "market_en"
        ]

        dfs.append(df)

    except Exception as e:
        print(f"❌ Failed: {file} - {e}")

if not dfs:
    raise Exception("xlsx読み込み失敗")

# 全ファイル結合
df = pd.concat(dfs, ignore_index=True)

# =====================
# 銘柄フィルタ
# =====================
df["code"] = df["code"].astype(str)

filtered = df
filtered = filtered.where(pd.notnull(filtered), None)

print(f"📊 Total rows: {len(filtered)}")

# =====================
# JSON形式へ変換
# =====================
all_data = []

for _, row in filtered.iterrows():
    try:
        date_obj = pd.to_datetime(row["date"]).date()

        if period_start <= date_obj <= period_end:
            item = {
                "date": date_obj.strftime("%Y-%m-%d"),
                "symbol": f'{row["code"]}.T',
                "name_ja": row["name_ja"],
                "name_en": row["name_en"],
                "market": row["market_ja"],
                "industry": row["industry_ja"],
                "fiscal_year_end": str(row["fiscal_year_end"]),
                "fiscal_period": row["fiscal_period"]
            }

            all_data.append(item)
    except:
        continue

# =====================
# 重複除去
# =====================
seen = set()
unique = []

for item in all_data:
    key = (item["symbol"], item["date"])

    if key not in seen:
        seen.add(key)
        unique.append(item)

# 日付順
unique.sort(key=lambda x: x["date"])

# =====================
# JSON保存
# =====================
with open(
    "earnings_data_jp.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        unique,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"\n✅ 保存完了: {len(unique)} 件")

# HTMLの生成
html = """<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Japan Earnings Calendar</title>
<style>
* {
    box-sizing: border-box;
}
html, body {
    touch-action: manipulation;
}
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #ffffff;
    margin: 0;
    padding: 0;
}
header {
    background-color: #31343C;
    color: white;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.header-left {
    display: flex;
    align-items: center;
    gap: 12px;
}
.header-icon {
    width: 40px;
    height: 40px;
    object-fit: contain;
}
.header-logo-text {
    font-size: 1.2em;
    font-weight: 600;
    color: white;
}
.header-content {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}
.header-title {
    font-size: 1.8em;
    font-weight: 600;
    color: white;
    margin: 0;
}
.header-date {
    font-size: 1.0em;
    color: #ddd;
    margin-top: 4px;
}
@media (max-width: 768px) {
    .header-content {
        display: none;
    }
}
.controls {
    background-color: white;
    padding: 16px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
    position: sticky;
    top: 0;
    z-index: 999;
}
.mode-toggle {
    display: flex;
    gap: 10px;
}
.mode-btn {
    padding: 10px 20px;
    border: 2px solid #31343C;
    background-color: white;
    color: #31343C;
    border-radius: 8px;
    cursor: pointer;
    font-size: 16px;
    font-weight: 600;
    transition: all 0.3s;
}
.mode-btn.active {
    background-color: #31343C;
    color: white;
}
.week-nav {
    display: none;
    flex-direction: column;
    align-items: center;
    gap: 10px;
}
.week-nav.active {
    display: flex;
}
.week-controls {
    display: flex;
    align-items: center;
    gap: 10px;
}
.nav-btn {
    width: 40px;
    height: 30px;
    border: none;
    background-color: #f0f0f0;
    border-radius: 8px;
    cursor: pointer;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;
    color: #333;
}
.nav-btn:hover:not(:disabled) {
    background-color: #31343C;
    color: white;
    transform: scale(1.1);
}
.nav-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
}
.week-label {
    font-weight: 600;
    font-size: 15px;
    color: #333;
    min-width: 200px;
    text-align: center;
}
.week-indicators {
    display: flex;
    gap: 8px;
}
.week-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #ddd;
    cursor: pointer;
    transition: all 0.3s;
}
.week-dot.active {
    background-color: #31343C;
    transform: scale(1.3);
}
.search-box {
    display: flex;
    width: 100%;
}
.search-box input {
    width: 100%;
    max-width: 400px;
    padding: 10px 16px;
    border: 2px solid #ddd;
    border-radius: 8px;
    font-size: 16px;
}
.search-box input:focus {
    outline: none;
    border-color: #31343C;
}
.container {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    padding: 20px;
}
.week-row {
    display: contents;
}
@media (max-width: 768px) {
    .container {
        display: block;
        overflow-x: auto;
        scroll-snap-type: x mandatory;
        -webkit-overflow-scrolling: touch;
        padding: 12px;
        scrollbar-width: thin;
        scrollbar-color: #31343C #f0f0f0;
    }
    .container::-webkit-scrollbar {
        height: 6px;
    }
    .container::-webkit-scrollbar-track {
        background: #f0f0f0;
        border-radius: 3px;
    }
    .container::-webkit-scrollbar-thumb {
        background: #31343C;
        border-radius: 3px;
    }
    .week-row {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
    }
    .day {
        min-width: 280px;
        flex-shrink: 0;
        scroll-snap-align: start;
    }
}
.day {
    background-color: rgba(255, 255, 255, 0.897);
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 10px;
    min-height: 150px;
    display: flex;
    flex-direction: column;
}
.day.today {
    border: 3px solid #4CAF50;
    box-shadow: 0 4px 10px rgba(76, 175, 80, 0.3);
    background-color: #f0fff0;
}
.date {
    font-weight: 600;
    margin-bottom: 8px;
    color: #333;
    text-align: left;
}
.day.today .date {
    color: #4CAF50;
    font-size: 1.2em;
}
.logos {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}
.logo-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 90px;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    background-color: #fff;
    padding: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    transition: all 0.3s;
}
.logo-card.hidden {
    display: none;
}
.logo-card img {
    width: 56px;
    height: 56px;
    object-fit: contain;
    margin-bottom: 6px;
    border-radius: 10%;
}
.symbol {
    font-size: 14px;
    font-weight: 600;
    color: #333;
}
.no-earnings {
    font-size: 13px;
    color: #aaa;
    margin-top: 20px;
    text-align: center;
}
.more-count {
    margin-top: 8px;
    text-align: center;
    font-size: 12px;
    color: #666;
    font-weight: 600;
}
footer {
    text-align: center;
    font-size: 12px;
    color: #888;
    margin: 20px;
}
@media (max-width: 768px) {
    header {
        flex-direction: column;
        gap: 12px;
    }
    .header-left {
        width: 100%;
        justify-content: flex-start;
    }
    .header-content {
        position: static;
        transform: none;
    }
    .header-icon {
        width: 32px;
        height: 32px;
    }
    .header-logo-text {
        font-size: 1.0em;
    }
    .header-title {
        font-size: 1.2em;
    }
    .header-title.hidden {
        display: none;
    }
    .header-left {
        display: none;
    }
    .header-date {
        font-size: 0.9em;
    }
    .day {
        min-height: 120px;
        padding: 8px;
    }
    .logos {
        grid-template-columns: repeat(3, 1fr);
        gap: 6px;
    }
    .logo-card {
        height: 70px;
    }
    .logo-card img {
        width: 40px;
        height: 40px;
    }
    .symbol {
        font-size: 12px;
    }
    .mode-btn {
        padding: 8px 16px;
        font-size: 14px;
    }
    .week-label {
        min-width: 180px;
        font-size: 14px;
    }
}
@media (max-width: 480px) {
    .day {
        min-width: 260px;
    }
    .week-label {
        min-width: 160px;
        font-size: 13px;
    }
}
.weekday-header {
    display: contents;
}
.weekday-cell {
    background-color: #31343C;
    color: white;
    padding: 4px;
    text-align: center;
    font-weight: 600;
    font-size: 16px;
}
@media (max-width: 768px) {
    .weekday-header {
        display: flex;
        gap: 8px;
        margin-bottom: 8px;
    }
    .weekday-cell {
        min-width: 280px;
        flex-shrink: 0;
        font-size: 14px;
        padding: 8px 4px;
        text-align: center;
    }
}
@media (max-width: 480px) {
    .weekday-cell {
        min-width: 260px;
    }
}
.logo-card.favorite {
    border: 2px solid #f0a500;
    background-color: #fffbf0;
    box-shadow: 0 2px 8px rgba(240, 165, 0, 0.35);
}
.logo-card.favorite .symbol {
    color: #b87800;
    font-weight: 700;
}
.top-controls-row {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}
.country-tabs {
    display: flex;
    gap: 8px;
}
.country-tabs {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 15px;
    font-weight: 600;
}
.country-link {
    color: #666;
    cursor: pointer;
    transition: color 0.2s;
    letter-spacing: 0.5px;
}
.country-link:hover {
    color: #31343C;
}
.country-link.active {
    color: #31343C;
}
.country-divider {
    color: #bbb;
}
.country-link.active {
    color: #31343C;
    border-bottom: 2px solid #31343C;
    padding-bottom: 2px;
}

</style>
</head>
<body>
<header>
    <div class="header-left">
        <img src="assets/icon.png" alt="Market Time Zen" class="header-icon">
        <span class="header-logo-text">Market Time Zen</span>
    </div>
    <div class="header-content">
        <div class="header-title">Japan Earnings Calendar</div>
        <div class="header-date">""" + datetime.now().strftime('%B %d, %Y') + """</div>
    </div>
</header>

<div class="controls">
    <div class="top-controls-row">
        <div class="mode-toggle">
            <button class="mode-btn active"
                onclick="switchMode('monthly')">
                Monthly
            </button>

            <button class="mode-btn"
                onclick="switchMode('weekly')">
                Weekly
            </button>
        </div>
    <div class="country-tabs">

        <span class="country-link"
            onclick="window.location.href='index.html'">
            New York
        </span>

        <span class="country-divider">|</span>

        <span class="country-link active"
            onclick="window.location.href='japan.html'">
            Tokyo
        </span>

    </div>
    </div>

    <div class="week-nav" id="weekNav">
        <div class="week-controls">
            <button class="nav-btn" id="prevWeek" onclick="changeWeek(-1)">‹</button>
            <span class="week-label" id="weekLabel">Week 1</span>
            <button class="nav-btn" id="nextWeek" onclick="changeWeek(1)">›</button>
        </div>
        <div class="week-indicators" id="weekDots"></div>
    </div>

    <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search by symbol (e.g., 7203, SONY)..." oninput="searchSymbols()">
    </div>
</div>

<div class="container" id="calendar"></div>

<footer>Last updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """</footer>

<script>
let earningsData = [];
let currentMode = 'monthly';
let currentWeek = 0;
let weeks = """ + json.dumps([[d.strftime("%Y-%m-%d") for d in week] for week in weeks]) + """;
let targetSymbols = """ + json.dumps(TARGET_JP) + """;

function getFavorites() {
    const params = new URLSearchParams(window.location.search);
    const fav = params.get('favorites');
    return fav ? fav.split(',').map(s => s.trim().toUpperCase()).filter(Boolean) : [];
}
const favorites = getFavorites();

function updateHeaderHeight() {
    const h = document.querySelector('header').offsetHeight;
    document.documentElement.style.setProperty('--header-height', h + 'px');
}

fetch('earnings_data_jp.json')
    .then(res => res.json())
    .then(data => {
        earningsData = data;
        currentWeek = findCurrentWeek();
        renderCalendar();
        scrollToCurrentWeek();
    });

function scrollToCurrentWeek() {
    if (currentMode !== 'monthly') return;
    const allWeekRows = document.querySelectorAll('.week-row-wrapper');
    if (allWeekRows.length === 0) return;
    const targetRow = allWeekRows[currentWeek] || allWeekRows[0];
    if (!targetRow) return;
    const headerEl = document.querySelector('header');
    const controlsEl = document.querySelector('.controls');
    const offset = (headerEl ? headerEl.offsetHeight : 0) + (controlsEl ? controlsEl.offsetHeight : 0);
    const top = targetRow.getBoundingClientRect().top + window.scrollY - offset - 8;
    window.scrollTo({ top: Math.max(0, top), behavior: 'instant' });
}

function findCurrentWeek() {
    const today = new Date().toISOString().split('T')[0];
    const todayDay = new Date().getDay();
    for (let i = 0; i < weeks.length; i++) {
        const weekDates = weeks[i];
        if (todayDay >= 1 && todayDay <= 5) {
            if (weekDates.includes(today)) return i;
        } else {
            if (weekDates[0] > today) return i;
        }
    }
    return 0;
}

function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.mode-btn').forEach(btn => {
        if ((mode === 'monthly' && btn.textContent === 'Monthly') ||
            (mode === 'weekly' && btn.textContent === 'Weekly')) {
            btn.classList.add('active');
        }
    });
    if (mode === 'weekly') {
        document.getElementById('weekNav').classList.add('active');
        renderWeekDots();
    } else {
        document.getElementById('weekNav').classList.remove('active');
    }
    renderCalendar();
}

function renderWeekDots() {
    const dotsContainer = document.getElementById('weekDots');
    dotsContainer.innerHTML = '';
    weeks.forEach((week, idx) => {
        const dot = document.createElement('div');
        dot.className = 'week-dot' + (idx === currentWeek ? ' active' : '');
        dot.onclick = () => {
            currentWeek = idx;
            renderCalendar();
        };
        dotsContainer.appendChild(dot);
    });
}

function changeWeek(delta) {
    currentWeek = Math.max(0, Math.min(weeks.length - 1, currentWeek + delta));
    renderCalendar();
}

function renderCalendar() {
    const calendar = document.getElementById('calendar');
    calendar.innerHTML = '';

    const headerRow = document.createElement('div');
    headerRow.className = 'weekday-header';
    ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'].forEach(day => {
        const cell = document.createElement('div');
        cell.className = 'weekday-cell';
        cell.textContent = day;
        headerRow.appendChild(cell);
    });
    calendar.appendChild(headerRow);

    if (currentMode === 'monthly') {
        weeks.forEach(weekDates => {
            const hasEarnings = weekDates.some(dateStr => {
                return earningsData.some(e => e.date === dateStr);
            });

            if (!hasEarnings) return;

            const weekRow = document.createElement('div');
            weekRow.className = 'week-row week-row-wrapper';
            weekDates.forEach(dateStr => {
                weekRow.appendChild(renderDay(dateStr));
            });
            calendar.appendChild(weekRow);
        });
    } else {
        const weekDates = weeks[currentWeek];
        const hasEarnings = weekDates.some(dateStr => {
            return earningsData.some(e => e.date === dateStr);
        });

        document.getElementById('weekLabel').textContent =
            `Week ${currentWeek + 1}: ${formatDateRange(weeks[currentWeek])}`;
        document.getElementById('prevWeek').disabled = currentWeek === 0;
        document.getElementById('nextWeek').disabled = currentWeek === weeks.length - 1;

        document.querySelectorAll('.week-dot').forEach((dot, idx) => {
            dot.classList.toggle('active', idx === currentWeek);
        });

        if (hasEarnings) {
            const weekRow = document.createElement('div');
            weekRow.className = 'week-row';
            weekDates.forEach(dateStr => {
                weekRow.appendChild(renderDay(dateStr));
            });
            calendar.appendChild(weekRow);
        } else {
            const noDataDiv = document.createElement('div');
            noDataDiv.style.width = '100%';
            noDataDiv.style.textAlign = 'center';
            noDataDiv.style.padding = '40px';
            noDataDiv.style.color = '#888';
            noDataDiv.style.fontSize = '16px';
            noDataDiv.textContent = 'No earnings data for this week';
            calendar.appendChild(noDataDiv);
        }
    }
}

function renderDay(dateStr) {
    const today = new Date().toISOString().split('T')[0];

    const earnings = earningsData.filter(e =>
        e.date === dateStr && targetSymbols.includes(e.symbol)
    ).sort((a, b) => {
        const aIdx = targetSymbols.indexOf(a.symbol);
        const bIdx = targetSymbols.indexOf(b.symbol);
        if (aIdx === -1 && bIdx === -1) return a.symbol.localeCompare(b.symbol);
        if (aIdx === -1) return 1;
        if (bIdx === -1) return -1;
        return aIdx - bIdx;
    });

    const dayDiv = document.createElement('div');
    dayDiv.className = 'day';
    if (dateStr === today) dayDiv.classList.add('today');

    if (currentMode === 'monthly') {
        dayDiv.style.cursor = 'pointer';
        dayDiv.onclick = () => {
            const weekIndex = weeks.findIndex(week => week.includes(dateStr));
            if (weekIndex !== -1) {
                currentWeek = weekIndex;
                switchMode('weekly');
            }
        };
    }

    const [year, month, day] = dateStr.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const dateDiv = document.createElement('div');
    dateDiv.className = 'date';
    dateDiv.textContent = `${monthNames[parseInt(month) - 1]}, ${parseInt(day)}`;
    dayDiv.appendChild(dateDiv);

    if (earnings.length > 0) {
        const logosDiv = document.createElement('div');
        logosDiv.className = 'logos';

        const displayEarnings = currentMode === 'monthly' ? earnings.slice(0, 9) : earnings;

        displayEarnings.forEach(e => {
            const card = document.createElement('div');
            card.className = 'logo-card';

            if (favorites.includes(e.symbol)) {
                card.classList.add('favorite');
            }

            card.dataset.symbol = e.symbol;

            card.addEventListener('click', (ev) => {
                ev.stopPropagation();
                window.webkit.messageHandlers.favoriteHandler.postMessage({
                    symbol: e.symbol
                });
            });

            const logoPath = '""" + ASSETS_DIR + """/' + e.symbol + '.png';

            const img = document.createElement('img');
            img.src = logoPath;
            img.alt = e.symbol;
            img.title = e.symbol;
            img.onerror = () => img.style.display = 'none';

            const symbolDiv = document.createElement('div');
            symbolDiv.className = 'symbol';
            symbolDiv.textContent = e.symbol;

            card.appendChild(img);
            card.appendChild(symbolDiv);

            logosDiv.appendChild(card);
        });

        dayDiv.appendChild(logosDiv);

        if (currentMode === 'monthly' && earnings.length > 9) {
            const moreDiv = document.createElement('div');
            moreDiv.className = 'more-count';
            moreDiv.textContent = `+${earnings.length - 9} more`;
            dayDiv.appendChild(moreDiv);
        }
    } else {
        const noEarnings = document.createElement('div');
        noEarnings.className = 'no-earnings';
        noEarnings.textContent = 'No Earnings';
        dayDiv.appendChild(noEarnings);
    }

    return dayDiv;
}

document.addEventListener('DOMContentLoaded', updateHeaderHeight);
window.addEventListener('resize', updateHeaderHeight);

function formatDateRange(dates) {
    if (!dates || dates.length === 0) return '';
    const start = new Date(dates[0] + 'T00:00:00');
    const end = new Date(dates[dates.length - 1] + 'T00:00:00');
    return `${start.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${end.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
}

function searchSymbols() {
    const query = document.getElementById('searchInput').value.toUpperCase().trim();
    const cards = document.querySelectorAll('.logo-card');
    if (!query) {
        cards.forEach(card => card.classList.remove('hidden'));
    } else {
        cards.forEach(card => {
            const symbol = card.dataset.symbol;
            if (symbol.includes(query)) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });
    }
}
</script>
</body>
</html>
"""

with open("japan.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Japan HTML calendar generated successfully.")
