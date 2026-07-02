import pandas as pd
import pytest
import requests

from order_to_cash.cleaning import (
    get_exchange_rate,
    is_valid_date,
    normalize_column_lowercase,
    normalize_missing_values,
    remove_duplicates,
    trim_spaces,
    validate_df,
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


def test_validate_df_with_all_valid_rows_returns_everything_in_valid():
    df = pd.DataFrame(
        {
            "order_id": ["A1", "A2"],
            "order_date": ["2026-01-01", "2026-01-02"],
            "expected_amount": [10, 20],
        }
    )
    df_valid, df_rejected = validate_df(
        df, "order_date", ["order_id", "expected_amount"]
    )
    assert df_valid.equals(df)
    assert df_rejected.empty


def test_validate_df_with_invalid_date_rejects_row_with_reason():
    df = pd.DataFrame(
        {
            "order_id": ["A1"],
            "order_date": ["not a date"],
            "expected_amount": [10],
        }
    )
    df_valid, df_rejected = validate_df(
        df, "order_date", ["order_id", "expected_amount"]
    )
    assert df_valid.empty
    assert df_rejected["rejection_reason"].tolist() == ["invalid date"]


def test_validate_df_with_missing_critical_field_rejects_row_with_reason():
    df = pd.DataFrame(
        {
            "order_id": ["A1"],
            "order_date": ["2026-01-01"],
            "expected_amount": [None],
        }
    )
    df_valid, df_rejected = validate_df(
        df, "order_date", ["order_id", "expected_amount"]
    )
    assert df_valid.empty
    assert df_rejected["rejection_reason"].tolist() == ["missing expected_amount"]


def test_validate_df_with_invalid_date_and_missing_field_rejects_with_both_reasons():
    df = pd.DataFrame(
        {
            "order_id": ["A1"],
            "order_date": ["not a date"],
            "expected_amount": [None],
        }
    )
    df_valid, df_rejected = validate_df(
        df, "order_date", ["order_id", "expected_amount"]
    )
    assert df_valid.empty
    assert df_rejected["rejection_reason"].tolist() == [
        "invalid date, missing expected_amount"
    ]


def test_validate_df_with_mix_of_valid_and_invalid_rows():
    df = pd.DataFrame(
        {
            "order_id": ["A1", "A2", "A3"],
            "order_date": ["2026-01-01", "not a date", "2026-01-03"],
            "expected_amount": [10, 20, None],
        }
    )
    df_valid, df_rejected = validate_df(
        df, "order_date", ["order_id", "expected_amount"]
    )
    assert df_valid["order_id"].tolist() == ["A1"]
    assert df_rejected["order_id"].tolist() == ["A2", "A3"]
    assert df_rejected["rejection_reason"].tolist() == [
        "invalid date",
        "missing expected_amount",
    ]


class FakeResponse:
    def raise_for_status(self):
        pass

    def json(self):
        return {"rates": {"USD": 1}}


def test_get_exchange_rate_ok(monkeypatch):
    def fake_get(*args, **kwargs):
        return FakeResponse()

    monkeypatch.setattr("order_to_cash.cleaning.requests.get", fake_get)
    assert get_exchange_rate("EUR", "USD") == 1


def test_get_exchange_rate_timeout(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.Timeout()

    monkeypatch.setattr("order_to_cash.cleaning.requests.get", fake_get)
    with pytest.raises(requests.Timeout):
        get_exchange_rate("EUR", "USD")


def test_get_exchange_rate_http_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.HTTPError()

    monkeypatch.setattr("order_to_cash.cleaning.requests.get", fake_get)
    with pytest.raises(requests.HTTPError):
        get_exchange_rate("EUR", "USD")


def test_get_exchange_rate_request_exception(monkeypatch):
    def fake_get(*args, **kwargs):
        raise requests.RequestException()

    monkeypatch.setattr("order_to_cash.cleaning.requests.get", fake_get)
    with pytest.raises(requests.RequestException):
        get_exchange_rate("EUR", "USD")


def test_get_exchange_rate_key_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise KeyError

    monkeypatch.setattr("order_to_cash.cleaning.requests.get", fake_get)
    with pytest.raises(KeyError):
        get_exchange_rate("EUR", "USD")


def test_get_exchange_rate_value_error(monkeypatch):
    def fake_get(*args, **kwargs):
        raise ValueError

    monkeypatch.setattr("order_to_cash.cleaning.requests.get", fake_get)
    with pytest.raises(ValueError):
        get_exchange_rate("EUR", "USD")
