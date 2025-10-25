import os
import json
import pandas as pd
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv("FINNHUB_API_KEY", "YOUR_API_KEY")

# 現在の日付から期間を自動設定
today = datetime.now()
# 開始日：今月の1日
FROM_DATE = today.replace(day=1).strftime("%Y-%m-%d")
# 終了日：翌月末（今月末 + 翌月分も含める）
next_month = today.replace(day=28) + timedelta(days=4)
end_of_next_month = next_month.replace(day=1) + timedelta(days=32)
TO_DATE = (end_of_next_month.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")

ASSETS_DIR = "assets/logos"

# Monthly表示用（主要銘柄のみ）
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
]

# Weekly表示用（より多くの銘柄）
TARGET_WEEKLY = [
    # Monthly銘柄を全て含む
    *TARGET_MONTHLY,
    
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
]

# 重複を削除
TARGET_WEEKLY = list(dict.fromkeys(TARGET_WEEKLY))

print(f"📊 TARGET_MONTHLY: {len(TARGET_MONTHLY)} symbols")
print(f"📊 TARGET_WEEKLY: {len(TARGET_WEEKLY)} symbols")

# APIからデータ取得
url = f"https://finnhub.io/api/v1/calendar/earnings?from={FROM_DATE}&to={TO_DATE}&token={API_KEY}"
resp = requests.get(url)
data = resp.json().get("earningsCalendar", [])
df = pd.DataFrame(data)
# NaNを0に置き換え
df = df.fillna(0)

# JSONファイルの生成（Weekly用の全データ）
weekly_data = df[df["symbol"].isin(TARGET_WEEKLY)].to_dict(orient="records")
with open("earnings_data.json", "w", encoding="utf-8") as f:
    json.dump(weekly_data, f, ensure_ascii=False, indent=2)
print(f"✅ earnings_data.json generated ({len(weekly_data)} records)")

# 月～金のみの日付リストを生成
start_date = datetime.strptime(FROM_DATE, "%Y-%m-%d")
end_date = datetime.strptime(TO_DATE, "%Y-%m-%d")
weekday_dates = []
current = start_date
while current <= end_date:
    if current.weekday() < 5:  # 0-4 = Mon-Fri
        weekday_dates.append(current)
    current += timedelta(days=1)

# 週ごとに分割（月曜から金曜までの5日間）
weeks = []
current_week = []
for date in weekday_dates:
    if date.weekday() == 0 and current_week:  # 月曜日で新しい週
        weeks.append(current_week)
        current_week = []
    current_week.append(date)
if current_week:
    weeks.append(current_week)

print(f"📅 Total weeks: {len(weeks)}")

