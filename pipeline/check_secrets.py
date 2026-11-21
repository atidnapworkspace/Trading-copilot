"""Verify that required secrets exist AND work, without ever printing a value.

Only prints: presence, length, and HTTP status codes. Exceptions print only their type
(requests exceptions can embed URLs). Writes docs/secrets-check.md.
"""
import os
from datetime import date, timedelta
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "secrets-check.md"
NAMES = ["POLYGON_API_KEY", "FINNHUB_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "SEC_CONTACT_EMAIL"]
rows = []


def env(name):
    return os.environ.get(name, "").strip()


def record(name, ok, detail):
    rows.append((name, ok, detail))
    print(f"[{'OK ' if ok else 'FAIL'}] {name}: {detail}", flush=True)


def safe(fn):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001
        return False, f"error de red/tipo {type(e).__name__}"


def last_weekday(days_back=7):
    d = date.today() - timedelta(days=days_back)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d.isoformat()


def check_polygon():
    r = requests.get(
        f"https://api.polygon.io/v2/aggs/grouped/locale/us/market/stocks/{last_weekday()}",
        params={"adjusted": "true"}, headers={"Authorization": f"Bearer {env('POLYGON_API_KEY')}"}, timeout=40)
    if r.status_code != 200:
        return False, f"HTTP {r.status_code}"
    j = r.json()
    return True, f"HTTP 200, resultsCount={j.get('resultsCount')} (grouped daily, todo el mercado en 1 llamada)"


def check_finnhub():
    r = requests.get("https://finnhub.io/api/v1/quote", params={"symbol": "AAPL"},
                     headers={"X-Finnhub-Token": env("FINNHUB_API_KEY")}, timeout=25)
    ok = r.status_code == 200 and r.json().get("c", 0) > 0
    return ok, f"HTTP {r.status_code}, precio presente={bool(r.status_code == 200 and r.json().get('c'))}"


def check_supabase():
    base = env("SUPABASE_URL").rstrip("/")
    key = env("SUPABASE_SERVICE_KEY")
    r = requests.get(f"{base}/rest/v1/instruments", params={"select": "id", "limit": "1"},
                     headers={"apikey": key, "Authorization": f"Bearer {key}"}, timeout=25)
    return r.status_code == 200, f"HTTP {r.status_code} (esquema accesible con service role)"


def main():
    for n in NAMES:
        v = env(n)
        record(f"{n} presente", bool(v), f"longitud={len(v)}")
    checks = [("POLYGON_API_KEY", check_polygon), ("FINNHUB_API_KEY", check_finnhub),
              ("SUPABASE_*", check_supabase)]
    for name, fn in checks:
        need = ["SUPABASE_URL", "SUPABASE_SERVICE_KEY"] if name == "SUPABASE_*" else [name]
        if not all(env(n) for n in need):
            record(f"{name} funciona", False, "omitido: falta el secreto")
            continue
        ok, detail = safe(fn)
        record(f"{name} funciona", ok, detail)
    lines = ["# Chequeo de secretos (sin valores)", "", "| Chequeo | Estado | Detalle |", "|---|---|---|"]
    lines += [f"| {n} | {'✅' if ok else '❌'} | {d} |" for n, ok, d in rows]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
