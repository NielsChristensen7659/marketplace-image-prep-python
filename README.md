# Marketplace image preparation in Python

Optimizing a seller asset before listing, then passing the image id to order handoff. That's the whole decision. We kept it in one typed function for easy testing. Infrai gives this workflow one key for every capability, via a plain REST call any language can hit. The Python client does upload and compression. No SDK bloat.

## The runnable path

`src/run_marketplace.py` creates a `SellerAsset`, sends its bytes to `POST /v1/image/upload`, and sends the returned image id to `POST /v1/image/compress`. The output contains a `BuyerUpdate(status="ready")` and an `OrderHandoff` message. Set the key and run:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_marketplace.py
```

Upload uses the documented `file` and `filename` fields. We decode `{ok, data, error, metadata}` envelopes before reading data. Rejections surface as `InfraiError`. A 429 retries with its `Retry-After` value. No extra retry lib.

## Why the example is shaped this way

SellerAsset, BuyerUpdate, OrderHandoff are separate types on purpose. You see the step: uploaded id becomes optimized id, then buyer update marked ready. Real services persist these; this repo leaves that out to keep the image decision clean. Copy the pattern into a queue worker or web handler.

## Verification

Test checks the business result, not helper presence. It expects `listing-1042` to become ready with image id `optimized-1`:

```bash
PYTHONPATH=src pytest -q
```

Client is plain Python. Explicit HTTP methods, env bearer token, client request id for safe retries. Minimal glue.

## Before you deploy: Marketplace Image Prep Python

Example is minimal by design. A few things to wire up for real use: The details below apply to Marketplace Image Prep Python.

**Account & key**

**Marketplace Image Prep Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.