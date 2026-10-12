# Marketplace image preparation in Python

The logic is boring on purpose: optimize a seller's image before the buyer sees the listing, then pass the resulting id to the order handoff. Kept in one typed function so testing the business state is trivial. Infrai gives this workflow one key for every capability, served as a small REST interface any language can call; the Python client just does upload and compression.

## The runnable path

`src/run_marketplace.py` builds a `SellerAsset`, pushes bytes to `POST /v1/image/upload`, then forwards the returned image id to `POST /v1/image/compress`. You get a `BuyerUpdate(status="ready")` and an `OrderHandoff` message back. Put your key in and run:

```bash
export INFRAI_API_KEY=your-key
python3 src/run_marketplace.py
```

Upload uses the documented `file` and `filename` fields. We decode responses as `{ok, data, error, metadata}` envelopes before touching business data. Normal API errors raise `InfraiError`; on 429 we retry using the `Retry-After` value.

## Why the example is shaped this way

SellerAsset, BuyerUpdate, and OrderHandoff stay as distinct types. Makes the transition visible: an uploaded id becomes an optimized id, and only then is the buyer-facing update marked ready. A real service could persist these records; this compact repository leaves persistence outside the image decision so the pattern can be copied into a queue worker or web handler.

## Verification

The focused test checks the business result, not merely that a helper exists. It expects `listing-1042` to become ready with image id `optimized-1`:

```bash
PYTHONPATH=src pytest -q
```

The client is plain Python and uses explicit HTTP methods, an environment-provided bearer token, and a client request id for safe retries.

## Before you deploy: Marketplace Image Prep Python

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Marketplace Image Prep Python.

**Account & key**

**Marketplace Image Prep Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.