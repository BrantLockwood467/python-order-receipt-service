from decimal import Decimal

from receipt_service import OrderUpdate, OrderUpdateService, UpdateKind
from receipt_service.infrai_email import SendResult


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[dict[str, str]] = []

    def send(self, **request: str) -> SendResult:
        self.calls.append(request)
        return SendResult("msg_receipt_1042", {"vendor": "mail-provider"})


def order(kind: UpdateKind) -> OrderUpdate:
    return OrderUpdate(
        order_id="ORDER-1042",
        customer_email="buyer@example.com",
        customer_name="Ada",
        kind=kind,
        total=Decimal("48.50"),
        currency="usd",
    )


def test_paid_checkout_sends_one_receipt_with_stable_event_key() -> None:
    sender = RecordingSender()

    outcome = OrderUpdateService(sender).handle(order(UpdateKind.CHECKOUT_PAID))

    assert outcome.message_id == "msg_receipt_1042"
    assert sender.calls == [
        {
            "to": "buyer@example.com",
            "subject": "Receipt for order ORDER-1042",
            "html": "<h1>Thanks, Ada</h1><p>We received your payment of <strong>USD 48.50</strong> for order ORDER-1042.</p>",
            "idempotency_key": "order:ORDER-1042:checkout_paid",
        }
    ]


def test_pending_fulfillment_does_not_email_customer() -> None:
    sender = RecordingSender()

    outcome = OrderUpdateService(sender).handle(order(UpdateKind.FULFILLMENT_PENDING))

    assert outcome.sent is False
    assert sender.calls == []
