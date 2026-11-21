"""Minimal Supabase PostgREST client (service role). No secrets are ever printed."""
import os
import time

import requests


class SupaError(RuntimeError):
    pass


class Supa:
    def __init__(self, url: str | None = None, key: str | None = None):
        self.url = (url or os.environ["SUPABASE_URL"]).strip().rstrip("/")
        key = (key or os.environ["SUPABASE_SERVICE_KEY"]).strip()
        self.headers = {"apikey": key, "Content-Type": "application/json"}
        if not key.startswith("sb_"):  # legacy JWT keys also go in Authorization
            self.headers["Authorization"] = f"Bearer {key}"
        self.session = requests.Session()

    def _request(self, method, path, params=None, json=None, prefer=None, extra_headers=None):
        headers = dict(self.headers)
        if prefer:
            headers["Prefer"] = prefer
        if extra_headers:
            headers.update(extra_headers)
        last = None
        for attempt in range(5):
            r = self.session.request(method, f"{self.url}/rest/v1/{path}", params=params,
                                     json=json, headers=headers, timeout=90)
            if r.status_code < 400:
                return r
            last = r
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            break
        raise SupaError(f"{method} {path} -> HTTP {last.status_code}: {last.text[:300]}")

    def upsert(self, table, rows, on_conflict, batch=500):
        """Bulk upsert. All rows in a batch must share the same keys."""
        n = 0
        for i in range(0, len(rows), batch):
            chunk = rows[i:i + batch]
            self._request("POST", table, params={"on_conflict": on_conflict}, json=chunk,
                          prefer="resolution=merge-duplicates,return=minimal")
            n += len(chunk)
        return n

    def select_all(self, table, params, page=1000):
        out, offset = [], 0
        while True:
            p = dict(params, limit=page, offset=offset)
            rows = self._request("GET", table, params=p).json()
            out.extend(rows)
            if len(rows) < page:
                return out
            offset += page

    def patch(self, table, params, body):
        self._request("PATCH", table, params=params, json=body, prefer="return=minimal")

    def delete(self, table, params) -> int:
        """Delete matching rows; returns how many were deleted."""
        r = self._request("DELETE", table, params=params, prefer="return=minimal,count=exact")
        return int(r.headers.get("Content-Range", "*/0").split("/")[-1] or 0)

    def count(self, table, params=None):
        r = self._request("GET", table, params=dict(params or {}, select="*", limit=1),
                          prefer="count=exact", extra_headers={"Range-Unit": "items", "Range": "0-0"})
        return int(r.headers.get("Content-Range", "*/0").split("/")[-1])
