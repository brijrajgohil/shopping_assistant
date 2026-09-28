from types import SimpleNamespace
from unittest.mock import Mock

from app.callbacks import audit


def test_pending_refund_is_sent_to_bigquery(
    monkeypatch,
):
    monkeypatch.setenv(
        "BIGQUERY_REFUND_TABLE",
        "project.dataset.refund_reviews",
    )

    mock_client = Mock()
    mock_client.insert_rows_json.return_value = []

    monkeypatch.setattr(
        audit.bigquery,
        "Client",
        lambda: mock_client,
    )

    result = audit.record_pending_refund(
        tool=SimpleNamespace(name="request_refund"),
        args={},
        tool_context=SimpleNamespace(
            invocation_id="test-123",
            state={"customer_id": "CUS-001"},
        ),
        tool_response={
            "status": "success",
            "order_id": "ORD-102",
            "refund_reason": "Faulty keyboard",
            "refund_amount": 5000,
            "approval_required": "manager",
            "approval_status": "pending",
        },
    )

    assert result is None
    mock_client.insert_rows_json.assert_called_once()