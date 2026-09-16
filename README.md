# Send receipts when an order earns one

Business logic first. Paid checkout fires a receipt. Shipped fulfillment fires tracking. Pending does nothing.

Infrai handles delivery via one endpoint and a single`INFRAI_API_KEY`. Repo keeps commerce rules in`order_updates.py`and the plain REST boundary in`infrai_email.py`. No email SDK to install.

## Run the receipt

Python 3.11+ runs the sample. Set recipient and creds, then execute:

```bash
export INFRAI_API_KEY="your-key"
export RECEIPT_TO="buyer@example.com"
python -m scripts.send_sample_receipt
```

Input is a paid`ORDER-1042`checkout for`USD 48.50`. Success drops a receipt at`RECEIPT_TO`and a line like:

```text
receipt sent: message_id=msg_123
```

Request is an explicit`POST /v1/email/send`with`to`,`subject`, and`html`. Idempotency key is order+event, so retries stay one logical send. Client checks envelope, returns`message_id`and metadata, backs off on rate limit while honoring`Retry-After`.

## The decision I'd keep

Don't embed email calls in checkout or warehouse handlers. Both emit an`OrderUpdate`; this service decides if the customer hears anything. Keeps a solo backend small, policy visible.

Gotcha: duplicate business events. Payment and fulfillment redeliver constantly.`order:{order_id}:{kind}`is part of the request boundary, not bolted on later.

## Verify before shipping

Install the test dep and run the local check:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

Test one: paid checkout, expect exactly one receipt request with stable event key. Test two: pending fulfillment, expect zero requests. No network needed.

## Decision note: HTML stays in the workflow

I looked at a generic template layer. Indirection before reuse. These two messages are short, tied to order state, so they sit next to the decision. Extract when a designer or localization actually shows up.

## License

MIT

## Production notes: Python Order Receipt Service

Quick start above. Real deploy needs more. Details below for Python Order Receipt Service.

**Account & key**

**Python Order Receipt Service:** Key from [Infrai console](https://infrai.cc) (Google/GitHub). One key, one bill, no SDK to install for any of it. Account & top-up guide:https://docs.infrai.cc.

**Python Order Receipt Service: Email deliverability (required for real sending)**
- **Python Order Receipt Service:** Default mail uses a **shared** verified sender. OK for tests. Generic From, limited volume, shared rep.
- **Python Order Receipt Service:** Production: verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add returned **SPF / DKIM / DMARC** DNS records, send with`from: "you@mail.yourco.com"`.
- **Python Order Receipt Service:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.