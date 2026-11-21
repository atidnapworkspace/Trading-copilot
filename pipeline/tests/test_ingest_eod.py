import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tcp.jobs.ingest_eod import bars_to_rows, pending_dates, weekdays  # noqa: E402
from tcp.validators import validate_bar  # noqa: E402


def test_validate_bar_cases():
    assert validate_bar(10, 11, 9, 10.5, 1000) == "OK"
    assert validate_bar(None, 11, 9, 10.5, 1000) == "MISSING"
    assert validate_bar(10, 11, 9, 0, 1000) == "SUSPECT"          # zero close
    assert validate_bar(10, 9, 11, 10, 1000) == "SUSPECT"         # high < low
    assert validate_bar(10, 11, 9, 12, 1000) == "SUSPECT"         # close above high
    assert validate_bar(10, 11, 9, 10, -5) == "SUSPECT"           # negative volume


def test_weekdays_skips_weekend():
    # 2026-11-20 is a Friday; 21-22 weekend; 23 Monday
    got = weekdays(date(2026, 11, 20), date(2026, 11, 23))
    assert [d.isoformat() for d in got] == ["2026-11-20", "2026-11-23"]


def test_pending_dates_newest_first_and_skips_loaded():
    got = pending_dates(date(2026, 11, 16), date(2026, 11, 20), {"2026-11-18"})
    assert got == ["2026-11-20", "2026-11-19", "2026-11-17", "2026-11-16"]


def test_bars_to_rows_filters_and_flags():
    ids = {"AAPL": 1, "PENNY": 2, "BAD": 3}
    results = [
        {"T": "AAPL", "o": 100, "h": 102, "l": 99, "c": 101, "v": 1_000_000},   # ok
        {"T": "PENNY", "o": 0.5, "h": 0.6, "l": 0.4, "c": 0.5, "v": 10_000},    # close < 1 => skipped
        {"T": "BAD", "o": 50, "h": 49, "l": 51, "c": 50, "v": 1_000_000},       # high<low => SUSPECT kept
        {"T": "ZZZ", "o": 5, "h": 6, "l": 4, "c": 5, "v": 1_000_000},           # not in universe
        {"T": "AAPL2", "o": 5, "h": 6, "l": 4, "c": 5, "v": 10},                # not in universe
    ]
    rows, stats = bars_to_rows(results, ids, "2026-11-20", min_close=1, min_dollar_volume=250_000)
    by = {r["instrument_id"]: r for r in rows}
    assert set(by) == {1, 3}
    assert by[1]["quality"] == "OK" and by[3]["quality"] == "SUSPECT"
    assert by[1]["close_adj"] is None                                  # raw only; split-adjust happens later
    assert stats["illiquid_skipped"] == 1 and stats["not_in_universe"] == 2
    assert len({tuple(sorted(r)) for r in rows}) == 1                  # uniform keys for bulk upsert
