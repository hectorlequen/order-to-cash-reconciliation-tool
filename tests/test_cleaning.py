import pandas as pd

from order_to_cash.cleaning import (
    is_valid_date,
    normalize_column_lowercase,
    normalize_missing_values,
    remove_duplicates,
    trim_spaces,
)


def test_is_valid_date_with_valid_date():
    assert is_valid_date("1789-07-14")


def test_is_valid_date_with_invalid_string():
    assert not is_valid_date("hello world")


def test_is_valid_date_with_invalid_date():
    assert not is_valid_date("2026-30-30")


def test_is_valid_date_with_nan():
    assert not is_valid_date(float("nan"))


def test_is_valid_date_with_none():
    assert not is_valid_date(None)


def test_normalize_column_lowercase_lowercases_strings():
    df = pd.DataFrame({"status": ["PAID", "Refunded", "failed"]})
    result = normalize_column_lowercase(df, "status")
    assert result["status"].tolist() == ["paid", "refunded", "failed"]


def test_normalize_column_lowercase_ignores_non_string_values():
    df = pd.DataFrame({"status": ["PAID", None, 42]})
    result = normalize_column_lowercase(df, "status")
    assert result["status"].tolist() == ["paid", None, 42]


def test_normalize_column_lowercase_does_not_affect_other_columns():
    df = pd.DataFrame({"status": ["PAID"], "product": ["MUG"]})
    result = normalize_column_lowercase(df, "status")
    assert result["product"].tolist() == ["MUG"]


def test_trim_spaces_strips_leading_and_trailing_spaces():
    df = pd.DataFrame({"product": ["  mug  ", "cup ", " plate"]})
    result = trim_spaces(df, "product")
    assert result["product"].tolist() == ["mug", "cup", "plate"]


def test_trim_spaces_ignores_non_string_values():
    df = pd.DataFrame({"product": ["  mug  ", None, 42]})
    result = trim_spaces(df, "product")
    assert result["product"].tolist() == ["mug", None, 42]


def test_trim_spaces_does_not_affect_other_columns():
    df = pd.DataFrame({"product": ["  mug  "], "category": [" home "]})
    result = trim_spaces(df, "product")
    assert result["category"].tolist() == [" home "]


def test_normalize_missing_values_replaces_empty_strings_with_none():
    df = pd.DataFrame({"product": ["mug", ""], "category": ["", "kitchen"]})
    result = normalize_missing_values(df)
    assert result["product"].tolist()[0] == "mug"
    assert pd.isna(result["product"].tolist()[1])
    assert pd.isna(result["category"].tolist()[0])
    assert result["category"].tolist()[1] == "kitchen"


def test_normalize_missing_values_leaves_other_values_unchanged():
    df = pd.DataFrame({"product": ["mug", "cup"], "quantity": [1, 2]})
    result = normalize_missing_values(df)
    assert result["product"].tolist() == ["mug", "cup"]
    assert result["quantity"].tolist() == [1, 2]


def test_remove_duplicates_drops_duplicate_rows_keeping_first():
    df = pd.DataFrame(
        {"order_id": ["A1", "A1", "A2"], "product": ["mug", "cup", "plate"]}
    )
    result = remove_duplicates(df, "order_id")
    assert result["order_id"].tolist() == ["A1", "A2"]
    assert result["product"].tolist() == ["mug", "plate"]


def test_remove_duplicates_keeps_unique_rows_unchanged():
    df = pd.DataFrame({"order_id": ["A1", "A2", "A3"]})
    result = remove_duplicates(df, "order_id")
    assert result["order_id"].tolist() == ["A1", "A2", "A3"]
