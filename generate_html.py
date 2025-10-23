import os
import pandas as pd
import requests
from datetime import datetime, timedelta

API_KEY = os.getenv("FINNHUB_API_KEY", "YOUR_API_KEY")
FROM_DATE = "2025-10-01"
TO_DATE = "2025-10-31"
ASSETS_DIR = "assets/logos"

TARGET = [
   "FAST", "BLK", "JPM", "C", "WFC", "JNJ", "ERIC", "ACI",
    "ASML", "UAL", "BAC", "MS", "SYF", "PGNY", "LII",
    "TSM", "BNY", "IBKR", "INFY", "SCHW", "KEY", "CSX", "TRV", "MTB",
    "SLB", "ALLY", "AXP", "HBAN", "ALV", "TFC", "RF",
    "CLF", "CCK", "AGNC", "WTFC", "RLI", "ZION", "BOKF",
    "NFLX", "VZ", "ISRG", "KO", "TXN", "RTX", "ELV",
    "TSLA", "IBM", "APH", "KMI", "GE", "VRT", "CTLT",
    "INTC", "AAL", "HON", "NEM", "ALK", "DOV", "ITW",
    "PG", "HCA", "GNTX", "GFF",
    "RMBS", "NUE", "WHR", "WM", "KDP", "NXP",
    "SOFI", "ENPH", "UPS", "BKNG", "HSBC", "PYPL", "GLW",
    "META", "MSFT", "GOOGL", "BA", "CMG", "CVS", "SNOW",
    "AAPL", "LLY", "MRK", "ABBV", "CBOE", "CLFD", "SENS",
    "CVX", "CNI", "LYB", "FET",
    "DUOL", "RDFN", "NVST", "EXAS", "PFE", "BP", "AMD", "ANET", "SPOT", "UPST", "CLOV",
    "UBS", "QCOM", "ARM", "MCD", "HUM",
    "COP", "OPEN", "NSC", "AZN", "SNDK",
    "NU", "EVLV", "SIGA", "VIA", "BALL", "KKR", "ENB", "WEN",
    "PANW", "AMAT", "CSCO", "DLO", "DIS"
]

url = f"https://finnhub.io/api/v1/calendar/earnings?from={FROM_DATE}&to={TO_DATE}&token={API_KEY}"
resp = requests.get(url)
data = resp.json().get("earningsCalendar", [])
df = pd.DataFrame(data)
df = df[df["symbol"].isin(TARGET)]

start_date = datetime.strptime(FROM_DATE, "%Y-%m-%d")
end_date = datetime.strptime(TO_DATE, "%Y-%m-%d")
all_dates = []
current = start_date
while current <= end_date:
    all_dates.append(current)
    current += timedelta(days=1)

html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Earnings Calendar (S&P 500 Highlights)</title>
<style>
body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #f6f7f9;
    margin: 0;
    padding: 0;
}
header {
    background-color: #31343C;
    color: white;
    text-align: center;
    padding: 16px;
    font-size: 1.8em;
    font-weight: 600;
}
.container {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 10px;
    padding: 20px;
}
.day {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    padding: 10px;
    min-height: 130px;
    display: flex;
    flex-direction: column;
    align-items: center;
}
.date {
    font-weight: 600;
    margin-bottom: 6px;
    color: #333;
}
.logos {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 10px;
}
.logo-card {
    display: flex;
    align-items: center;
    justify-content: flex-start;
    width: 110px;
    height: 50px;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    background-color: #fff;
    padding: 5px 8px;
    box-sizing: border-box;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.logo-card img {
    width: 30px;
    height: 30px;
    object-fit: contain;
    margin-right: 6px;
}
.symbol {
    font-size: 13px;
    font-weight: 600;
    color: #333;
    text-align: left;
}
footer {
    text-align: center;
    font-size: 12px;
    color: #888;
    margin: 20px;
}
</style>
</head>
<body>
<header>Earnings Calendar - October 2025</header>
<div class="container">
"""

for day in all_dates:
    date_str = day.strftime("%Y-%m-%d")
    group = df[df["date"] == date_str]

    html += f'<div class="day">'
    html += f'<div class="date">{day.strftime("%b %d (%a)")}</div>'

    if not group.empty:
        html += '<div class="logos">'
        for _, row in group.iterrows():
            symbol = row["symbol"]
            logo_path = f"{ASSETS_DIR}/{symbol}.png"
            html += '<div class="logo-card">'
            if os.path.exists(logo_path):
                html += f'<img src="{logo_path}" alt="{symbol}" title="{symbol}">'
            html += f'<div class="symbol">{symbol}</div>'
            html += '</div>'
        html += "</div>"
    else:
        html += '<div style="font-size:13px;color:#aaa;margin-top:20px;">No Earnings</div>'

    html += "</div>"

html += f"""
</div>
<footer>Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</footer>
</body></html>
"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ HTML calendar generated successfully.")
