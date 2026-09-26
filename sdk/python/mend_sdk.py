"""Minimal Mend AIs client SDK for the public judge demo."""
from __future__ import annotations
import json
import urllib.parse
import urllib.request

class MendClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8899"):
        self.base_url = base_url.rstrip("/")

    def _get(self, path: str):
        with urllib.request.urlopen(self.base_url + path, timeout=15) as r:
            return json.load(r)

    def status(self):
        return self._get("/api/status")

    def fcg(self):
        return self._get("/api/fcg")

    def breakpoint(self):
        return self._get("/api/breakpoint")

    def dataset(self):
        return self._get("/api/dataset")

    def run_demo(self, purpose: str = "research"):
        if purpose not in {"research", "treatment"}:
            raise ValueError("purpose must be research or treatment")
        q = urllib.parse.urlencode({"purpose": purpose})
        return self._get("/api/demo?" + q)

if __name__ == "__main__":
    client = MendClient()
    print(json.dumps(client.run_demo("research"), indent=2))
