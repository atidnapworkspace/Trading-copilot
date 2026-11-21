"""Back up old prices_daily months to the owner's PC (historico/, not in Git) BEFORE the cloud deletes them.

Runs on the PC (weekly Windows task). Per month: export -> re-read and verify row counts against the DB
-> only then mark the month as backed up in `ingest_state`. The cloud job deletes only marked months.

Run:   scripts/backup_prices.ps1           (normal)
Test:  python -m tcp.jobs.backup_prices --test --out <dir>   (exports the oldest month, changes nothing)
Needs: .env at the project root with SUPABASE_URL and SUPABASE_SERVICE_KEY.
"""
import argparse
import csv
import gzip
import hashlib
from datetime import date, datetime
from pathlib import Path

from tcp.envfile import load_env
from tcp.retention import STATE_KEY, month_bounds, months_to_backup

ROOT = Path(__file__).resolve().parents[4]
COLS = ["date", "symbol", "instrument_id", "open", "high", "low", "close_raw", "volume", "source", "quality"]


def write_csv_gz(path: Path, rows: list[dict], symbols: dict[int, str]) -> tuple[int, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    with gzip.open(tmp, "wt", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for r in rows:
            w.writerow([r["d"], symbols.get(r["instrument_id"], ""), r["instrument_id"], r["open"], r["high"],
                        r["low"], r["close_raw"], r["volume"], r["source"], r["quality"]])
    tmp.replace(path)
    return count_csv_gz(path), hashlib.sha256(path.read_bytes()).hexdigest()


def count_csv_gz(path: Path) -> int:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return sum(1 for _ in f) - 1  # minus header


def log(msg: str):
    line = f"{datetime.now():%Y-%m-%d %H:%M} {msg}"
    print(line, flush=True)
    logf = ROOT / "historico" / "backup-log.txt"
    logf.parent.mkdir(parents=True, exist_ok=True)
    with logf.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def backup_month(db, ym: str, out_dir: Path, symbols: dict[int, str]) -> int:
    first, last = month_bounds(ym)
    flt = {"and": f"(d.gte.{first},d.lte.{last})"}
    rows = db.select_all("prices_daily", {"select": "instrument_id,d,open,high,low,close_raw,volume,source,quality",
                                          **flt, "order": "d,instrument_id"})
    n_db = db.count("prices_daily", flt)
    path = out_dir / f"{ym}.csv.gz"
    n_file, sha = write_csv_gz(path, rows, symbols)
    if not (len(rows) == n_db == n_file):
        raise RuntimeError(f"{ym}: verificación fallida (leídas={len(rows)} base={n_db} archivo={n_file})")
    with (out_dir / "MANIFEST.csv").open("a", encoding="utf-8") as f:
        f.write(f"{ym},{n_file},{sha},{datetime.now():%Y-%m-%d %H:%M}\n")
    return n_file


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="export the oldest month only; change nothing in the DB")
    ap.add_argument("--out", default=str(ROOT / "historico" / "prices_daily"))
    args = ap.parse_args()

    load_env(ROOT / ".env")
    from tcp.supa import Supa  # after .env is loaded
    db = Supa()
    out_dir = Path(args.out)

    oldest_rows = db._request("GET", "prices_daily", params={"select": "d", "order": "d.asc", "limit": 1}).json()
    if not oldest_rows:
        log("Sin datos en prices_daily.")
        return
    oldest = date.fromisoformat(oldest_rows[0]["d"])
    inst = db.select_all("instruments", {"select": "id,symbol", "order": "id"})
    symbols = {i["id"]: i["symbol"] for i in inst}

    if args.test:
        ym = f"{oldest:%Y-%m}"
        n = backup_month(db, ym, out_dir, symbols)
        log(f"[TEST] {ym}: {n} filas exportadas y verificadas en {out_dir} (sin cambios en la base)")
        return

    st = db.select_all("ingest_state", {"select": "value", "key": f"eq.{STATE_KEY}"})
    done = set(st[0]["value"].get("months", [])) if st else set()
    todo = months_to_backup(oldest, date.today(), done)
    if not todo:
        log(f"Nada para respaldar todavía (dato más viejo: {oldest}; meses ya respaldados: {len(done)}).")
        return
    for ym in todo:
        n = backup_month(db, ym, out_dir, symbols)
        done.add(ym)
        db.upsert("ingest_state", [{"key": STATE_KEY, "value": {"months": sorted(done)},
                                    "updated_at": datetime.now().astimezone().isoformat()}], on_conflict="key")
        log(f"{ym}: {n} filas respaldadas y verificadas; marcado para limpieza en la nube.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        log(f"ERROR {type(e).__name__}: {str(e)[:500]}")
        raise
