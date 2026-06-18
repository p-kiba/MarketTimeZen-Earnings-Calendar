import json
import os
import requests

HEADERS = {
    "User-Agent": "MarketTimeZen contact@example.com"
}

INDEX_FILE = "earnings_py/input/earnings_index.json"


def load_index():
    """
    earnings_index.jsonを読み込む
    """

    if not os.path.exists(INDEX_FILE):
        return {}

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index_data):
    """
    earnings_index.jsonを書き込む
    """

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(
            index_data,
            f,
            indent=2,
            ensure_ascii=False,
        )


def get_latest_filing(cik):
    """
    最新の10-Qまたは10-Kを取得
    """

    cik = str(cik).zfill(10)

    url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    recent = data["filings"]["recent"]

    forms = recent["form"]
    accession_numbers = recent["accessionNumber"]
    filing_dates = recent["filingDate"]

    for form, accession, filing_date in zip(
        forms,
        accession_numbers,
        filing_dates,
    ):
        if form in ("10-Q", "10-K"):
            return {
                "form": form,
                "accessionNumber": accession,
                "filingDate": filing_date,
            }

    return None


def get_changed_companies(companies):
    """
    更新が必要な銘柄だけ返す
    """

    index_data = load_index()

    changed_companies = []

    for company in companies:

        symbol = company["symbol"]
        cik = company["cik"]
        name = company["name"]

        try:

            latest = get_latest_filing(cik)

            if latest is None:
                continue

            latest_accession = latest["accessionNumber"]

            stored_accession = index_data.get(symbol)

            if stored_accession == latest_accession:
                print(f"{symbol}: no update")
                continue

            print(
                f"{symbol}: update detected "
                f"({stored_accession} -> {latest_accession})"
            )

            changed_companies.append(
                {
                    "symbol": symbol,
                    "cik": cik,
                    "name": name,
                    "accessionNumber": latest_accession,
                }
            )

        except Exception as e:
            print(f"{symbol}: {e}")

    return changed_companies


def update_index_for_company(
    symbol,
    accession_number,
):
    """
    処理成功後にindex更新
    """

    index_data = load_index()

    index_data[symbol] = accession_number

    save_index(index_data)