from app.tools.order_tools import get_order_status


def test_returns_existing_order() -> None:
    result = get_order_status("ORD-101")

    assert result["status"] == "success"
    assert result["order"]["order_id"] == "ORD-101"
    assert result["order"]["status"] == "shipped"


def test_normalizes_order_id() -> None:
    result = get_order_status(" ord-102 ")

    assert result["status"] == "success"
    assert result["order"]["order_id"] == "ORD-102"


def test_returns_error_for_unknown_order() -> None:
    result = get_order_status("ORD-999")

    assert result == {
        "status": "error",
        "error_message": "Order ORD-999 was not found.",
    }