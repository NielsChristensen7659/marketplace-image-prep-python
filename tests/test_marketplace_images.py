import io
from unittest.mock import patch
from urllib.error import HTTPError

from marketplace_images import InfraiClient, SellerAsset, prepare_listing


class FakeClient:
    def upload(self, image: bytes, filename: str):
        assert filename.endswith(".jpg")
        return {"id": "uploaded-1"}

    def compress(self, image: str):
        assert image == "uploaded-1"
        return {"id": "optimized-1"}


def test_ready_image_drives_buyer_update_and_order_handoff():
    update, handoff = prepare_listing(SellerAsset("lamp.jpg", b"pixels"), "listing-1042", FakeClient())
    assert update.status == "ready"
    assert update.image_id == "optimized-1"
    assert handoff.buyer_message == "Image optimized-1 is optimized and ready for your order."


def test_rate_limit_envelope_is_retried():
    rejected = HTTPError("url", 429, "rate limited", {"Retry-After": "0"},
                         io.BytesIO(b'{"ok":false,"error":{"code":"RATE_LIMITED"}}'))

    class Response:
        status = 200
        headers = {}

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def read(self):
            return b'{"ok":true,"data":{"id":"uploaded-1"}}'

    with patch("marketplace_images.urlopen", side_effect=[rejected, Response()]) as send, \
         patch("marketplace_images.time.sleep") as sleep:
        assert InfraiClient("key").upload(b"image", "image.png")["id"] == "uploaded-1"
    assert send.call_count == 2
    sleep.assert_called_once_with(0.0)


def test_compress_uses_image_id_reference():
    client = InfraiClient("key")
    with patch.object(client, "_post", return_value={}) as send:
        client.compress("uploaded-1")
    assert send.call_args.args == ("/v1/image/compress", {"image": {"image_id": "uploaded-1"}})
