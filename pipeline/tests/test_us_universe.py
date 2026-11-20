import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tcp.us_universe import filter_universe, parse_directory  # noqa: E402

NASDAQ = """Symbol|Security Name|Market Category|Test Issue|Financial Status|Round Lot Size|ETF|NextShares
AAPL|Apple Inc. - Common Stock|Q|N|N|100|N|N
QQQ|Invesco QQQ Trust, Series 1|G|N|N|100|Y|N
ZVZZT|NASDAQ TEST STOCK|G|Y|N|100|N|N
ABCDW|Foo Acquisition Corp - Warrants|S|N|N|100|N|N
File Creation Time: 1120202600:00|||||||
"""
OTHER = """ACT Symbol|Security Name|Exchange|CQS Symbol|ETF|Round Lot Size|Test Issue|NASDAQ Symbol
JPM|JPMorgan Chase & Co. Common Stock|N|JPM|N|100|N|JPM
BRK.B|Berkshire Hathaway Inc. Class B|N|BRK.B|N|100|N|BRK-B
SPY|SPDR S&P 500 ETF Trust|P|SPY|Y|100|N|SPY
AAA$B|Some Preferred Stock Series B|N|AAA$B|N|100|N|AAA-B
File Creation Time: 1120202600:00|||||||
"""


def _build():
    import pandas as pd
    nas = parse_directory(NASDAQ, "Symbol", "ETF", "NASDAQ")
    oth = parse_directory(OTHER, "ACT Symbol", "ETF", None)
    return filter_universe(pd.concat([nas, oth], ignore_index=True))


def test_keeps_stocks_and_etfs_with_types():
    u = _build().set_index("symbol")
    assert set(u.index) == {"AAPL", "QQQ", "JPM", "BRK.B", "SPY"}
    assert u.loc["QQQ", "asset_type"] == "etf"
    assert u.loc["SPY", "asset_type"] == "etf"
    assert u.loc["AAPL", "asset_type"] == "stock"


def test_drops_test_issues_warrants_and_preferreds():
    syms = set(_build()["symbol"])
    assert "ZVZZT" not in syms      # test issue
    assert "ABCDW" not in syms      # warrants
    assert "AAA$B" not in syms      # preferred / '$' symbol


def test_footer_row_is_removed_and_exchange_mapped():
    u = _build().set_index("symbol")
    assert not any(s.startswith("File") for s in u.index)
    assert u.loc["JPM", "exchange"] == "NYSE"
    assert u.loc["SPY", "exchange"] == "NYSE Arca"
