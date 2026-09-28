import logging
import os
from datetime import datetime, timezone
from typing import Any

from google.adk.tools import BaseTool, ToolContext
from google.cloud import bigquery

logger = logging.getLogger(__name__)

def record_pending_refund(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    tool_response: dict[str, Any],
) -> dict[str, Any] | None:
    """Add pendind refund requests to the manager's BigQuery queue"""
    if tool.name != "request_refund":
        return None
    if tool_response.get("status") != "success":
        return None
    if tool_response.get("approval_status") != "pending":
        return None
    table_id = os.environ.get("BIGQUERY_REFUND_TABLE")
    if not table_id:
        logger.warning("BIGQUERY_REFUND_TABLE is not configured")
        return None

    order_id = tool_response["order_id"]
    invocation_id = tool_context.invocation_id
    event_id = f"{invocation_id}:{order_id}"

    row = {
        "event_id": event_id,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "order_id": order_id,
        "customer_id": tool_context.state.get("customer_id"),
        "refund_reason": tool_response["refund_reason"],
        "refund_amount": tool_response["refund_amount"],
        "currency": "INR",
        "approval_required": tool_response["approval_required"],
        "approval_status": tool_response["approval_status"],
    }

    try:
        client = bigquery.Client()
        errors = client.insert_rows_json(
            table_id,
            [row],
            row_ids=[event_id]
        )
        if errors:
            logger.error(
                "BigQuery rejected refund event %s: %s",
                event_id,
                errors,
            )
    except Exception:
        logger.exception(
            "Could not write event %s to BigQuery",
            event_id
        )
    return None