from google.adk.tools import BaseTool, ToolContext
from app.tools.order_tools import find_order
from datetime import date

def check_order_access(
    tool: BaseTool,
    args: dict,
    tool_context: ToolContext
) -> dict | None:
    # This guardrail applies only to the order-status tool
    if tool.name not in ["get_order_status", "request_refund"]:
        return None

    customer_id = tool_context.state.get("customer_id")
    if not isinstance(customer_id, str) or not customer_id.strip():
        return {
            "status": "blocked",
            "error_message": "Customer identity is unavailable"
        }
    order_id = args.get("order_id")
    if not isinstance(order_id, str) or not order_id.strip():
        return {
            "status": "blocked",
            "error_message": "A valid order ID is required"
        }
    order = find_order(order_id)
    if order is None or order.get("customer_id") != customer_id:
        return {
            "status": "blocked",
            "error_message": "This order is not available for this customer"
        }

    # Additional checks apply only to refund request
    if tool.name == "request_refund":
        reason = args.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            return {
                "status": "blocked",
                "error_message": "A refund reason is required"
            }
        if order.get("refund_status") != "none":
            return {
                "status": "blocked",
                "error_message": "This order already has a refund request"
            }
        if order.get("status") != "delivered":
            return {
                "status": "blocked",
                "error_message": "Refund requests require a delivered order"
            }
        try:
            delivered_on = date.fromisoformat(order["delivered_on"])
        except (KeyError, TypeError, ValueError):
            return {
                "status": "blocked",
                "error_message": "Delivery date could not be verified"
            }
        days_since_delivery = (date.today() - delivered_on).days
        if not 0 <= days_since_delivery <= 30:
            return {
                "status": "blocked",
                "error_message": "This order is outsied the 30-day window"
            }

    return None