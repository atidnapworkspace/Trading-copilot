"""Load the US universe (Nasdaq Trader + SEC CIK map) into Supabase `instruments` / `instrument_aliases`.

Run:  PYTHONPATH=pipeline/src python -m tcp.jobs.load_universe
Env:  SUPABASE_URL, SUPABASE_SERVICE_KEY, SEC_CONTACT_EMAIL
"""
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from tcp.supa import Supa
from tcp.us_universe import fetch_us_universe

ROOT = Path(__file__).resolve().parents[4]


def norm_symbol(sym: str) -> str:
    """SEC uses dashes for share classes (BRK-B); Nasdaq Trader uses dots (BRK.B)."""
    return sym.replace(".", "-").upper()


def build_rows(universe: pd.DataFrame, cik_by_ticker: dict[str, str]) -> list[dict]:
    rows = []
    for r in universe.itertuples():
        cik = cik_by_ticker.get(norm_symbol(r.symbol))
        rows.append({
            "symbol": r.symbol,
            "market": "US",
            "asset_type": r.asset_type,
            "name": r.name or None,
            "exchange": r.exchange,
            "currency": "USD",
            "cik": cik,
            "active": True,
        })
    return rows


def build_alias_rows(instruments: list[dict]) -> list[dict]:
    """instruments: [{id, symbol}] as returned by the DB."""
    out = []
    for i in instruments:
        out.append({"instrument_id": i["id"], "provider": "yahoo", "provider_symbol": norm_symbol(i["symbol"])})
        out.append({"instrument_id": i["id"], "provider": "polygon", "provider_symbol": i["symbol"]})
    return out


def fetch_cik_map(contact: str) -> dict[str, str]:
    r = requests.get("https://www.sec.gov/files/company_tickers.json",
                     headers={"User-Agent": f"TradingCopilot/0.1 {contact}"}, timeout=30)
    r.raise_for_status()
    return {v["ticker"].upper(): str(v["cik_str"]).zfill(10) for v in r.json().values()}


def main():
    contact = os.environ["SEC_CONTACT_EMAIL"]
    db = Supa()
    universe = fetch_us_universe()
    cik_map = fetch_cik_map(contact)
    rows = build_rows(universe, cik_map)
    db.upsert("instruments", rows, on_conflict="market,symbol,currency")

    existing = db.select_all("instruments", {"select": "id,symbol,active", "market": "eq.US",
                                             "currency": "eq.USD", "order": "id"})
    db.upsert("instrument_aliases", build_alias_rows(existing), on_conflict="instrument_id,provider")

    current = set(universe["symbol"])
    stale = [e["symbol"] for e in existing if e["active"] and e["symbol"] not in current]
    for i in range(0, len(stale), 50):
        quoted = ",".join(f'"{s}"' for s in stale[i:i + 50])
        db.patch("instruments", {"market": "eq.US", "currency": "eq.USD", "symbol": f"in.({quoted})"},
                 {"active": False})

    with_cik = sum(1 for r in rows if r["cik"])
    stocks = sum(1 for r in rows if r["asset_type"] == "stock")
    stocks_cik = sum(1 for r in rows if r["asset_type"] == "stock" and r["cik"])
    total_db = db.count("instruments", {"market": "eq.US", "active": "eq.true"})
    alias_db = db.count("instrument_aliases")
    lines = [
        "# Carga del universo EE.UU.", "",
        f"Corrida: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}", "",
        f"- Instrumentos en el universo: {len(rows)} ({stocks} acciones, {len(rows) - stocks} ETFs)",
        f"- Con CIK de la SEC: {with_cik} (acciones con CIK: {stocks_cik} de {stocks})",
        f"- Activos en la base (US): {total_db}",
        f"- Aliases en la base: {alias_db}",
        f"- Desactivados por salir del universo: {len(stale)}",
    ]
    (ROOT / "docs" / "load-universe-result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
