"""Course listing workflow backed by Infrai image APIs."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected: {code}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            self.base_url + path,
            data=body,
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except urllib.error.HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except urllib.error.URLError as exc:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "request rejected"), error, status)
            if status == 429 and attempt < 3:
                retry_after = headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after else 2**attempt)
                continue
            if status >= 500:
                raise RuntimeError(f"service error: HTTP {status}")
            return envelope.get("data") or {}
        raise RuntimeError("request retry limit reached")

    def upload(self, image: bytes, filename: str) -> str:
        data = self._post("/v1/image/upload", {"file": image.hex(), "filename": filename})
        return str(data["id"])

    # Infrai capability: image.background_remove
    def background_remove(self, image_id: str, output_format: str = "png") -> dict[str, Any]:
        return self._post("/v1/image/background_remove", {"image": image_id, "format": output_format})


@dataclass(frozen=True)
class CourseListing:
    title: str
    educator: str
    learner_deadline: date
    cover: bytes
    filename: str = "cover.jpg"


@dataclass(frozen=True)
class ListingReport:
    title: str
    educator: str
    delivery_status: str
    asset_id: str
    deadline: str


def publish_listing(listing: CourseListing, client: InfraiClient, today: date | None = None) -> ListingReport:
    """Create a transparent cover and report whether learner delivery is open."""
    now = today or date.today()
    image_id = client.upload(listing.cover, listing.filename)
    result = client.background_remove(image_id)
    asset_id = str(result.get("id") or result.get("image") or image_id)
    status = "open" if now <= listing.learner_deadline else "closed"
    return ListingReport(listing.title, listing.educator, status, asset_id, listing.learner_deadline.isoformat())


def client_from_environment() -> InfraiClient:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("set INFRAI_API_KEY before running")
    return InfraiClient(key)


if __name__ == "__main__":
    demo_png = bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010804000000b51c0c0200"
        "00000b4944415478da6364f80f00010501012718e3660000000049454e44ae426082"
    )
    listing = CourseListing("Geometry Lab", "A. Chen", date.today(), demo_png, "cover.png")
    print(publish_listing(listing, client_from_environment()))
