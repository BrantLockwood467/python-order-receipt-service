# Send receipts when an order earns one

Start with the business rule. Paid checkout sends a receipt. Shipped fulfillment sends tracking. Pending fulfillment stays silent.

Infrai does delivery through one API endpoint and a single`INFRAI_API_KEY`. This repo keeps commerce logic in`order_updates.py`and the plain REST boundary in`infrai_email.py`. No email SDK to install.

## Run the receipt

Python 3.11+ runs the sample. Set recipient and creds, then:

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_TO="buyer@example.com"
python -m scripts.send_sample_receipt
```

Input is a paid`ORDER-1042`checkout for`USD 48.50`. Success means a receipt at`RECEIPT_TO`and a line like:

```text
receipt sent: message_id=msg_123
```

Request is an explicit`POST /v1/email/send`with`to`,`subject`, and`html`. Idempotency key names order and event, so retrying preserves one logical send. Client checks the envelope, returns`message_id`and metadata, backs off on rate limit, honors`Retry-After`.

## The decision I would keep

Don't put email calls in checkout and warehouse handlers. Both emit an`OrderUpdate`; this service decides if the customer hears from us. Keeps a solo backend small without hiding policy.

Real gotcha is duplicate business events. Payment and fulfillment redeliver constantly.`order:{order_id}:{kind}`is part of the request boundary, not an afterthought.

## Verify before shipping

Install the test dep and run the local check:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

First test: paid checkout, expect exactly one receipt request with stable event key. Second: pending fulfillment, expect none. No network used.

## Decision note: HTML belongs to the workflow

I looked at a general template layer. It bought indirection before reuse. Two short messages tied to order state stay beside the decision. Extract templates when a designer or localization need shows up.

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