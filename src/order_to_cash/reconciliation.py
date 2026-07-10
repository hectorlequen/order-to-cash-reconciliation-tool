import pandas as pd

EXCEPTION_STATUSES = [
    "missing_payment",
    "unexpected_payment",
    "awaiting_payment",
    "underpaid",
    "overpaid",
    "orphan_payment",
    "payment_for_rejected_order",
    "to_refund",
    "order_cancelled",
]

REFUND_STATUSES = ["full_refund", "partial_refund"]

PAID_ORDER_STATUSES = ("paid", "completed")


def reconcile(
    df_orders: pd.DataFrame,
    df_payments: pd.DataFrame,
    df_customers: pd.DataFrame,
    df_orders_rejected: pd.DataFrame,
    df_payments_rejected: pd.DataFrame,
    df_customers_rejected: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_merged = pd.merge(df_orders, df_payments, on="order_id", how="outer")
    df_merged["currency"] = df_merged["currency_x"].fillna(df_merged["currency_y"])
    df_merged = df_merged.drop(columns=["currency_x", "currency_y"])
    df_merged["payment_reference"] = df_merged["payment_reference_x"].fillna(
        df_merged["payment_reference_y"]
    )
    df_merged = df_merged.drop(columns=["payment_reference_x", "payment_reference_y"])
    rejected_order_ids = set(df_orders_rejected["order_id"].dropna())
    df_merged["reconciliation_status"] = df_merged.apply(
        lambda row: assign_status(row, rejected_order_ids), axis=1
    )
    df_merged = pd.merge(df_merged, df_customers, on="customer_id", how="left")
    df_merged["unknown_customer"] = (
        df_merged["first_name"].isna() & df_merged["customer_id"].notna()
    )

    df_reconciled = df_merged[df_merged["reconciliation_status"] == "reconciled"]
    df_exceptions = df_merged[
        df_merged["reconciliation_status"].isin(EXCEPTION_STATUSES)
    ]
    df_refunds = df_merged[df_merged["reconciliation_status"].isin(REFUND_STATUSES)]
    df_rejected = pd.concat(
        [df_orders_rejected, df_payments_rejected, df_customers_rejected],
        ignore_index=True,
    )

    return df_reconciled, df_exceptions, df_refunds, df_rejected


def assign_status(row, rejected_order_ids: set) -> str:
    if _is_rejected_order_payment(row, rejected_order_ids):
        return "payment_for_rejected_order"
    elif _has_no_order(row):
        return "orphan_payment"
    elif _is_full_refund(row):
        return "full_refund"
    elif _is_partial_refund(row):
        return "partial_refund"
    elif _has_pending_refund(row):
        return "to_refund"
    elif _is_cancelled_awaiting_refund(row):
        return "to_refund"
    elif _is_cancelled_without_payment(row):
        return "order_cancelled"
    elif _is_paid_order(row) and _has_succeeded_payment(row) and _amounts_match(row):
        return "reconciled"
    elif _is_paid_order(row) and (_has_failed_payment(row) or _has_no_payment(row)):
        return "missing_payment"
    elif _is_open_order(row) and _has_succeeded_payment(row):
        return "unexpected_payment"
    elif _is_open_order(row) and _has_no_payment(row):
        return "awaiting_payment"
    elif _is_paid_order(row) and _is_underpaid(row):
        return "underpaid"
    elif _is_paid_order(row) and _is_overpaid(row):
        return "overpaid"


def _has_no_order(row) -> bool:
    return pd.isna(row["order_status"])


def _is_rejected_order_payment(row, rejected_order_ids: set) -> bool:
    return _has_no_order(row) and row["order_id"] in rejected_order_ids


def _has_succeeded_refund(row) -> bool:
    return not pd.isna(row["refund_id"]) and row["refund_status"] == "succeeded"


def _has_pending_refund(row) -> bool:
    return not pd.isna(row["refund_id"]) and row["refund_status"] != "succeeded"


def _is_full_refund(row) -> bool:
    return _has_succeeded_refund(row) and row["refund_amount"] == row["amount_paid"]


def _is_partial_refund(row) -> bool:
    return _has_succeeded_refund(row) and row["refund_amount"] < row["amount_paid"]


def _is_cancelled_awaiting_refund(row) -> bool:
    return (
        row["order_status"] == "cancelled"
        and row["payment_status"] == "succeeded"
        and pd.isna(row["refund_id"])
    )


def _is_cancelled_without_payment(row) -> bool:
    return row["order_status"] == "cancelled" and pd.isna(row["payment_status"])


def _is_paid_order(row) -> bool:
    return row["order_status"] in PAID_ORDER_STATUSES


def _is_open_order(row) -> bool:
    return row["order_status"] not in (*PAID_ORDER_STATUSES, "cancelled")


def _has_succeeded_payment(row) -> bool:
    return row["payment_status"] == "succeeded"


def _has_failed_payment(row) -> bool:
    return row["payment_status"] == "failed"


def _has_no_payment(row) -> bool:
    return pd.isna(row["payment_status"])


def _amounts_match(row) -> bool:
    return row["expected_amount"] == row["amount_paid"]


def _is_underpaid(row) -> bool:
    return row["expected_amount"] > row["amount_paid"]


def _is_overpaid(row) -> bool:
    return row["expected_amount"] < row["amount_paid"]
