from unittest.mock import MagicMock

import pandas as pd
import pytest
import requests

from order_to_cash.cleaning import (
    get_exchange_rate,
    is_valid_date,
    normalize_column_capitalize,
    normalize_column_lowercase,
    normalize_column_uppercase,
    normalize_country,
    normalize_country_column,
    normalize_currency,
    normalize_missing_values,
    remove_duplicates,
    round_columns,
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


def test_normalize_column_uppercase_uppercases_strings():
    df = pd.DataFrame({"currency": ["eur", "Usd", "GBP"]})
    result = normalize_column_uppercase(df, "currency")
    assert result["currency"].tolist() == ["EUR", "USD", "GBP"]


def test_normalize_column_uppercase_ignores_non_string_values():
    df = pd.DataFrame({"currency": ["eur", None, 42]})
    result = normalize_column_uppercase(df, "currency")
    assert result["currency"].tolist() == ["EUR", None, 42]


def test_normalize_column_uppercase_does_not_affect_other_columns():
    df = pd.DataFrame({"currency": ["eur"], "product": ["mug"]})
    result = normalize_column_uppercase(df, "currency")
    assert result["product"].tolist() == ["mug"]


def test_normalize_column_capitalize_capitalizes_strings():
    df = pd.DataFrame({"first_name": ["JOHN", "jane", "aLiCe"]})
    result = normalize_column_capitalize(df, "first_name")
    assert result["first_name"].tolist() == ["John", "Jane", "Alice"]


def test_normalize_column_capitalize_ignores_non_string_values():
    df = pd.DataFrame({"first_name": ["JOHN", None, 42]})
    result = normalize_column_capitalize(df, "first_name")
    assert result["first_name"].tolist() == ["John", None, 42]


def test_normalize_column_capitalize_does_not_affect_other_columns():
    df = pd.DataFrame({"first_name": ["JOHN"], "last_name": ["DOE"]})
    result = normalize_column_capitalize(df, "first_name")
    assert result["last_name"].tolist() == ["DOE"]


def test_trim_spaces_strips_leading_and_trailing_spaces():
    df = pd.DataFrame({"product": ["  mug  ", "cup ", " plate"]})
    result = trim_spaces(df)
    assert result["product"].tolist() == ["mug", "cup", "plate"]


def test_trim_spaces_ignores_non_string_values():
    df = pd.DataFrame({"product": ["  mug  ", None, 42]})
    result = trim_spaces(df)
    assert result["product"].tolist() == ["mug", None, 42]


def test_trim_spaces_trims_every_column_containing_at_least_one_string():
    df = pd.DataFrame({"product": ["  mug  "], "category": [" home "]})
    result = trim_spaces(df)
    assert result["product"].tolist() == ["mug"]
    assert result["category"].tolist() == ["home"]


def test_trim_spaces_leaves_columns_without_any_string_unchanged():
    df = pd.DataFrame({"product": ["  mug  "], "quantity": [42]})
    result = trim_spaces(df)
    assert result["quantity"].tolist() == [42]


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


def test_normalize_currency_does_not_convert_rows_already_in_target_currency(
    monkeypatch,
):
    mock_get_exchange_rate = MagicMock()
    monkeypatch.setattr(
        "order_to_cash.cleaning.get_exchange_rate", mock_get_exchange_rate
    )
    df = pd.DataFrame({"amount": [10, 20], "currency": ["EUR", "EUR"]})
    result = normalize_currency(df, ["amount"])
    mock_get_exchange_rate.assert_not_called()
    assert result["amount"].tolist() == [10, 20]
    assert result["currency"].tolist() == ["EUR", "EUR"]


def test_normalize_currency_converts_amount_and_updates_currency(monkeypatch):
    monkeypatch.setattr(
        "order_to_cash.cleaning.get_exchange_rate", MagicMock(return_value=2)
    )
    df = pd.DataFrame({"amount": [10], "currency": ["USD"]})
    result = normalize_currency(df, ["amount"])
    assert result["amount"].tolist() == [20]
    assert result["currency"].tolist() == ["EUR"]


def test_normalize_currency_converts_all_specified_columns(monkeypatch):
    monkeypatch.setattr(
        "order_to_cash.cleaning.get_exchange_rate", MagicMock(return_value=2)
    )
    df = pd.DataFrame(
        {"unit_price": [10], "expected_amount": [100], "currency": ["USD"]}
    )
    result = normalize_currency(df, ["unit_price", "expected_amount"])
    assert result["unit_price"].tolist() == [20]
    assert result["expected_amount"].tolist() == [200]


def test_normalize_currency_leaves_target_currency_rows_unchanged_in_mixed_df(
    monkeypatch,
):
    monkeypatch.setattr(
        "order_to_cash.cleaning.get_exchange_rate", MagicMock(return_value=2)
    )
    df = pd.DataFrame({"amount": [10, 20], "currency": ["EUR", "USD"]})
    result = normalize_currency(df, ["amount"])
    assert result["amount"].tolist() == [10, 40]
    assert result["currency"].tolist() == ["EUR", "EUR"]


def test_normalize_currency_applies_different_rates_per_currency(monkeypatch):
    rates = {"USD": 2, "GBP": 3}
    mock_get_exchange_rate = MagicMock(
        side_effect=lambda currency_from, currency_to: rates[currency_from]
    )
    monkeypatch.setattr(
        "order_to_cash.cleaning.get_exchange_rate", mock_get_exchange_rate
    )
    df = pd.DataFrame({"amount": [10, 10], "currency": ["USD", "GBP"]})
    result = normalize_currency(df, ["amount"])
    assert result["amount"].tolist() == [20, 30]
    assert result["currency"].tolist() == ["EUR", "EUR"]


def test_normalize_currency_calls_get_exchange_rate_with_correct_currencies(
    monkeypatch,
):
    mock_get_exchange_rate = MagicMock(return_value=1)
    monkeypatch.setattr(
        "order_to_cash.cleaning.get_exchange_rate", mock_get_exchange_rate
    )
    df = pd.DataFrame({"amount": [10], "currency": ["USD"]})
    normalize_currency(df, ["amount"], currency_target="EUR")
    mock_get_exchange_rate.assert_called_once_with("USD", "EUR")


def test_normalize_currency_respects_custom_column_and_target(monkeypatch):
    monkeypatch.setattr(
        "order_to_cash.cleaning.get_exchange_rate", MagicMock(return_value=2)
    )
    df = pd.DataFrame({"amount": [10], "money_currency": ["GBP"]})
    result = normalize_currency(
        df,
        ["amount"],
        currency_column_name="money_currency",
        currency_target="USD",
    )
    assert result["amount"].tolist() == [20]
    assert result["money_currency"].tolist() == ["USD"]


def test_normalize_country_with_full_name():
    assert normalize_country("France") == "France"


def test_normalize_country_with_alpha_2_code():
    assert normalize_country("FR") == "France"


def test_normalize_country_with_alpha_3_code():
    assert normalize_country("FRA") == "France"


def test_normalize_country_with_lowercase_and_spaces():
    assert normalize_country(" france ") == "France"


def test_normalize_country_ignores_non_string_values():
    assert normalize_country(None) is None
    assert normalize_country(42) == 42


def test_normalize_country_keeps_unrecognized_value_unchanged():
    assert normalize_country("not a country") == "not a country"


def test_normalize_country_column_normalizes_every_row():
    df = pd.DataFrame({"country": ["France", "FR", " germany ", "DE"]})
    result = normalize_country_column(df, "country")
    assert result["country"].tolist() == ["France", "France", "Germany", "Germany"]


def test_normalize_country_column_does_not_affect_other_columns():
    df = pd.DataFrame({"country": ["FR"], "customer_id": ["C1"]})
    result = normalize_country_column(df, "country")
    assert result["customer_id"].tolist() == ["C1"]


def test_round_columns_rounds_to_two_decimals_by_default():
    df = pd.DataFrame({"unit_price": [10.12345, 5.005]})
    result = round_columns(df, ["unit_price"])
    assert result["unit_price"].tolist() == [10.12, 5.0]


def test_round_columns_rounds_to_custom_decimals():
    df = pd.DataFrame({"unit_price": [10.12345]})
    result = round_columns(df, ["unit_price"], decimals=3)
    assert result["unit_price"].tolist() == [10.123]


def test_round_columns_rounds_multiple_columns():
    df = pd.DataFrame({"unit_price": [10.126], "expected_amount": [20.554]})
    result = round_columns(df, ["unit_price", "expected_amount"])
    assert result["unit_price"].tolist() == [10.13]
    assert result["expected_amount"].tolist() == [20.55]


def test_round_columns_does_not_affect_other_columns():
    df = pd.DataFrame({"unit_price": [10.12345], "quantity": [3.456]})
    result = round_columns(df, ["unit_price"])
    assert result["quantity"].tolist() == [3.456]
