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
    if pd.isna(row["order_status"]) and row["order_id"] in rejected_order_ids:
        return "payment_for_rejected_order"
    elif pd.isna(row["order_status"]):
        return "orphan_payment"
    elif (
        not pd.isna(row["refund_id"])
        and row["refund_status"] == "succeeded"
        and row["refund_amount"] == row["amount_paid"]
    ):
        return "full_refund"
    elif (
        not pd.isna(row["refund_id"])
        and row["refund_status"] == "succeeded"
        and row["refund_amount"] < row["amount_paid"]
    ):
        return "partial_refund"
    elif not pd.isna(row["refund_id"]) and row["refund_status"] != "succeeded":
        return "to_refund"
    elif (
        row["order_status"] == "cancelled"
        and row["payment_status"] == "succeeded"
        and pd.isna(row["refund_id"])
    ):
        return "to_refund"
    elif row["order_status"] == "cancelled" and pd.isna(row["payment_status"]):
        return "order_cancelled"
    elif (
        row["order_status"] in ("paid", "completed")
        and row["payment_status"] == "succeeded"
        and row["expected_amount"] == row["amount_paid"]
    ):
        return "reconciled"
    elif row["order_status"] in ("paid", "completed") and (
        row["payment_status"] == "failed" or pd.isna(row["payment_status"])
    ):
        return "missing_payment"
    elif (
        row["order_status"] not in ("paid", "completed", "cancelled")
        and row["payment_status"] == "succeeded"
    ):
        return "unexpected_payment"
    elif row["order_status"] not in (
        "paid",
        "completed",
        "cancelled",
    ) and pd.isna(row["payment_status"]):
        return "awaiting_payment"
    elif (
        row["order_status"] in ("paid", "completed")
        and row["expected_amount"] > row["amount_paid"]
    ):
        return "underpaid"
    elif (
        row["order_status"] in ("paid", "completed")
        and row["expected_amount"] < row["amount_paid"]
    ):
        return "overpaid"
