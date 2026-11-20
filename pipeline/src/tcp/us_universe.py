"""Build the US equity/ETF universe from the official Nasdaq Trader symbol directories.

Pure functions (parse + filter) are unit-tested; fetching is a thin wrapper.
"""
import io
import re

import pandas as pd
import requests

NASDAQ_URL = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
OTHER_URL = "https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt"

# Name patterns that are not plain common stock / ETF shares.
_EXCLUDE_NAME = re.compile(
    r"\b(?:warrants?|rights?|units?|preferred|pref\b|depositary shares? representing|"
    r"notes? due|subordinated|trust preferred|acquisition corp)\b",
    re.IGNORECASE,
)
# Symbols with these characters are share classes/derivatives (BRK.B is kept: handled by '.'/'$' rule below).
_BAD_SYMBOL = re.compile(r"[\$\^]|\.WS|\.U$|\.R$")


def parse_directory(text: str, symbol_col: str, etf_col: str, exchange: str | None) -> pd.DataFrame:
    """Parse one Nasdaq Trader pipe-delimited file (drops the trailing 'File Creation Time' row)."""
    df = pd.read_csv(io.StringIO(text), sep="|", dtype=str).fillna("")
    df = df[~df.iloc[:, 0].str.startswith("File Creation Time")]
    out = pd.DataFrame({
        "symbol": df[symbol_col].str.strip(),
        "name": df["Security Name"].str.strip(),
        "is_etf": df[etf_col].str.strip().eq("Y"),
        "test_issue": df["Test Issue"].str.strip().eq("Y"),
        "exchange": exchange if exchange else df["Exchange"].map(
            {"N": "NYSE", "A": "NYSE American", "P": "NYSE Arca", "Z": "Cboe BZX", "V": "IEX"}
        ).fillna("OTHER"),
    })
    if "Financial Status" in df.columns:  # Nasdaq file only
        out["deficient"] = df["Financial Status"].str.strip().ne("N")
    else:
        out["deficient"] = False
    return out


def filter_universe(df: pd.DataFrame) -> pd.DataFrame:
    """Keep common stocks and ETFs; drop tests, warrants, rights, units, preferreds, SPAC shells."""
    keep = (
        ~df["test_issue"]
        & ~df["symbol"].str.contains(_BAD_SYMBOL)
        & ~df["name"].str.contains(_EXCLUDE_NAME)
        & df["symbol"].str.match(r"^[A-Z]{1,5}([.-][A-Z])?$")
    )
    out = df[keep].copy()
    out["asset_type"] = out["is_etf"].map({True: "etf", False: "stock"})
    return out.drop_duplicates("symbol").sort_values("symbol").reset_index(drop=True)


def fetch_us_universe(session: requests.Session | None = None) -> pd.DataFrame:
    s = session or requests.Session()
    hdr = {"User-Agent": "Mozilla/5.0 (compatible; TradingCopilot/0.1)"}
    a = s.get(NASDAQ_URL, headers=hdr, timeout=30)
    b = s.get(OTHER_URL, headers=hdr, timeout=30)
    a.raise_for_status()
    b.raise_for_status()
    nas = parse_directory(a.text, "Symbol", "ETF", "NASDAQ")
    oth = parse_directory(b.text, "ACT Symbol", "ETF", None)
    return filter_universe(pd.concat([nas, oth], ignore_index=True))