# HTMLの生成
html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Earnings Calendar - October 2025</title>
<style>
* {
    box-sizing: border-box;
}
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #f6f7f9;
    margin: 0;
    padding: 0;
}
header {
    background-color: #31343C;
    color: white;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 12px;
}
.header-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}
.header-icon {
    width: 40px;
    height: 40px;
    object-fit: contain;
    margin-bottom: 8px;
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
.controls {
    background-color: white;
    padding: 16px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
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
    height: 40px;
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
.day {
    background-color: white;
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
    text-align: center;
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
footer {
    text-align: center;
    font-size: 12px;
    color: #888;
    margin: 20px;
}

@media (max-width: 768px) {
    .header-icon {
        width: 32px;
        height: 32px;
        margin-bottom: 6px;
    }
    .header-title {
        font-size: 1.2em;
    }
    .header-date {
        font-size: 0.9em;
    }
    .container {
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        padding: 12px;
    }
    .day {
        min-height: 120px;
        padding: 8px;
    }
    .logos {
        grid-template-columns: repeat(2, 1fr);
        gap: 6px;
    }
    .logo-card {
        height: 70px;
    }
    .logo-card img {
        width: 40px;
        height: 40px;
    }
    .mode-btn {
        padding: 8px 16px;
        font-size: 14px;
    }
}

@media (max-width: 480px) {
    .container {
        grid-template-columns: 1fr;
    }
}
</style>
</head>
<body>
<header>
    <div class="header-content">
        <img src="assets/icon.png" alt="Market Time Zen" class="header-icon">
        <div class="header-title">Earnings Calendar</div>
        <div class="header-date">""" + datetime.now().strftime('%B %d, %Y') + """</div>
    </div>
</header>

<div class="controls">
    <div class="mode-toggle">
        <button class="mode-btn active" onclick="switchMode('monthly')">Monthly</button>
        <button class="mode-btn" onclick="switchMode('weekly')">Weekly</button>
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
        <input type="text" id="searchInput" placeholder="Search by symbol (e.g., AAPL, TSLA)..." oninput="searchSymbols()">
    </div>
</div>

<div class="container" id="calendar"></div>

<footer>Last updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M') + """</footer>

<script>
let earningsData = [];
let currentMode = 'monthly';
let currentWeek = 0;
let weeks = """ + json.dumps([[d.strftime("%Y-%m-%d") for d in week] for week in weeks]) + """;
let targetMonthly = """ + json.dumps(TARGET_MONTHLY) + """;
let targetWeekly = """ + json.dumps(TARGET_WEEKLY) + """;
let allWeekdayDates = """ + json.dumps([d.strftime("%Y-%m-%d") for d in weekday_dates]) + """;

// データ読み込み
fetch('earnings_data.json')
    .then(res => res.json())
    .then(data => {
        earningsData = data;
        renderCalendar();
    });

function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.mode-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
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
    
    let targetSymbols = currentMode === 'monthly' ? targetMonthly : targetWeekly;
    
    // Monthlyモードの場合、週ごとに処理
    if (currentMode === 'monthly') {
        weeks.forEach(weekDates => {
            // この週に決算データがあるかチェック
            const hasEarnings = weekDates.some(dateStr => {
                const earnings = earningsData.filter(e => 
                    e.date === dateStr && targetSymbols.includes(e.symbol)
                );
                return earnings.length > 0;
            });
            
            // 決算データがない週はスキップ
            if (!hasEarnings) {
                return;
            }
            
            // この週の日付を表示
            weekDates.forEach(dateStr => {
                renderDay(dateStr, targetSymbols, calendar);
            });
        });
    } else {
        // Weeklyモードの場合も週ごとにチェック
        const weekDates = weeks[currentWeek];
        
        // この週に決算データがあるかチェック
        const hasEarnings = weekDates.some(dateStr => {
            const earnings = earningsData.filter(e => 
                e.date === dateStr && targetSymbols.includes(e.symbol)
            );
            return earnings.length > 0;
        });
        
        // 週ナビゲーションの更新
        document.getElementById('weekLabel').textContent = 
            `Week ${currentWeek + 1}: ${formatDateRange(weeks[currentWeek])}`;
        document.getElementById('prevWeek').disabled = currentWeek === 0;
        document.getElementById('nextWeek').disabled = currentWeek === weeks.length - 1;
        
        document.querySelectorAll('.week-dot').forEach((dot, idx) => {
            dot.classList.toggle('active', idx === currentWeek);
        });
        
        // 決算データがある場合のみ日付を表示
        if (hasEarnings) {
            weekDates.forEach(dateStr => {
                renderDay(dateStr, targetSymbols, calendar);
            });
        } else {
            // 決算データがない場合のメッセージ
            const noDataDiv = document.createElement('div');
            noDataDiv.style.gridColumn = '1 / -1';
            noDataDiv.style.textAlign = 'center';
            noDataDiv.style.padding = '40px';
            noDataDiv.style.color = '#888';
            noDataDiv.style.fontSize = '16px';
            noDataDiv.textContent = 'No earnings data for this week';
            calendar.appendChild(noDataDiv);
        }
    }
}

function renderDay(dateStr, targetSymbols, calendar) {
    const today = new Date().toISOString().split('T')[0];
    
    const earnings = earningsData.filter(e => 
        e.date === dateStr && targetSymbols.includes(e.symbol)
    );
    
    const dayDiv = document.createElement('div');
    dayDiv.className = 'day';
    if (dateStr === today) {
        dayDiv.classList.add('today');
    }
    
    const date = new Date(dateStr + 'T00:00:00');
    const dateDiv = document.createElement('div');
    dateDiv.className = 'date';
    dateDiv.textContent = date.toLocaleDateString('en-US', { 
        month: 'short', day: 'numeric', weekday: 'short' 
    });
    dayDiv.appendChild(dateDiv);
    
    if (earnings.length > 0) {
        const logosDiv = document.createElement('div');
        logosDiv.className = 'logos';
        
        // Monthlyモードでは最大9件まで表示
        const displayEarnings = currentMode === 'monthly' ? earnings.slice(0, 9) : earnings;
        
        displayEarnings.forEach(e => {
            const card = document.createElement('div');
            card.className = 'logo-card';
            card.dataset.symbol = e.symbol;
            
            const logoPath = `${""" + json.dumps(ASSETS_DIR) + """}/${e.symbol}.png`;
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
    } else {
        const noEarnings = document.createElement('div');
        noEarnings.className = 'no-earnings';
        noEarnings.textContent = 'No Earnings';
        dayDiv.appendChild(noEarnings);
    }
    
    calendar.appendChild(dayDiv);
}

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
        // 検索クエリが空の場合はすべて表示
        cards.forEach(card => card.classList.remove('hidden'));
    } else {
        // 検索クエリがある場合は、マッチしないものを非表示
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

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ HTML calendar generated successfully.")