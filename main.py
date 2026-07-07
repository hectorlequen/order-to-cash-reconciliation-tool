import pandas as pd

from src.order_to_cash.cleaning import (
    clean_customers,
    clean_orders,
    clean_payments,
    validate_customers,
    validate_orders,
    validate_payments,
)
from src.order_to_cash.reconciliation import reconcile

pd.set_option("display.max_rows", None)
df_customers = pd.read_excel("data/customers.xlsx")
df_orders = pd.read_csv("data/orders.csv")
df_payments = pd.read_csv("data/payments.csv")

df_customers = clean_customers(df_customers)
df_orders = clean_orders(df_orders)
df_payments = clean_payments(df_payments)

df_customers, df_customers_rejected = validate_customers(df_customers)
df_orders, df_orders_rejected = validate_orders(df_orders)
df_payments, df_payments_rejected = validate_payments(df_payments)

df_reconciled, df_exceptions, df_refunds, df_rejected = reconcile(
    df_orders,
    df_payments,
    df_customers,
    df_orders_rejected,
    df_payments_rejected,
    df_customers_rejected,
)

print(df_customers)
print(df_customers_rejected)
print(df_orders)
print(df_orders_rejected)
print(df_payments)
print(df_payments_rejected)

print(df_reconciled)
print(df_exceptions)
print(df_refunds)
print(df_rejected)

print("reconciled:", df_reconciled.shape)
print("exceptions:", df_exceptions.shape)
print(df_exceptions["reconciliation_status"].value_counts())
print("refunds:", df_refunds.shape)
print("rejected:", df_rejected.shape)
