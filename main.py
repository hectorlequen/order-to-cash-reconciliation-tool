import pandas as pd

from src.order_to_cash.cleaning import (
    clean_customers,
    clean_orders,
    clean_payments,
    validate_customers,
    validate_orders,
    validate_payments,
)

df_customers = pd.read_excel("data/customers.xlsx")
df_orders = pd.read_csv("data/orders.csv")
df_payments = pd.read_csv("data/payments.csv")

df_customers = clean_customers(df_customers)
df_orders = clean_orders(df_orders)
df_payments = clean_payments(df_payments)

df_customers, df_customers_rejected = validate_customers(df_customers)
df_orders, df_orders_rejected = validate_orders(df_orders)
df_payments, df_payments_rejected = validate_payments(df_payments)

print(df_customers)
print(df_customers_rejected)
print(df_orders)
print(df_orders_rejected)
print(df_payments)
print(df_payments_rejected)
