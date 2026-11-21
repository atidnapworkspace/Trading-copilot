import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tcp.jobs.load_universe import build_alias_rows, build_rows, norm_symbol  # noqa: E402


def _uni():
    return pd.DataFrame([
        {"symbol": "AAPL", "name": "Apple Inc.", "exchange": "NASDAQ", "asset_type": "stock"},
        {"symbol": "BRK.B", "name": "Berkshire B", "exchange": "NYSE", "asset_type": "stock"},
        {"symbol": "QQQ", "name": "Invesco QQQ", "exchange": "NASDAQ", "asset_type": "etf"},
    ])


def test_norm_symbol_dot_to_dash():
    assert norm_symbol("BRK.B") == "BRK-B"
    assert norm_symbol("aapl") == "AAPL"


def test_build_rows_maps_cik_and_leaves_etf_without_cik():
    rows = {r["symbol"]: r for r in build_rows(_uni(), {"AAPL": "0000320193", "BRK-B": "0001067983"})}
    assert rows["AAPL"]["cik"] == "0000320193"
    assert rows["BRK.B"]["cik"] == "0001067983"      # dot symbol matched via SEC dash form
    assert rows["QQQ"]["cik"] is None
    assert all(r["market"] == "US" and r["currency"] == "USD" and r["active"] for r in rows.values())


def test_all_rows_share_same_keys_for_bulk_upsert():
    rows = build_rows(_uni(), {})
    assert len({tuple(sorted(r)) for r in rows}) == 1


def test_alias_rows_yahoo_dash_polygon_dot():
    al = build_alias_rows([{"id": 7, "symbol": "BRK.B"}])
    got = {a["provider"]: a["provider_symbol"] for a in al}
    assert got == {"yahoo": "BRK-B", "polygon": "BRK.B"}
