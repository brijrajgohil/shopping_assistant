import json
from datetime import date
from types import SimpleNamespace

from app.callbacks.security import check_order_access
from app.tools import order_tools


def create_test_order(tmp_path, monkeypatch, **changes):
    """
    Create a temporary orders.json containing one eligible order.

    Individual tests can change fields such as customer_id, status,
    or refund_status.
    """
    order = {
        "order_id": "ORD-TEST",
        "customer_id": "CUS-001",
        "status": "delivered",
        "item": "Mechanical Keyboard",
        "price": 5000,
        "currency": "INR",
        "carrier": "Delhivery",
        "tracking_number": "TEST-TRACKING",
        "estimated_delivery": None,
        "delivered_on": date.today().isoformat(),
        "refund_status": "none",
    }

    order.update(changes)

    test_orders_file = tmp_path / "orders.json"
    test_orders_file.write_text(
        json.dumps([order], indent=2),
        encoding="utf-8",
    )

    # Make your existing tools use the temporary file during this test.
    monkeypatch.setattr(
        order_tools,
        "ORDERS_FILE",
        test_orders_file,
    )

    return test_orders_file


def run_refund_security_check(
    customer_id="CUS-001",
    reason="Keyboard is faulty",
):
    """
    Run the existing before_tool callback as if ADK were calling
    request_refund.
    """
    tool = SimpleNamespace(name="request_refund")

    args = {
        "order_id": "ORD-TEST",
        "reason": reason,
    }

    tool_context = SimpleNamespace(
        state={"customer_id": customer_id}
    )

    return check_order_access(
        tool=tool,
        args=args,
        tool_context=tool_context,
    )


def test_eligible_refund_request_is_recorded(
    tmp_path,
    monkeypatch,
):
    test_orders_file = create_test_order(
        tmp_path,
        monkeypatch,
        price=5000,
    )

    # The callback returns None when the tool is allowed to execute.
    security_result = run_refund_security_check()

    assert security_result is None

    # Since security allowed the request, execute the tool.
    result = order_tools.request_refund(
        order_id="ORD-TEST",
        reason="Keyboard is faulty",
    )

    assert result["status"] == "success"
    assert result["refund_status"] == "requested"
    assert result["refund_reason"] == "Keyboard is faulty"
    assert result["refund_amount"] == 5000
    assert result["approval_required"] == "manager"
    assert result["approval_status"] == "pending"

    # Read the temporary file again to prove the changes were saved.
    saved_orders = json.loads(
        test_orders_file.read_text(encoding="utf-8")
    )
    saved_order = saved_orders[0]

    assert saved_order["refund_status"] == "requested"
    assert saved_order["refund_reason"] == "Keyboard is faulty"
    assert saved_order["refund_amount"] == 5000
    assert saved_order["approval_required"] == "manager"
    assert saved_order["approval_status"] == "pending"


def test_refund_for_another_customers_order_is_blocked(
    tmp_path,
    monkeypatch,
):
    create_test_order(tmp_path, monkeypatch)

    result = run_refund_security_check(
        customer_id="CUS-002",
    )

    assert result == {
        "status": "blocked",
        "error_message": (
            "This order is not available for this customer"
        ),
    }


def test_refund_without_reason_is_blocked(
    tmp_path,
    monkeypatch,
):
    create_test_order(tmp_path, monkeypatch)

    result = run_refund_security_check(reason="")

    assert result == {
        "status": "blocked",
        "error_message": "A refund reason is required",
    }


def test_refund_for_undelivered_order_is_blocked(
    tmp_path,
    monkeypatch,
):
    create_test_order(
        tmp_path,
        monkeypatch,
        status="shipped",
        delivered_on=None,
    )

    result = run_refund_security_check()

    assert result == {
        "status": "blocked",
        "error_message": (
            "Refund requests require a delivered order"
        ),
    }


def test_duplicate_refund_request_is_blocked(
    tmp_path,
    monkeypatch,
):
    create_test_order(
        tmp_path,
        monkeypatch,
        refund_status="requested",
    )

    result = run_refund_security_check()

    assert result == {
        "status": "blocked",
        "error_message": (
            "This order already has a refund request"
        ),
    }