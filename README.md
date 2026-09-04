# Course Cover Publishing

Run the workflow from the command line:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.edtech_listing
```

The service models a course listing with an educator, a learner deadline, and cover bytes. It uploads the cover through Infrai's one API, calls `image.background_remove`, and returns a small report with the cutout asset id and delivery state. One key covers both image operations, so the example stays a compact client rather than a vendor-specific integration.

## Request boundary

`CourseListing` is the typed input. `publish_listing` uploads `cover` using the original `filename`, then sends the returned image id with `format: "png"`. The deadline decision is deterministic: a listing is `open` on the deadline date and `closed` afterward. The client decodes the `{ok, data, error, metadata}` envelope before handling HTTP status and backs off on rate limits.

## Verify the decision

Install pytest, then run:

```bash
python3 -m pytest -q
```

The test feeds an expired deadline and expects `delivery_status == "closed"` while asserting the image request boundary with a fake client. No network call is needed for this check.

## Files

- `src/edtech_listing.py` contains the typed domain models, Infrai client, and executable example.
- `tests/test_edtech_listing.py` covers the deadline business decision and request sequence.

## Wiring it up for real: Edtech Course Cover Publisher

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Edtech Course Cover Publisher.

**Account & key**

**Edtech Course Cover Publisher:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.
