import gzip
import os
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tcp.envfile import load_env  # noqa: E402
from tcp.jobs.backup_prices import count_csv_gz, write_csv_gz  # noqa: E402
from tcp.retention import month_bounds, months_between, months_to_backup, months_to_delete  # noqa: E402


def test_month_bounds_including_december_and_leap_year():
    assert month_bounds("2025-12") == (date(2025, 12, 1), date(2025, 12, 31))
    assert month_bounds("2028-02") == (date(2028, 2, 1), date(2028, 2, 29))


def test_months_between():
    assert months_between(date(2025, 11, 15), date(2026, 2, 1)) == ["2025-11", "2025-12", "2026-01", "2026-02"]


def test_nothing_to_backup_while_data_is_younger_than_400_days():
    # today 2026-11-21 -> cutoff 2025-10-17; oldest data 2025-11-15 -> nothing eligible
    assert months_to_backup(date(2025, 11, 15), date(2026, 11, 21), set()) == []


def test_only_full_months_before_cutoff_and_not_done():
    # today 2027-02-10 -> cutoff 2026-01-06: Nov and Dec 2025 eligible; Jan 2026 not (ends after cutoff)
    assert months_to_backup(date(2025, 11, 15), date(2027, 2, 10), set()) == ["2025-11", "2025-12"]
    assert months_to_backup(date(2025, 11, 15), date(2027, 2, 10), {"2025-11"}) == ["2025-12"]


def test_delete_only_backed_up_months_older_than_cutoff():
    today = date(2027, 2, 10)
    assert months_to_delete(today, set()) == []                         # nothing backed up => nothing deleted
    assert months_to_delete(today, {"2025-11", "2026-01"}) == ["2025-11"]  # 2026-01 too recent


def test_csv_gz_roundtrip_counts(tmp_path):
    rows = [{"d": "2025-11-17", "instrument_id": 1, "open": 1, "high": 2, "low": 1, "close_raw": 1.5,
             "volume": 10, "source": "polygon", "quality": "OK"}] * 3
    n, sha = write_csv_gz(tmp_path / "2025-11.csv.gz", rows, {1: "AAPL"})
    assert n == 3 == count_csv_gz(tmp_path / "2025-11.csv.gz") and len(sha) == 64
    with gzip.open(tmp_path / "2025-11.csv.gz", "rt", encoding="utf-8") as f:
        assert f.readline().startswith("date,symbol")
        assert ",AAPL," in f.readline()


def test_load_env_with_bom_and_quotes(tmp_path, monkeypatch):
    p = tmp_path / ".env"
    p.write_text('﻿TCP_TEST_A="x1"\n# comment\nTCP_TEST_B=y2\n', encoding="utf-8")
    monkeypatch.delenv("TCP_TEST_A", raising=False)
    monkeypatch.delenv("TCP_TEST_B", raising=False)
    assert load_env(p)
    assert os.environ["TCP_TEST_A"] == "x1" and os.environ["TCP_TEST_B"] == "y2"
