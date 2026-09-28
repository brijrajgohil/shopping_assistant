import json
from pathlib import Path
from typing import Any
from google.adk.tools import ToolContext

ORDERS_FILE = Path(__file__).resolve().parents[2] / "data" / "orders.json"

def find_order(order_id: str) -> dict[str, Any] | None:
    """Find a synthetic order by its normalized ID."""
    normalized_order_id = order_id.strip().upper()
    with ORDERS_FILE.open(encoding="utf-8") as file:
        orders = json.load(file)

    for order in orders:
        if order["order_id"] == normalized_order_id:
            return order
    return None

def get_order_status(order_id: str) -> dict[str, Any]:
    """Return customer-facing shipment information for an order."""
    normalized_order_id = order_id.strip().upper()
    order = find_order(normalized_order_id)

    if order is None:
        return {
            "status": "error",
            "error_message": (
                f"Order {normalized_order_id} was not found."
            ),
        }
    # Return only information that the customer needs.
    return {
        "status": "success",
        "order": {
            "order_id": order["order_id"],
            "status": order["status"],
            "item": order["item"],
            "carrier": order["carrier"],
            "tracking_number": order["tracking_number"],
            "estimated_delivery": order["estimated_delivery"],
            "delivered_on": order["delivered_on"],
        },
    }

def request_refund(order_id: str, reason: str) -> dict[str, Any]:
    """
    Record a refund request for an order
    Args: 
        order_id: The order the customer wants refunded.
        reaons: The customer's reason for requesting a refund
    """
    normalized_order_id = order_id.strip().upper()
    with ORDERS_FILE.open(encoding="utf-8") as file:
        orders = json.load(file)

    for order in orders:
        if order["order_id"] == normalized_order_id:
            # Use the stored price, never an amount supplied by the model
            amount = order.get("price")

            if amount <= 2000:
                approval_required = "none"
                approval_status = "approved"
                message = (
                    "Refund request recorded and automatically approved, The refund has not be issued"
                )
            elif amount <= 10000:
                approval_required = "manager"
                approval_status = "pending"
                message = (
                    "Refund request recorded, manager approval is pending"
                )
            else:
                approval_required = "finance"
                approval_status = "pending"
                message = (
                    "Refund request recorded, Finance approval is pending"
                )

            refund_details = {
                "refund_status": "requested",
                "refund_reason": reason.strip(),
                "refund_amount": amount,
                "approval_required": approval_required,
                "approval_status": approval_status
            }
            order.update(refund_details)

            with ORDERS_FILE.open("w", encoding="utf-8") as file:
                json.dump(orders, file, indent=2)
                file.write("\n")

            return {
                "status": "success",
                "order_id": normalized_order_id,
                **refund_details,
                "message": message
            }
    return {
        "status": "error",
        "error_message": "Order was not found."
    }