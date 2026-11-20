"""Phase 1.1 spike: verify real availability of every free data source.

Run:  SEC_CONTACT_EMAIL=... python pipeline/spike_sources.py
Writes docs/spike-results.md (contains no secrets / no email).
Each check returns (ok, detail). Nothing here computes business metrics.
"""
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / os.environ.get("SPIKE_OUT", "docs/spike-results.md")
CONTACT = os.environ.get("SEC_CONTACT_EMAIL", "")
BROWSER_UA = "Mozilla/5.0 (compatible; TradingCopilotSpike/0.1)"
TIMEOUT = 25

results = []


def check(name, fn):
    t0 = time.time()
    try:
        ok, detail = fn()
    except Exception as e:  # noqa: BLE001 - spike must never crash
        ok, detail = False, f"EXC {type(e).__name__}: {str(e)[:160]}"
    dt = time.time() - t0
    results.append((name, ok, round(dt, 1), detail))
    print(f"[{'OK ' if ok else 'FAIL'}] {name} ({dt:.1f}s) {detail}", flush=True)


def get(url, **kw):
    kw.setdefault("timeout", TIMEOUT)
    kw.setdefault("headers", {"User-Agent": BROWSER_UA})
    return requests.get(url, **kw)


# ---------- EE.UU. ----------
def nasdaq_trader():
    a = get("https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt")
    b = get("https://www.nasdaqtrader.com/dynamic/symdir/otherlisted.txt")
    if a.status_code != 200 or b.status_code != 200:
        return False, f"HTTP {a.status_code}/{b.status_code}"
    na = len(a.text.strip().splitlines()) - 2
    nb = len(b.text.strip().splitlines()) - 2
    return True, f"nasdaqlisted={na} otherlisted={nb} filas (incluye ETFs/warrants/etc, a filtrar)"


def sec_edgar():
    if not CONTACT:
        return False, "falta SEC_CONTACT_EMAIL"
    h = {"User-Agent": f"TradingCopilot/0.1 {CONTACT}"}
    r = get("https://data.sec.gov/api/xbrl/companyfacts/CIK0000320193.json", headers=h)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    j = r.json()
    gaap = j["facts"].get("us-gaap", {})
    keys = [k for k in ("EarningsPerShareDiluted", "StockholdersEquity", "NetIncomeLoss",
                        "WeightedAverageNumberOfDilutedSharesOutstanding") if k in gaap]
    return True, f"AAPL companyfacts {len(r.content)//1024}KB; conceptos clave presentes: {keys}"


def sec_tickers_map():
    h = {"User-Agent": f"TradingCopilot/0.1 {CONTACT}"}
    r = get("https://www.sec.gov/files/company_tickers.json", headers=h)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    return True, f"{len(r.json())} tickers->CIK"


def stooq():
    r = get("https://stooq.com/q/d/l/?s=aapl.us&i=d")
    head = r.text[:80].replace("\n", " | ")
    ok = r.status_code == 200 and r.text.lower().startswith("date")
    return ok, f"HTTP {r.status_code}; inicio: {head!r}"


def yahoo_prices():
    import yfinance as yf
    df = yf.download(["AAPL", "QQQ", "GGAL.BA", "BTC-USD"], period="1mo", auto_adjust=True,
                     progress=False, group_by="ticker", threads=False)
    got = {t: int(df[t]["Close"].dropna().shape[0]) for t in ["AAPL", "QQQ", "GGAL.BA", "BTC-USD"]
           if t in df.columns.get_level_values(0)}
    ok = all(v > 5 for v in got.values()) and len(got) == 4
    return ok, f"filas cierre 1 mes: {got}"


def yahoo_fundamentals():
    import yfinance as yf
    info = yf.Ticker("AAPL").info
    keys = {k: info.get(k) for k in ("trailingPE", "forwardPE", "priceToBook", "returnOnEquity")}
    ok = any(v is not None for v in keys.values())
    return ok, f"{keys}"


def yahoo_history_10y():
    import yfinance as yf
    df = yf.download("QQQ", period="10y", interval="1d", auto_adjust=True, progress=False)
    return len(df) > 2000, f"QQQ 10y diario: {len(df)} filas"


# ---------- Cripto ----------
def okx():
    h = "https://www.okx.com/api/v5"
    f = get(f"{h}/public/funding-rate?instId=BTC-USDT-SWAP").json()
    oi = get(f"{h}/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP").json()
    tk = get(f"{h}/market/ticker?instId=BTC-USDT").json()
    ok = f.get("code") == "0" and oi.get("code") == "0" and tk.get("code") == "0"
    fr = f["data"][0].get("fundingRate") if ok else None
    oi_v = oi["data"][0].get("oiUsd") if ok else None
    return ok, f"funding={fr} oiUsd={oi_v}"


def coingecko():
    r = get("https://api.coingecko.com/api/v3/coins/markets",
            params={"vs_currency": "usd", "order": "market_cap_desc", "per_page": 50, "page": 1})
    if r.status_code != 200:
        return False, f"HTTP {r.status_code} {r.text[:80]!r}"
    j = r.json()
    keys = [k for k in ("market_cap", "ath", "ath_change_percentage", "total_volume") if k in j[0]]
    return True, f"{len(j)} monedas, top={j[0]['symbol']}, campos={keys}"


