import pandas as pd

from order_to_cash.reporting import build_summary, generate_report


def make_df_reconciled():
    return pd.DataFrame({"order_id": ["ORD-1", "ORD-2"], "valid_email": [True, True]})


def make_df_exceptions():
    return pd.DataFrame(
        {
            "order_id": ["ORD-3", "ORD-4", "ORD-5"],
            "reconciliation_status": [
                "missing_payment",
                "missing_payment",
                "orphan_payment",
            ],
            "valid_email": [True, False, True],
        }
    )


def make_df_refunds():
    return pd.DataFrame(
        {
            "order_id": ["ORD-6"],
            "reconciliation_status": ["partial_refund"],
            "valid_email": [True],
        }
    )


def make_df_rejected():
    return pd.DataFrame({"order_id": ["ORD-7"], "rejection_reason": ["invalid date"]})


def make_summary_metrics():
    result = build_summary(
        make_df_reconciled(),
        make_df_exceptions(),
        make_df_refunds(),
        make_df_rejected(),
    )
    return dict(zip(result["metric"], result["count"]))


def test_build_summary_counts_rows_per_bucket():
    metrics = make_summary_metrics()
    assert metrics["reconciled_orders"] == 2
    assert metrics["exceptions_to_review"] == 3
    assert metrics["payments_refunds"] == 1
    assert metrics["rejected_rows"] == 1


def test_build_summary_breaks_down_exceptions_by_status():
    metrics = make_summary_metrics()
    assert metrics["exception_missing_payment"] == 2
    assert metrics["exception_orphan_payment"] == 1


def test_build_summary_breaks_down_refunds_by_status():
    metrics = make_summary_metrics()
    assert metrics["refund_partial_refund"] == 1


def test_generate_report_creates_all_expected_sheets(tmp_path):
    output_path = tmp_path / "report.xlsx"
    generate_report(
        make_df_reconciled(),
        make_df_exceptions(),
        make_df_refunds(),
        make_df_rejected(),
        str(output_path),
    )
    sheets = pd.read_excel(output_path, sheet_name=None)
    assert set(sheets.keys()) == {
        "summary",
        "reconciled_orders",
        "exceptions_to_review",
        "payments_refunds",
        "rejected_rows",
    }


def test_generate_report_drops_valid_email_column(tmp_path):
    output_path = tmp_path / "report.xlsx"
    generate_report(
        make_df_reconciled(),
        make_df_exceptions(),
        make_df_refunds(),
        make_df_rejected(),
        str(output_path),
    )
    sheets = pd.read_excel(output_path, sheet_name=None)
    assert "valid_email" not in sheets["reconciled_orders"].columns
    assert "valid_email" not in sheets["exceptions_to_review"].columns
    assert "valid_email" not in sheets["payments_refunds"].columns


def test_generate_report_does_not_fail_when_valid_email_column_is_absent(tmp_path):
    output_path = tmp_path / "report.xlsx"
    generate_report(
        make_df_reconciled(),
        make_df_exceptions(),
        make_df_refunds(),
        make_df_rejected(),
        str(output_path),
    )
    sheets = pd.read_excel(output_path, sheet_name=None)
    assert sheets["rejected_rows"]["order_id"].tolist() == ["ORD-7"]


def test_generate_report_writes_expected_row_counts(tmp_path):
    output_path = tmp_path / "report.xlsx"
    generate_report(
        make_df_reconciled(),
        make_df_exceptions(),
        make_df_refunds(),
        make_df_rejected(),
        str(output_path),
    )
    sheets = pd.read_excel(output_path, sheet_name=None)
    assert len(sheets["reconciled_orders"]) == 2
    assert len(sheets["exceptions_to_review"]) == 3
    assert len(sheets["payments_refunds"]) == 1
    assert len(sheets["rejected_rows"]) == 1


def test_generate_report_summary_matches_build_summary(tmp_path):
    output_path = tmp_path / "report.xlsx"
    df_reconciled = make_df_reconciled()
    df_exceptions = make_df_exceptions()
    df_refunds = make_df_refunds()
    df_rejected = make_df_rejected()
    generate_report(
        df_reconciled, df_exceptions, df_refunds, df_rejected, str(output_path)
    )
    expected_summary = build_summary(
        df_reconciled, df_exceptions, df_refunds, df_rejected
    )
    sheets = pd.read_excel(output_path, sheet_name=None)
    assert sheets["summary"]["metric"].tolist() == expected_summary["metric"].tolist()
    assert sheets["summary"]["count"].tolist() == expected_summary["count"].tolist()
