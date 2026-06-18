import time

from input.us_companies import TARGET_US
from submissions import (
    get_changed_companies,
    load_index,
    save_index,
)
from generate_earnings import (
    build_earnings,
    write_earnings_file,
)


def main():

    print("Checking SEC filings...")

    changed_companies = get_changed_companies(TARGET_US)

    if not changed_companies:
        print("No updates found.")
        return

    print(
        f"{len(changed_companies)} companies require updates."
    )

    index_data = load_index()

    for company in changed_companies:

        symbol = company["symbol"]
        cik = company["cik"]
        name = company["name"]
        accession_number = company["accessionNumber"]

        print(f"Updating {symbol}...")

        try:

            earnings = build_earnings(cik, company_name=name)

            filename = write_earnings_file(
                symbol,
                earnings,
            )

            index_data[symbol] = accession_number

            print(
                f"Wrote {filename}: "
                f"{len(earnings)} quarters"
            )

            time.sleep(0.2)

        except Exception as e:

            print(
                f"Failed {symbol}: {e}"
            )

    save_index(index_data)

    print("Done.")


if __name__ == "__main__":
    main()