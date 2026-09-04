from __future__ import annotations

import os
from decimal import Decimal

from receipt_service import OrderUpdate, OrderUpdateService, UpdateKind
from receipt_service.infrai_email import InfraiEmailClient


def main() -> None:
    client = InfraiEmailClient(os.environ["INFRAI_API_KEY"])
    service = OrderUpdateService(client)
    outcome = service.handle(
        OrderUpdate(
            order_id="ORDER-1042",
            customer_email=os.environ["RECEIPT_TO"],
            customer_name="Ada",
            kind=UpdateKind.CHECKOUT_PAID,
            total=Decimal("48.50"),
            currency="USD",
        )
    )
    print(f"receipt sent: message_id={outcome.message_id}")


if __name__ == "__main__":
    main()
