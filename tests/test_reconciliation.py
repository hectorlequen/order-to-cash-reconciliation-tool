import pandas as pd

from order_to_cash.reconciliation import assign_status, reconcile


def make_row(**overrides):
    row = {
        "order_id": "ORD-1",
        "order_status": "paid",
        "payment_status": "succeeded",
        "expected_amount": 100,
        "amount_paid": 100,
        "refund_id": None,
        "refund_status": None,
        "refund_amount": None,
    }
    row.update(overrides)
    return row


def test_assign_status_payment_for_rejected_order():
    row = make_row(order_id="ORD-1", order_status=None)
    assert assign_status(row, {"ORD-1"}) == "payment_for_rejected_order"


def test_assign_status_orphan_payment():
    row = make_row(order_id="ORD-2", order_status=None)
    assert assign_status(row, set()) == "orphan_payment"


def test_assign_status_full_refund():
    row = make_row(
        refund_id="REF-1",
        refund_status="succeeded",
        refund_amount=100,
        amount_paid=100,
    )
    assert assign_status(row, set()) == "full_refund"


def test_assign_status_partial_refund():
    row = make_row(
        refund_id="REF-1",
        refund_status="succeeded",
        refund_amount=50,
        amount_paid=100,
    )
    assert assign_status(row, set()) == "partial_refund"


def test_assign_status_to_refund_when_refund_not_succeeded():
    row = make_row(
        refund_id="REF-1",
        refund_status="pending",
        refund_amount=100,
        amount_paid=100,
    )
    assert assign_status(row, set()) == "to_refund"


def test_assign_status_to_refund_for_cancelled_paid_order_without_refund():
    row = make_row(order_status="cancelled", payment_status="succeeded", refund_id=None)
    assert assign_status(row, set()) == "to_refund"


def test_assign_status_order_cancelled_without_payment():
    row = make_row(order_status="cancelled", payment_status=None)
    assert assign_status(row, set()) == "order_cancelled"


def test_assign_status_reconciled():
    row = make_row(
        order_status="paid",
        payment_status="succeeded",
        expected_amount=100,
        amount_paid=100,
    )
    assert assign_status(row, set()) == "reconciled"


def test_assign_status_reconciled_with_completed_status():
    row = make_row(
        order_status="completed",
        payment_status="succeeded",
        expected_amount=100,
        amount_paid=100,
    )
    assert assign_status(row, set()) == "reconciled"


def test_assign_status_missing_payment_with_failed_status():
    row = make_row(order_status="paid", payment_status="failed")
    assert assign_status(row, set()) == "missing_payment"


def test_assign_status_missing_payment_with_no_payment():
    row = make_row(order_status="paid", payment_status=None, amount_paid=None)
    assert assign_status(row, set()) == "missing_payment"


def test_assign_status_unexpected_payment():
    row = make_row(order_status="pending", payment_status="succeeded")
    assert assign_status(row, set()) == "unexpected_payment"


def test_assign_status_awaiting_payment():
    row = make_row(order_status="pending", payment_status=None, amount_paid=None)
    assert assign_status(row, set()) == "awaiting_payment"


def test_assign_status_underpaid():
    row = make_row(
        order_status="paid",
        payment_status="succeeded",
        expected_amount=100,
        amount_paid=80,
    )
    assert assign_status(row, set()) == "underpaid"


def test_assign_status_overpaid():
    row = make_row(
        order_status="paid",
        payment_status="succeeded",
        expected_amount=100,
        amount_paid=120,
    )
    assert assign_status(row, set()) == "overpaid"


def test_assign_status_full_refund_takes_precedence_over_reconciled():
    row = make_row(
        order_status="paid",
        payment_status="succeeded",
        expected_amount=100,
        amount_paid=100,
        refund_id="REF-1",
        refund_status="succeeded",
        refund_amount=100,
    )
    assert assign_status(row, set()) == "full_refund"


def create_df_orders():
    return pd.DataFrame(
        {
            "order_id": ["ORD-1", "ORD-2", "ORD-3"],
            "customer_id": ["C1", "C2", "C3"],
            "order_status": ["paid", "paid", "pending"],
            "expected_amount": [100, 50, 30],
            "currency": ["EUR", "EUR", "EUR"],
            "payment_reference": [None, None, None],
        }
    )


def create_df_payments():
    return pd.DataFrame(
        {
            "order_id": ["ORD-1", "ORD-4"],
            "payment_status": ["succeeded", "succeeded"],
            "amount_paid": [100, 20],
            "refund_id": [None, None],
            "refund_status": [None, None],
            "refund_amount": [None, None],
            "currency": ["EUR", "EUR"],
            "payment_reference": [None, None],
        }
    )


def create_df_customers():
    return pd.DataFrame(
        {
            "customer_id": ["C1", "C2", "C3"],
            "first_name": ["Alice", "Bob", "Carol"],
        }
    )


def test_reconcile_splits_rows_by_status():
    df_reconciled, df_exceptions, df_refunds, df_rejected = reconcile(
        create_df_orders(),
        create_df_payments(),
        create_df_customers(),
        pd.DataFrame({"order_id": []}),
        pd.DataFrame({"payment_id": []}),
        pd.DataFrame({"customer_id": []}),
    )
    assert df_reconciled["order_id"].tolist() == ["ORD-1"]
    assert sorted(df_exceptions["order_id"].dropna().tolist()) == [
        "ORD-2",
        "ORD-3",
        "ORD-4",
    ]
    assert sorted(df_exceptions["reconciliation_status"].tolist()) == [
        "awaiting_payment",
        "missing_payment",
        "orphan_payment",
    ]
    assert df_refunds.empty


def test_reconcile_concatenates_rejected_rows_from_all_three_sources():
    df_orders_rejected = pd.DataFrame(
        {"order_id": ["ORD-9"], "rejection_reason": ["invalid date"]}
    )
    df_payments_rejected = pd.DataFrame(
        {"payment_id": ["PAY-9"], "rejection_reason": ["missing amount_paid"]}
    )
    df_customers_rejected = pd.DataFrame(
        {"customer_id": ["C9"], "rejection_reason": ["invalid date"]}
    )
    _, _, _, df_rejected = reconcile(
        create_df_orders(),
        create_df_payments(),
        create_df_customers(),
        df_orders_rejected,
        df_payments_rejected,
        df_customers_rejected,
    )
    assert len(df_rejected) == 3
    assert set(df_rejected["rejection_reason"]) == {
        "invalid date",
        "missing amount_paid",
    }


def test_reconcile_flags_unknown_customer():
    df_orders = pd.DataFrame(
        {
            "order_id": ["ORD-1"],
            "customer_id": ["C-UNKNOWN"],
            "order_status": ["paid"],
            "expected_amount": [100],
            "currency": ["EUR"],
            "payment_reference": [None],
        }
    )
    df_payments = pd.DataFrame(
        {
            "order_id": ["ORD-1"],
            "payment_status": ["succeeded"],
            "amount_paid": [100],
            "refund_id": [None],
            "refund_status": [None],
            "refund_amount": [None],
            "currency": ["EUR"],
            "payment_reference": [None],
        }
    )
    df_reconciled, _, _, _ = reconcile(
        df_orders,
        df_payments,
        create_df_customers(),
        pd.DataFrame({"order_id": []}),
        pd.DataFrame({"payment_id": []}),
        pd.DataFrame({"customer_id": []}),
    )
    assert df_reconciled["unknown_customer"].tolist() == [True]