def coingecko_global():
    r = get("https://api.coingecko.com/api/v3/global")
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    d = r.json()["data"]["market_cap_percentage"]
    return True, f"btc.d={d.get('btc'):.1f}%"


def binance_futures():
    r = get("https://fapi.binance.com/fapi/v1/premiumIndex?symbol=BTCUSDT")
    return r.status_code == 200, f"HTTP {r.status_code} {r.text[:90]!r}"


def binance_spot_public():
    r = get("https://data-api.binance.vision/api/v3/ticker/price?symbol=BTCUSDT")
    return r.status_code == 200, f"HTTP {r.status_code} {r.text[:70]!r}"


def bybit():
    r = get("https://api.bybit.com/v5/market/tickers?category=linear&symbol=BTCUSDT")
    ok = r.status_code == 200 and '"retCode":0' in r.text.replace(" ", "")
    return ok, f"HTTP {r.status_code} {r.text[:90]!r}"


# ---------- Argentina ----------
def data912(path, label):
    def _f():
        r = get(f"https://data912.com{path}")
        if r.status_code != 200:
            return False, f"HTTP {r.status_code}"
        j = r.json()
        sample = j[0] if isinstance(j, list) and j else j
        return bool(j), f"{label}: {len(j) if isinstance(j, list) else '?'} items; ej={json.dumps(sample)[:200]}"
    return _f


def data912_hist():
    r = get("https://data912.com/historical/stocks/GGAL")
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    j = r.json()
    return bool(j), f"GGAL hist: {len(j)} filas; ej={json.dumps(j[-1])[:160]}"


def byma_leading():
    url = "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/leading-equity"
    body = {"excludeZeroPxAndQty": True, "T2": True, "T1": False, "T0": False,
            "Content-Type": "application/json"}
    r = requests.post(url, json=body, headers={"User-Agent": BROWSER_UA}, timeout=TIMEOUT)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code} {r.text[:80]!r}"
    j = r.json()
    data = j.get("data", j) if isinstance(j, dict) else j
    return bool(data), f"{len(data)} items; campos={list(data[0].keys())[:12]}"


def byma_bonds():
    url = "https://open.bymadata.com.ar/vanoms-be-core/rest/api/bymadata/free/public-bonds"
    body = {"excludeZeroPxAndQty": True, "T2": True, "T1": False, "T0": False,
            "Content-Type": "application/json"}
    r = requests.post(url, json=body, headers={"User-Agent": BROWSER_UA}, timeout=TIMEOUT)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code} {r.text[:80]!r}"
    j = r.json()
    data = j.get("data", j) if isinstance(j, dict) else j
    return bool(data), f"{len(data)} items; campos={list(data[0].keys())[:12]}"


def dolarapi():
    r = get("https://dolarapi.com/v1/dolares")
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    names = [d["nombre"] for d in r.json()]
    return True, f"{names}"


CHECKS = [
    ("US: Nasdaq Trader universo", nasdaq_trader),
    ("US: SEC EDGAR companyfacts", sec_edgar),
    ("US: SEC ticker->CIK", sec_tickers_map),
    ("US: Stooq CSV diario", stooq),
    ("US: Yahoo precios (yfinance)", yahoo_prices),
    ("US: Yahoo fundamentales", yahoo_fundamentals),
    ("US: Yahoo histórico 10y QQQ", yahoo_history_10y),
    ("CRYPTO: OKX funding/OI/ticker", okx),
    ("CRYPTO: CoinGecko markets", coingecko),
    ("CRYPTO: CoinGecko global", coingecko_global),
    ("CRYPTO: Binance futures (geo?)", binance_futures),
    ("CRYPTO: Binance spot público", binance_spot_public),
    ("CRYPTO: Bybit linear", bybit),
    ("AR: data912 acciones", data912("/live/arg_stocks", "acciones")),
    ("AR: data912 cedears", data912("/live/arg_cedears", "cedears")),
    ("AR: data912 bonos", data912("/live/arg_bonds", "bonos")),
    ("AR: data912 histórico GGAL", data912_hist),
    ("AR: BYMA líderes", byma_leading),
    ("AR: BYMA bonos públicos", byma_bonds),
    ("AR: dolarapi CCL/MEP", dolarapi),
]


def main():
    for name, fn in CHECKS:
        check(name, fn)
        time.sleep(1.2)  # be polite
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    origin = os.environ.get("SPIKE_ORIGIN", "la PC del owner (IP residencial)")
    lines = [f"# Spike de fuentes — {ts}", "",
             f"Ejecutado desde: {origin}.", "",
             "| Fuente | Estado | Seg | Detalle |", "|---|---|---|---|"]
    for name, ok, dt, detail in results:
        lines.append(f"| {name} | {'✅' if ok else '❌'} | {dt} | {detail.replace('|', '/')} |")
    lines += ["", "Pendientes por falta de key (no probadas): Polygon/Massive free, Finnhub free, CoinGecko demo key."]
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nEscrito {OUT}")


if __name__ == "__main__":
    sys.exit(main())
