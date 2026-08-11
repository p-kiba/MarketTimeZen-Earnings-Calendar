from datetime import date, datetime
import json
import os
import tempfile


CONFIRMED = "confirmed"
UNCONFIRMED = "unconfirmed"
CHANGED = "changed"
VALID_STATUSES = {CONFIRMED, UNCONFIRMED, CHANGED}


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


def sort_earnings(records):
    """Return unique earnings records in a stable date/symbol order."""
    return sorted(
        deduplicate_earnings(records),
        key=lambda record: (record["date"], record["symbol"]),
    )


def load_existing_earnings(path):
    """Load a JSON earnings array, returning an empty list when absent."""
    try:
        with open(path, encoding="utf-8") as earnings_file:
            records = json.load(earnings_file)
    except FileNotFoundError:
        return []

    if not isinstance(records, list):
        raise ValueError(f"{path} must contain a JSON array")
    return records


def write_earnings_atomically(path, records):
    """Replace an earnings JSON file only after the new file is complete."""
    directory = os.path.dirname(os.path.abspath(path))
    stem = os.path.splitext(os.path.basename(path))[0]
    temporary_path = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=directory,
            prefix=f".{stem}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(records, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
        os.replace(temporary_path, path)
    except Exception:
        if temporary_path and os.path.exists(temporary_path):
            os.unlink(temporary_path)
        raise


def merge_earnings_history(
    previous_records,
    snapshot_records,
    *,
    window_start,
    window_end,
    preserve_through=None,
):
    """Replace future window data while preserving completed history."""
    window_start = _as_date(window_start)
    window_end = _as_date(window_end)
    if preserve_through is not None:
        preserve_through = _as_date(preserve_through)
    previous = deduplicate_earnings(previous_records)
    snapshot = _records_in_window(
        deduplicate_earnings(snapshot_records), window_start, window_end
    )
    history = [
        record
        for record in previous
        if not window_start <= _record_date(record) <= window_end
        or (
            preserve_through is not None
            and _record_date(record) <= preserve_through
        )
    ]
    # Snapshot records come first so refreshed metadata wins for the same key.
    return sort_earnings(snapshot + history)


def reconcile_earnings(
    previous_records,
    fetched_records,
    *,
    today,
    window_start,
    window_end,
    successful_ranges,
):
    """Reconcile the latest API snapshot with the previously saved schedule."""
    today = _as_date(today)
    window_start = _as_date(window_start)
    window_end = _as_date(window_end)
    successful_ranges = [
        (_as_date(start), _as_date(end)) for start, end in successful_ranges
    ]

    previous_unique = deduplicate_earnings(previous_records)
    previous = _records_in_window(previous_unique, window_start, window_end)
    history = [
        record
        for record in previous_unique
        if not window_start <= _record_date(record) <= window_end
    ]
    fetched = _records_in_window(
        deduplicate_earnings(fetched_records), window_start, window_end
    )

    previous_keys = {_record_key(record) for record in previous}
    previous_statuses = {
        _record_key(record): _normalized_status(record) for record in previous
    }
    fetched_keys = {_record_key(record) for record in fetched}
    newly_confirmed_future_symbols = {
        record["symbol"]
        for record in fetched
        if _record_date(record) >= today
        and (
            _record_key(record) not in previous_keys
            or previous_statuses[_record_key(record)] != CONFIRMED
        )
    }
    reconciled = [_with_status(record, CONFIRMED) for record in fetched]

    for record in previous:
        if _record_key(record) in fetched_keys:
            continue

        event_date = _record_date(record)
        previous_status = _normalized_status(record)

        if previous_status == CHANGED:
            reconciled.append(_with_status(record, CHANGED))
        elif not _date_is_covered(event_date, successful_ranges):
            reconciled.append(_with_status(record, previous_status))
        elif event_date < today:
            if (
                previous_status == UNCONFIRMED
                and record["symbol"] in newly_confirmed_future_symbols
            ):
                reconciled.append(_with_status(record, CHANGED))
            else:
                reconciled.append(_with_status(record, previous_status))
        elif record["symbol"] in newly_confirmed_future_symbols:
            reconciled.append(_with_status(record, CHANGED))
        else:
            reconciled.append(_with_status(record, UNCONFIRMED))

    return sort_earnings(reconciled + history)


def _as_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _record_date(record):
    return date.fromisoformat(record["date"])


def _record_key(record):
    return record["symbol"], record["date"]


def _records_in_window(records, window_start, window_end):
    return [
        record
        for record in records
        if window_start <= _record_date(record) <= window_end
    ]


def _normalized_status(record):
    status = record.get("status", CONFIRMED)
    return status if status in VALID_STATUSES else CONFIRMED


def _with_status(record, status):
    updated = dict(record)
    updated["status"] = status
    return updated


def _date_is_covered(event_date, successful_ranges):
    return any(start <= event_date <= end for start, end in successful_ranges)
