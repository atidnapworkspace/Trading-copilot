"""Polygon.io (free tier) client: rate-limited, never prints the key.

Free tier ~5 calls/minute => min_interval 12.5s. Auth via header (never in the URL).
"""
import os
import time

import requests


class PolygonError(RuntimeError):
    pass


class Polygon:
    BASE = "https://api.polygon.io"

    def __init__(self, key: str | None = None, min_interval: float = 12.5):
        key = (key or os.environ["POLYGON_API_KEY"]).strip()
        self.min_interval = min_interval
        self.calls = 0
        self._last = 0.0
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {key}"

    def _get(self, url: str, params: dict | None = None) -> dict:
        for attempt in range(6):
            wait = self.min_interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            self.calls += 1
            r = self.session.get(url, params=params, timeout=90)
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(30 * (attempt + 1))
                continue
            raise PolygonError(f"HTTP {r.status_code}: {r.text[:200]}")
        raise PolygonError("retries exhausted")

    def grouped_daily(self, d: str) -> list[dict]:
        """Whole US market for one date, UNADJUSTED. Empty list on holidays/weekends."""
        j = self._get(f"{self.BASE}/v2/aggs/grouped/locale/us/market/stocks/{d}",
                      {"adjusted": "false", "include_otc": "false"})
        return j.get("results") or []

    def splits_since(self, since: str) -> list[dict]:
        out = []
        j = self._get(f"{self.BASE}/v3/reference/splits",
                      {"execution_date.gte": since, "limit": 1000, "order": "asc", "sort": "execution_date"})
        while True:
            out.extend(j.get("results") or [])
            nxt = j.get("next_url")
            if not nxt:
                return out
            j = self._get(nxt)
