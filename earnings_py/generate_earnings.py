import json
import time
import requests
from datetime import datetime
from input.us_companies import TARGET_US

HEADERS = {
    "User-Agent": "MarketTimeZen contact@example.com"
}

METRIC_TAGS = {
    "revenue": [
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
    ],
    "netIncome": [
        "NetIncomeLoss",
        "ProfitLoss",
    ],
    "epsDiluted": [
        "EarningsPerShareDiluted",
    ],
    "grossProfit": [
        "GrossProfit",
    ],
    "costOfRevenue": [
        "CostOfRevenue",
        "CostOfGoodsAndServicesSold",
    ],
    "operatingCashFlow": [
        "NetCashProvidedByUsedInOperatingActivities",
    ],
}

METRIC_UNITS = {
    "revenue": "USD",
    "netIncome": "USD",
    "epsDiluted": "USD/shares",
    "grossProfit": "USD",
    "costOfRevenue": "USD",
    "operatingCashFlow": "USD",
}


def extract_periods(items):
    result = {}

    for item in items:

        form = item.get("form")
        fy = item.get("fy")
        fp = item.get("fp")

        if fy is None:
            continue

        if form == "10-Q":
            if fp not in ["Q1", "Q2", "Q3"]:
                continue
        elif form == "10-K":
            if fp != "FY":
                continue
        else:
            continue

        start = item.get("start")
        end = item.get("end")

        if not start or not end:
            continue

        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        days = (end_date - start_date).days

        if form == "10-Q" and not (80 <= days <= 100):
            continue

        if form == "10-K" and days < 300:
            continue

        key = f"FY{fy}{fp}"

        existing = result.get(key)

        if existing is None:
            result[key] = dict(item)
            result[key]["duration"] = days
            continue

        existing_end = datetime.strptime(existing["end"], "%Y-%m-%d")
        existing_filed = datetime.strptime(existing["filed"], "%Y-%m-%d")
        filed = datetime.strptime(item["filed"], "%Y-%m-%d")

        if end_date > existing_end or (
            end_date == existing_end and filed > existing_filed
        ):
            result[key] = dict(item)
            result[key]["duration"] = days

    return result


def extract_periods_ytd(items):
    """CFのYTD累計値を取得する（日数チェックなし）"""
    result = {}

    for item in items:

        form = item.get("form")
        fy = item.get("fy")
        fp = item.get("fp")

        if fy is None:
            continue

        if form == "10-Q":
            if fp not in ["Q1", "Q2", "Q3"]:
                continue
        elif form == "10-K":
            if fp != "FY":
                continue
        else:
            continue

        start = item.get("start")
        end = item.get("end")

        if not start or not end:
            continue

        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        days = (end_date - start_date).days

        if form == "10-K" and days < 300:
            continue

        key = f"FY{fy}{fp}"

        existing = result.get(key)

        if existing is None:
            result[key] = dict(item)
            result[key]["duration"] = days
            continue

        existing_end = datetime.strptime(existing["end"], "%Y-%m-%d")
        existing_filed = datetime.strptime(existing["filed"], "%Y-%m-%d")
        filed = datetime.strptime(item["filed"], "%Y-%m-%d")

        if end_date > existing_end or (
            end_date == existing_end and filed > existing_filed
        ):
            result[key] = dict(item)
            result[key]["duration"] = days

    return result


def generate_q4(metric):

    result = dict(metric)

    fiscal_years = sorted(
        {
            value["fy"]
            for value in metric.values()
            if value.get("fp") == "FY"
        },
        reverse=True,
    )

    for fy in fiscal_years:

        fy_key = f"FY{fy}FY"
        q1_key = f"FY{fy}Q1"
        q2_key = f"FY{fy}Q2"
        q3_key = f"FY{fy}Q3"

        if not all(
            key in metric
            for key in [fy_key, q1_key, q2_key, q3_key]
        ):
            continue

        q4_value = (
            metric[fy_key]["val"]
            - metric[q1_key]["val"]
            - metric[q2_key]["val"]
            - metric[q3_key]["val"]
        )

        result[f"FY{fy}Q4"] = {
            "val": q4_value,
            "fy": fy,
            "fp": "Q4",
            "form": "10-K",
            "start": metric[q3_key]["end"],
            "end": metric[fy_key]["end"],
            "filed": metric[fy_key]["filed"],
            "accn": metric[fy_key]["accn"],
        }

    return result


