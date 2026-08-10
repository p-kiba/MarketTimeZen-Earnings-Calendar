from datetime import date, datetime


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

    previous = _records_in_window(
        deduplicate_earnings(previous_records), window_start, window_end
    )
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

    return reconciled


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
