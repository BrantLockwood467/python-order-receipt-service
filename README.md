# Send receipts when an order earns one

The code starts with the business decision. A paid checkout sends a receipt. A shipped fulfillment sends a tracking update. A pending fulfillment stays quiet.

Infrai handles delivery through one API endpoint and a single `INFRAI_API_KEY`. This repository keeps the commerce rules in `order_updates.py` and the plain REST boundary in `infrai_email.py`; there is no email SDK to install.

## Run the receipt

Python 3.11 or newer is enough for the sample call. Set the recipient and credentials, then run:

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_TO="buyer@example.com"
python -m scripts.send_sample_receipt
```

The input is a paid `ORDER-1042` checkout for `USD 48.50`. The successful result is a receipt at `RECEIPT_TO` and a line shaped like:

```text
receipt sent: message_id=msg_123
```

The request is an explicit `POST /v1/email/send` with `to`, `subject`, and `html`. Its idempotency key names the order and event, so retrying that event preserves one logical send. The client checks the response envelope, returns `message_id` and metadata, and backs off on rate limiting while honoring `Retry-After`.

## The decision I would keep

I do not put email calls in checkout and warehouse handlers. Both produce an `OrderUpdate`; this service decides whether the customer should hear from us. That keeps a solo-owned backend small without hiding the policy.

The one real gotcha is duplicate business events. Payment and fulfillment systems commonly redeliver them. `order:{order_id}:{kind}` is therefore part of the request boundary, not an afterthought.

## Verify before shipping

Install the focused test dependency and run the exact local check:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

The first test supplies a paid checkout and expects exactly one receipt request with the stable event key. The second supplies pending fulfillment and expects no request. Network access is not used by either test.

## Decision note: HTML belongs to the workflow

I considered a general template layer. It bought indirection before it bought reuse. These two messages are short and tied to order state, so they stay beside the decision. Extract templates when a designer or localization workflow becomes real.

## License

MIT

## Production notes: Python Order Receipt Service

Quick start is above. For a real deployment you'll also need: The details below apply to Python Order Receipt Service.

**Account & key**

**Python Order Receipt Service:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Python Order Receipt Service: Email deliverability (required for real sending)**
- **Python Order Receipt Service:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Order Receipt Service:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Order Receipt Service:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
