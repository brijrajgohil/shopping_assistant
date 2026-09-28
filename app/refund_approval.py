import argparse
import json

from app.tools.order_tools import ORDERS_FILE


def record_refund_decision(
    order_id: str,
    reviewer_role: str,
    decision: str,
) -> dict:
    """Record a human decision for a pending refund."""

    normalized_order_id = order_id.strip().upper()
    normalized_role = reviewer_role.strip().lower()
    normalized_decision = decision.strip().lower()

    with ORDERS_FILE.open(encoding="utf-8") as file:
        orders = json.load(file)

    for order in orders:
        if order["order_id"] != normalized_order_id:
            continue

        if order.get("refund_status") != "requested":
            return {
                "status": "blocked",
                "error_message": "No refund request is pending",
            }

        if order.get("approval_status") != "pending":
            return {
                "status": "blocked",
                "error_message": (
                    "This refund is not waiting for approval"
                ),
            }

        required_role = order.get("approval_required")

        if normalized_role != required_role:
            return {
                "status": "blocked",
                "error_message": (
                    f"This refund requires {required_role} approval"
                ),
            }

        if normalized_decision not in ["approved", "rejected"]:
            return {
                "status": "blocked",
                "error_message": (
                    "Decision must be approved or rejected"
                ),
            }

        order["approval_status"] = normalized_decision
        order["reviewed_by"] = normalized_role

        with ORDERS_FILE.open("w", encoding="utf-8") as file:
            json.dump(orders, file, indent=2)
            file.write("\n")

        return {
            "status": "success",
            "order_id": normalized_order_id,
            "reviewed_by": normalized_role,
            "approval_status": normalized_decision,
        }

    return {
        "status": "error",
        "error_message": "Order was not found",
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simulate human review of a refund request"
    )

    parser.add_argument("order_id")
    parser.add_argument(
        "reviewer_role",
        choices=["manager", "finance"],
    )
    parser.add_argument(
        "decision",
        choices=["approved", "rejected"],
    )

    args = parser.parse_args()

    result = record_refund_decision(
        order_id=args.order_id,
        reviewer_role=args.reviewer_role,
        decision=args.decision,
    )

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()