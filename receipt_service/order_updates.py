"""Checkout and fulfillment decisions expressed as customer email updates."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from html import escape
from typing import Protocol

from .infrai_email import SendResult


class UpdateKind(str, Enum):
    CHECKOUT_PAID = "checkout_paid"
    FULFILLMENT_SHIPPED = "fulfillment_shipped"
    FULFILLMENT_PENDING = "fulfillment_pending"


@dataclass(frozen=True)
class OrderUpdate:
    order_id: str
    customer_email: str
    customer_name: str
    kind: UpdateKind
    total: Decimal
    currency: str
    tracking_url: str | None = None


@dataclass(frozen=True)
class UpdateOutcome:
    sent: bool
    message_id: str | None
    reason: str


class EmailSender(Protocol):
    def send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> SendResult: ...


class OrderUpdateService:
    def __init__(self, email: EmailSender) -> None:
        self._email = email

    def handle(self, update: OrderUpdate) -> UpdateOutcome:
        message = self._message_for(update)
        if message is None:
            return UpdateOutcome(False, None, "pending fulfillment has no customer update")

        subject, html = message
        result = self._email.send(
            to=update.customer_email,
            subject=subject,
            html=html,
            idempotency_key=f"order:{update.order_id}:{update.kind.value}",
        )
        return UpdateOutcome(True, result.message_id, "customer update sent")

    @staticmethod
    def _message_for(update: OrderUpdate) -> tuple[str, str] | None:
        order_id = escape(update.order_id)
        name = escape(update.customer_name)
        if update.kind is UpdateKind.CHECKOUT_PAID:
            amount = f"{update.currency.upper()} {update.total:.2f}"
            return (
                f"Receipt for order {update.order_id}",
                f"<h1>Thanks, {name}</h1><p>We received your payment of "
                f"<strong>{escape(amount)}</strong> for order {order_id}.</p>",
            )
        if update.kind is UpdateKind.FULFILLMENT_SHIPPED:
            tracking = (
                f'<p><a href="{escape(update.tracking_url, quote=True)}">Track this shipment</a></p>'
                if update.tracking_url
                else ""
            )
            return (
                f"Order {update.order_id} has shipped",
                f"<h1>Your order is moving, {name}</h1>"
                f"<p>Order {order_id} has left our fulfillment center.</p>{tracking}",
            )
        return None
