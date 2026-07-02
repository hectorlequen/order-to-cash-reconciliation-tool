import logging

import pandas as pd
import requests

logger = logging.getLogger(__name__)


def clean_orders(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column_name in ["product", "category", "order_status"]:
        df = normalize_column_lowercase(df, column_name)
        df = trim_spaces(df, column_name)
    df = remove_duplicates(df, "order_id")
    df = normalize_missing_values(df)
    df = normalize_currency(df, ["unit_price", "expected_amount"])
    return df


def clean_payments(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for column_name in ["payment_status", "refund_status"]:
        df = normalize_column_lowercase(df, column_name)
        df = trim_spaces(df, column_name)
    df = remove_duplicates(df, "payment_id")
    df = normalize_missing_values(df)
    df = normalize_currency(df, ["amount_paid", "refund_amount"])
    return df


def validate_orders(
    df: pd.DataFrame,
    date_column_name: str = "order_date",
    critical_fields: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if critical_fields is None:
        critical_fields = ["order_id", "expected_amount"]
    return validate_df(df, date_column_name, critical_fields)


def validate_payments(
    df: pd.DataFrame,
    date_column_name: str = "payment_date",
    critical_fields: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if critical_fields is None:
        critical_fields = ["payment_id", "amount_paid"]
    return validate_df(df, date_column_name, critical_fields)


def validate_df(
    df: pd.DataFrame,
    date_column_name: str,
    critical_fields: list[str],
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    rejected_indexes = []
    rejection_reasons = {}
    for idx, row in df.iterrows():
        reject_reasons = []
        if not is_valid_date(row[date_column_name]):
            reject_reasons.append("invalid date")
        for field in critical_fields:
            if field not in row or pd.isna(row[field]):
                reject_reasons.append(f"missing {field}")
        if reject_reasons:
            rejected_indexes.append(idx)
            rejection_reasons[idx] = ", ".join(reject_reasons)

    df_valid = df.drop(rejected_indexes)
    df_rejected = df.loc[rejected_indexes].copy()
    df_rejected["rejection_reason"] = df_rejected.index.map(rejection_reasons)
    return df_valid, df_rejected


def normalize_column_lowercase(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    df = df.copy()
    df[column_name] = df[column_name].apply(
        lambda x: x.lower() if isinstance(x, str) else x
    )
    return df


def trim_spaces(df: pd.DataFrame, column_name: str) -> pd.DataFrame:
    df = df.copy()
    df[column_name] = df[column_name].apply(
        lambda x: x.strip() if isinstance(x, str) else x
    )
    return df


def normalize_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.replace("", None)
    return df


def remove_duplicates(df: pd.DataFrame, subset_column: str) -> pd.DataFrame:
    df = df.copy()
    return df.drop_duplicates(subset=subset_column)


def normalize_currency(
    df: pd.DataFrame,
    columns_to_convert: list[str],
    currency_column_name: str = "currency",
    currency_target: str = "EUR",
) -> pd.DataFrame:
    df = df.copy()
    for currency in df[currency_column_name].unique():
        if currency != currency_target:
            exchange_rate = get_exchange_rate(currency, currency_target)
            for column_to_convert in columns_to_convert:
                df.loc[df[currency_column_name] == currency, column_to_convert] *= (
                    exchange_rate
                )

            df.loc[df[currency_column_name] == currency, currency_column_name] = (
                currency_target
            )

    return df


def get_exchange_rate(currency_from: str, currency_to: str) -> float:
    try:
        response = requests.get(
            f"https://api.frankfurter.app/latest?from={currency_from}&to={currency_to}",
            timeout=5,
        )
        response.raise_for_status()
        return response.json()["rates"][currency_to]
    except requests.Timeout:
        logger.error(f"Timeout fetching exchange rate {currency_from} -> {currency_to}")
        raise
    except requests.HTTPError as e:
        logger.error(f"HTTP error fetching exchange rate: {e}")
        raise
    except requests.RequestException as e:
        logger.error(f"Request error fetching exchange rate: {e}")
        raise
    except (KeyError, ValueError) as e:
        logger.error(f"Failed to parse exchange rate response: {e}")
        raise


def is_valid_date(_date: str) -> bool:
    return not pd.isnull(pd.to_datetime(_date, errors="coerce"))
