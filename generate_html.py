import os
import requests
import pandas as pd
from datetime import datetime

API_KEY = os.getenv("FINNHUB_API_KEY", "YOUR_API_KEY")
FROM_DATE = "2025-10-01"
TO_DATE = "2025-10-31"

TOP10_SP500 = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "NVDA", "BRK.B", "TSLA", "LLY", "AVGO"
]

LOGO_URLS = {
    "AAPL": "https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg",
    "MSFT": "https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg",
    "AMZN": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg",
    "GOOGL": "https://upload.wikimedia.org/wikipedia/commons/2/2f/Google_2015_logo.svg",
    "META": "https://upload.wikimedia.org/wikipedia/commons/0/05/Meta_Platforms_Inc._logo.svg",
    "NVDA": "https://upload.wikimedia.org/wikipedia/en/2/21/Nvidia_logo.svg",
    "BRK.B": "https://upload.wikimedia.org/wikipedia/commons/8/80/Berkshire_Hathaway_logo.svg",
    "TSLA": "https://upload.wikimedia.org/wikipedia/commons/b/bd/Tesla_Motors.svg",
    "LLY": "https://upload.wikimedia.org/wikipedia/commons/e/ea/Eli_Lilly_and_Company_logo.svg",
    "AVGO": "https://upload.wikimedia.org/wikipedia/commons/5/5c/Broadcom_Logo.svg",
}

url = f"https://finnhub.io/api/v1/calendar/earnings?from={FROM_DATE}&to={TO_DATE}&token={API_KEY}"
resp = requests.get(url)
data = resp.json().get("earningsCalendar", [])
if not data:
    print("⚠️ No data returned from Finnhub API.")
    exit()

df = pd.DataFrame(data)
df = df[df["symbol"].isin(TOP10_SP500)]

html = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>決算カレンダー（S&P500トップ10）</title>
<style>
body { font-family: sans-serif; background-color: #f4f4f7; margin: 0; padding: 20px; }
h1 { text-align: center; margin-bottom: 20px; }
.calendar { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.day { background: #fff; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); padding: 8px; min-height: 160px;
       display: flex; flex-direction: column; align-items: center; }
.date { font-weight: bold; margin-bottom: 6px; }
.logos { display: flex; flex-wrap: wrap; justify-content: center; gap: 6px; }
.logos img { height: 28px; object-fit: contain; }
.info { font-size: 12px; color: #555; margin-top: 4px; }
</style>
</head><body>
<h1>決算カレンダー（S&P500 トップ10）</h1>
<div class="calendar">
"""

for date, group in df.groupby("date"):
    html += f'<div class="day"><div class="date">{date}</div><div class="logos">'
    for _, row in group.head(10).iterrows():
        symbol = row["symbol"]
        logo_url = LOGO_URLS.get(symbol, "")
        if logo_url:
            html += f'<img src="{logo_url}" alt="{symbol}" title="{symbol}">'
        else:
            html += f'<div style="font-size:14px;">{symbol}</div>'
    html += "</div>"
    for _, row in group.iterrows():
        if pd.notna(row["epsEstimate"]):
            html += f'<div class="info">・{row["symbol"]}: EPS予想 {row["epsEstimate"]}</div>'
    html += "</div>"

html += f"</div><p style='font-size:12px;color:#666;text-align:center;'>最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p></body></html>"

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ ロゴ付き index.html を生成しました。")
