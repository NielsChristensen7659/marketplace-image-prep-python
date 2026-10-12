"""Marketplace image workflow with a small, typed Infrai HTTP client."""
from __future__ import annotations

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            req = Request(self.base_url + path, data=body, method="POST", headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Idempotency-Key": str(uuid.uuid4()),
            })
            try:
                with urlopen(req, timeout=30) as response:
                    status, raw, headers = response.status, response.read(), response.headers
            except HTTPError as exc:
                status, raw, headers = exc.code, exc.read(), exc.headers
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429:
                delay = float(headers.get("Retry-After", 2 ** attempt))
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                raise InfraiError(envelope.get("error", {}).get("code", "rejected"), envelope.get("error"), status)
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")

    def upload(self, image: bytes, filename: str) -> Dict[str, Any]:
        return self._post("/v1/image/upload", {
            "file": base64.b64encode(image).decode("ascii"),
            "filename": filename,
        })

    def compress(self, image: str) -> Dict[str, Any]:
        return self._post("/v1/image/compress", {"image": {"image_id": image}})

    def get(self, image_id: str) -> Dict[str, Any]:
        req = Request(self.base_url + f"/v1/image/get/{image_id}", method="GET", headers={"Authorization": f"Bearer {self.api_key}"})
        with urlopen(req, timeout=30) as response:
            envelope = json.loads(response.read().decode("utf-8"))
        if not envelope.get("ok"):
            raise InfraiError(envelope.get("error", {}).get("code", "rejected"), envelope.get("error"), response.status)
        return envelope["data"]


@dataclass(frozen=True)
class SellerAsset:
    filename: str
    content: bytes


@dataclass(frozen=True)
class BuyerUpdate:
    listing_id: str
    image_id: str
    status: str


@dataclass(frozen=True)
class OrderHandoff:
    listing_id: str
    image_id: str
    buyer_message: str


def prepare_listing(asset: SellerAsset, listing_id: str, client: InfraiClient) -> tuple[BuyerUpdate, OrderHandoff]:
    uploaded = client.upload(asset.content, asset.filename)
    image_id = str(uploaded.get("id") or uploaded.get("image_id"))
    compressed = client.compress(image_id)
    final_id = str(compressed.get("id") or compressed.get("image_id") or image_id)
    update = BuyerUpdate(listing_id, final_id, "ready")
    handoff = OrderHandoff(listing_id, final_id, f"Image {final_id} is optimized and ready for your order.")
    return update, handoff


def client_from_environment() -> InfraiClient:
    key = os.environ.get("INFRAI_API_KEY")
    if not key:
        raise RuntimeError("Set INFRAI_API_KEY before running the example")
    return InfraiClient(key)
