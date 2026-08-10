def deduplicate_earnings(records):
    """Keep the first earnings record for each symbol and date."""
    seen = set()
    unique_records = []

    for record in records:
        key = (record["symbol"], record["date"])
        if key in seen:
            continue

        seen.add(key)
        unique_records.append(record)

    return unique_records
