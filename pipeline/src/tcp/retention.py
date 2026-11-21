"""Shared retention rules for prices_daily. Pure functions, no I/O.

Rule: a month may be deleted from the DB only if (a) it was backed up and verified on the owner's PC
and (b) the whole month is older than RETAIN_DAYS.
"""
from datetime import date, timedelta

RETAIN_DAYS = 400               # ~13 months (52W metrics need ~12)
STATE_KEY = "prices_backup"     # ingest_state value: {"months": ["2025-11", ...]}


def month_bounds(ym: str) -> tuple[date, date]:
    y, m = int(ym[:4]), int(ym[5:7])
    first = date(y, m, 1)
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return first, nxt - timedelta(days=1)


def cutoff(today: date) -> date:
    return today - timedelta(days=RETAIN_DAYS)


def months_between(start: date, end: date) -> list[str]:
    out, y, m = [], start.year, start.month
    while (y, m) <= (end.year, end.month):
        out.append(f"{y:04d}-{m:02d}")
        y, m = y + (m == 12), m % 12 + 1
    return out


def months_to_backup(oldest: date, today: date, done: set[str]) -> list[str]:
    """Full months (from the oldest data) that end before the cutoff and are not backed up yet."""
    c = cutoff(today)
    return [ym for ym in months_between(oldest, c) if month_bounds(ym)[1] < c and ym not in done]


def months_to_delete(today: date, done: set[str]) -> list[str]:
    c = cutoff(today)
    return sorted(ym for ym in done if month_bounds(ym)[1] < c)
