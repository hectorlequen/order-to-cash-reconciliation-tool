import pandas as pd


def generate_report(
    df_reconciled: pd.DataFrame,
    df_exceptions: pd.DataFrame,
    df_refunds: pd.DataFrame,
    df_rejected: pd.DataFrame,
    output_path: str,
) -> None:
    df_summary = build_summary(df_reconciled, df_exceptions, df_refunds, df_rejected)
    df_reconciled = df_reconciled.drop(columns=["valid_email"], errors="ignore")
    df_exceptions = df_exceptions.drop(columns=["valid_email"], errors="ignore")
    df_refunds = df_refunds.drop(columns=["valid_email"], errors="ignore")
    df_rejected = df_rejected.drop(columns=["valid_email"], errors="ignore")
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="summary", index=False)
        df_reconciled.to_excel(writer, sheet_name="reconciled_orders", index=False)
        df_exceptions.to_excel(writer, sheet_name="exceptions_to_review", index=False)
        df_refunds.to_excel(writer, sheet_name="payments_refunds", index=False)
        df_rejected.to_excel(writer, sheet_name="rejected_rows", index=False)


def build_summary(
    df_reconciled: pd.DataFrame,
    df_exceptions: pd.DataFrame,
    df_refunds: pd.DataFrame,
    df_rejected: pd.DataFrame,
) -> pd.DataFrame:
    rows = [
        {"metric": "reconciled_orders", "count": len(df_reconciled)},
        {"metric": "exceptions_to_review", "count": len(df_exceptions)},
        {"metric": "payments_refunds", "count": len(df_refunds)},
        {"metric": "rejected_rows", "count": len(df_rejected)},
    ]
    for status, count in df_exceptions["reconciliation_status"].value_counts().items():
        rows.append({"metric": f"exception_{status}", "count": count})
    for status, count in df_refunds["reconciliation_status"].value_counts().items():
        rows.append({"metric": f"refund_{status}", "count": count})
    return pd.DataFrame(rows)
