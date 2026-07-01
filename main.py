import pandas as pd

from src.order_to_cash.cleaning import (
    clean_orders,
    clean_payments,
    validate_orders,
    validate_payments,
)

df_orders = pd.read_csv("data/orders.csv")
df_payments = pd.read_csv("data/payments.csv")

df_orders = clean_orders(df_orders)
df_payments = clean_payments(df_payments)

df_orders, df_orders_rejected = validate_orders(df_orders)
df_payments, df_payments_rejected = validate_payments(df_payments)

print(df_orders)
print(df_orders_rejected)
print(df_payments)
print(df_payments_rejected)
