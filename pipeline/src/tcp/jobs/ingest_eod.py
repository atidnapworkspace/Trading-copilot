"""Ingest US end-of-day bars (raw, unadjusted) + splits from Polygon into Supabase.

Resumable: loaded dates are tracked in `ingest_state`. Newest dates first, so the latest data lands early.
Run:  PYTHONPATH=pipeline/src python -m tcp.jobs.ingest_eod
Env:  POLYGON_API_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY, LOOKBACK_DAYS (370), MAX_MINUTES (100)
"""
import os
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from tcp.polygon import Polygon
from tcp.retention import STATE_KEY as BACKUP_KEY
from tcp.retention import cutoff, month_bounds, months_to_delete
from tcp.supa import Supa
from tcp.validators import validate_bar

ROOT = Path(__file__).resolve().parents[4]
STATE_KEY = "eod_loaded"
DEFAULT_FILTERS = {"min_close": 1, "min_dollar_volume": 250000}


def weekdays(start: date, end: date) -> list[date]:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def pending_dates(start: date, end: date, loaded: set[str]) -> list[str]:
    """Weekdays in [start, end] not yet loaded, newest first."""
    return sorted((d.isoformat() for d in weekdays(start, end) if d.isoformat() not in loaded), reverse=True)


def bars_to_rows(results: list[dict], symbol_to_id: dict[str, int], d: str,
                 min_close: float, min_dollar_volume: float) -> tuple[list[dict], Counter]:
    rows, stats = [], Counter()
    for r in results:
        iid = symbol_to_id.get(r.get("T"))
        if iid is None:
            stats["not_in_universe"] += 1
            continue
        o, h, l, c, v = r.get("o"), r.get("h"), r.get("l"), r.get("c"), r.get("v")  # noqa: E741
        if c is None or c < min_close or c * (v or 0) < min_dollar_volume:
            stats["illiquid_skipped"] += 1
            continue
        q = validate_bar(o, h, l, c, v)
        stats[f"quality_{q}"] += 1
        rows.append({"instrument_id": iid, "d": d, "open": o, "high": h, "low": l, "close_raw": c,
                     "close_adj": None, "volume": v, "source": "polygon", "quality": q})
    return rows, stats


def apply_retention(db: Supa, today: date) -> tuple[int, str]:
    """Delete only months backed up on the owner's PC AND older than the cutoff. Returns (deleted, warning)."""
    st = db.select_all("ingest_state", {"select": "value", "key": f"eq.{BACKUP_KEY}"})
    done = set(st[0]["value"].get("months", [])) if st else set()
    deleted = 0
    for ym in months_to_delete(today, done):
        first, last = month_bounds(ym)
        deleted += db.delete("prices_daily", {"and": f"(d.gte.{first},d.lte.{last})"})
    oldest = db._request("GET", "prices_daily", params={"select": "d", "order": "d.asc", "limit": 1}).json()
    warn = ""
    if oldest and date.fromisoformat(oldest[0]["d"]) < cutoff(today):
        warn = (f"⚠️ Hay precios con más de 400 días sin respaldar (desde {oldest[0]['d']}): "
                "corré el respaldo en la PC; hasta entonces no se borran.")
    return deleted, warn


def load_filters(db: Supa) -> dict:
    got = db.select_all("app_settings", {"select": "value", "key": "eq.storage_filters"})
    return {**DEFAULT_FILTERS, **(got[0]["value"] if got else {})}


def main():
    lookback = int(os.environ.get("LOOKBACK_DAYS", "370"))
    max_minutes = float(os.environ.get("MAX_MINUTES", "100"))
    t0 = time.time()
    db, poly = Supa(), Polygon()

    inst = db.select_all("instruments", {"select": "id,symbol", "market": "eq.US", "active": "eq.true",
                                         "order": "id"})
    symbol_to_id = {i["symbol"]: i["id"] for i in inst}
    flt = load_filters(db)

    end = datetime.now(timezone.utc).date() - timedelta(days=1)
    start = end - timedelta(days=lookback)

    # splits (a few calls for the whole market)
    splits = []
    for s in poly.splits_since(start.isoformat()):
        iid = symbol_to_id.get(s.get("ticker"))
        if iid and s.get("split_from") and s.get("split_to"):
            splits.append({"instrument_id": iid, "ex_date": s["execution_date"], "split_from": s["split_from"],
                           "split_to": s["split_to"], "source": "polygon"})
    db.upsert("splits", splits, on_conflict="instrument_id,ex_date")

    st = db.select_all("ingest_state", {"select": "value", "key": f"eq.{STATE_KEY}"})
    loaded = set(st[0]["value"].get("dates", [])) if st else set()
    todo = pending_dates(start, end, loaded)

    stats, rows_total, done, holidays = Counter(), 0, 0, 0
    for d in todo:
        if (time.time() - t0) / 60 > max_minutes:
            break
        results = poly.grouped_daily(d)
        if not results:
            holidays += 1
        else:
            rows, s = bars_to_rows(results, symbol_to_id, d, flt["min_close"], flt["min_dollar_volume"])
            db.upsert("prices_daily", rows, on_conflict="instrument_id,d", batch=1000)
            rows_total += len(rows)
            stats.update(s)
        loaded.add(d)
        done += 1
        db.upsert("ingest_state", [{"key": STATE_KEY, "value": {"dates": sorted(loaded)},
                                    "updated_at": datetime.now(timezone.utc).isoformat()}], on_conflict="key")

    deleted, warn = apply_retention(db, datetime.now(timezone.utc).date())
    size = db._request("POST", "rpc/db_size_mb", json={}).json()
    remaining = len(todo) - done
    lines = [
        "# Ingesta EOD EE.UU.", "",
        f"Corrida: {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} — ventana {start} a {end}", "",
        f"- Fechas cargadas en esta corrida: {done} (feriados/sin datos: {holidays})",
        f"- Fechas pendientes: {remaining}",
        f"- Filas escritas: {rows_total} (filtros: cierre ≥ {flt['min_close']}, volumen USD ≥ {flt['min_dollar_volume']})",
        f"- Splits guardados: {len(splits)}",
        f"- Calidad de barras: OK={stats['quality_OK']} SUSPECT={stats['quality_SUSPECT']} "
        f"MISSING={stats['quality_MISSING']}",
        f"- Omitidas por iliquidez: {stats['illiquid_skipped']}; fuera del universo: {stats['not_in_universe']}",
        f"- Llamadas a Polygon: {poly.calls}",
        f"- Tamaño de la base: {size} MB de 500 MB",
        f"- Retención: {deleted} filas borradas (solo meses ya respaldados en la PC y con más de 400 días)",
    ]
    if warn:
        lines.append(f"- {warn}")
    (ROOT / "docs" / "ingest-eod-result.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def run():
    try:
        main()
    except Exception as e:  # noqa: BLE001 - secret-free error summary, then fail
        msg = f"# Ingesta EOD EE.UU. — ERROR\n\n{datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}\n\n" \
              f"`{type(e).__name__}`: {str(e)[:800]}\n"
        (ROOT / "docs" / "ingest-eod-result.md").write_text(msg, encoding="utf-8")
        print(msg)
        raise


if __name__ == "__main__":
    run()