def generate_quarterly_from_ytd(ytd):
    """YTD累計から単一四半期の値を逆算する"""
    result = {}

    fiscal_years = sorted(
        {v["fy"] for v in ytd.values()},
        reverse=True,
    )

    for fy in fiscal_years:
        q1_key = f"FY{fy}Q1"
        q2_key = f"FY{fy}Q2"
        q3_key = f"FY{fy}Q3"
        fy_key = f"FY{fy}FY"

        # Q1はYTD = 単一四半期なのでそのまま使う
        if q1_key in ytd:
            result[q1_key] = dict(ytd[q1_key])

        # Q2 = YTD Q2 - Q1
        if q2_key in ytd and q1_key in ytd:
            result[q2_key] = dict(ytd[q2_key])
            result[q2_key]["val"] = ytd[q2_key]["val"] - ytd[q1_key]["val"]

        # Q3 = YTD Q3 - YTD Q2
        if q3_key in ytd and q2_key in ytd:
            result[q3_key] = dict(ytd[q3_key])
            result[q3_key]["val"] = ytd[q3_key]["val"] - ytd[q2_key]["val"]

        # Q4 = 年間 - YTD Q3
        if fy_key in ytd and q3_key in ytd:
            result[f"FY{fy}Q4"] = {
                "val": ytd[fy_key]["val"] - ytd[q3_key]["val"],
                "fy": fy,
                "fp": "Q4",
                "form": "10-K",
                "start": ytd[q3_key]["end"],
                "end": ytd[fy_key]["end"],
                "filed": ytd[fy_key]["filed"],
                "accn": ytd[fy_key]["accn"],
            }

    return result


def collect_metric_items(us_gaap, metric_name):
    items = []
    unit = METRIC_UNITS[metric_name]

    for tag in METRIC_TAGS[metric_name]:
        fact = us_gaap.get(tag)
        if not fact:
            continue

        unit_items = fact.get("units", {}).get(unit)
        if unit_items:
            items.extend(unit_items)

    return items


def build_earnings(cik, company_name=None):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
    response = requests.get(url, headers=HEADERS, timeout=60)
    response.raise_for_status()

    data = response.json()
    us_gaap = data["facts"]["us-gaap"]

    revenue = generate_q4(
        extract_periods(
            collect_metric_items(us_gaap, "revenue")
        )
    )

    revenue = {
        k: v
        for k, v in revenue.items()
        if v["fp"] != "FY"
    }

    net_income = generate_q4(
        extract_periods(
            collect_metric_items(us_gaap, "netIncome")
        )
    )

    eps = generate_q4(
        extract_periods(
            collect_metric_items(us_gaap, "epsDiluted")
        )
    )

    gross_profit = generate_q4(
        extract_periods(
            collect_metric_items(us_gaap, "grossProfit")
        )
    )

    cost_of_revenue = generate_q4(
        extract_periods(
            collect_metric_items(us_gaap, "costOfRevenue")
        )
    )

    operating_cash_flow = generate_quarterly_from_ytd(
        extract_periods_ytd(
            collect_metric_items(us_gaap, "operatingCashFlow")
        )
    )

    quarters = sorted(
        [
            q for q in (
                set(revenue.keys())
                & set(net_income.keys())
                & set(eps.keys())
            )
            if q.endswith(("Q1", "Q2", "Q3", "Q4"))
        ],
        reverse=True,
    )[:40]

    output = {}

    if company_name:
        output["companyName"] = company_name

    for quarter in quarters:
        fiscal_quarter = (
            4
            if revenue[quarter]["fp"] == "Q4"
            else int(revenue[quarter]["fp"].replace("Q", ""))
        )

        rev_val = revenue[quarter]["val"]

        # GrossProfitが取得できない場合はRevenue - CostOfRevenueで計算
        if quarter in gross_profit:
            gp_val = gross_profit[quarter]["val"]
        elif quarter in cost_of_revenue:
            gp_val = rev_val - cost_of_revenue[quarter]["val"]
        else:
            gp_val = None

        output[quarter] = {
            "revenue": rev_val,
            "netIncome": net_income[quarter]["val"],
            "epsDiluted": round(eps[quarter]["val"], 2),
            "grossProfit": gp_val,
            "grossMargin": round(gp_val / rev_val, 4) if gp_val and rev_val else None,
            "operatingCashFlow": operating_cash_flow[quarter]["val"] if quarter in operating_cash_flow else None,
            "fiscalYear": revenue[quarter]["fy"],
            "fiscalQuarter": fiscal_quarter,
            "form": revenue[quarter]["form"],
            "startDate": revenue[quarter]["start"],
            "endDate": revenue[quarter]["end"],
            "filedDate": revenue[quarter]["filed"],
            "accessionNumber": revenue[quarter]["accn"],
        }

    return output


def write_earnings_file(symbol, earnings):
    filename = f"output_json/earnings/{symbol.lower()}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(earnings, f, indent=2)

    return filename


def main():
    for index, company in enumerate(TARGET_US):
        symbol = company["symbol"]
        cik = company["cik"]

        print(f"[{index + 1}/{len(TARGET_US)}] Downloading {symbol} ({cik})...")

        try:
            earnings = build_earnings(cik)
        except requests.RequestException as error:
            print(f"Skipped {symbol}: {error}")
            continue

        filename = write_earnings_file(symbol, earnings)
        print(f"Wrote {filename}: {len(earnings)} quarters")

        if index < len(TARGET_US) - 1:
            time.sleep(0.2)


if __name__ == "__main__":
    main()