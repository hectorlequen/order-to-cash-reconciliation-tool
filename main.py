import argparse
import logging

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
from src.order_to_cash.reporting import generate_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Order-to-cash reconciliation pipeline"
    )
    parser.add_argument(
        "--customers", default="data/customers.xlsx", help="Path to the customers file"
    )
    parser.add_argument(
        "--orders", default="data/orders.csv", help="Path to the orders file"
    )
    parser.add_argument(
        "--payments", default="data/payments.csv", help="Path to the payments file"
    )
    parser.add_argument(
        "--output",
        default="output/report.xlsx",
        help="Path to the generated Excel report",
    )
    args = parser.parse_args()

    df_customers = pd.read_excel(args.customers)
    df_orders = pd.read_csv(args.orders)
    df_payments = pd.read_csv(args.payments)

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

    logger.info(
        f"customers: {len(df_customers)} valid, {len(df_customers_rejected)} rejected"
    )
    logger.info(f"orders: {len(df_orders)} valid, {len(df_orders_rejected)} rejected")
    logger.info(
        f"payments: {len(df_payments)} valid, {len(df_payments_rejected)} rejected"
    )
    logger.info(f"reconciled: {len(df_reconciled)}")
    logger.info(
        f"exceptions: {len(df_exceptions)}\n"
        f"{df_exceptions['reconciliation_status'].value_counts()}"
    )
    logger.info(f"refunds: {len(df_refunds)}")
    logger.info(f"rejected: {len(df_rejected)}")

    generate_report(df_reconciled, df_exceptions, df_refunds, df_rejected, args.output)
    logger.info(f"report written to {args.output}")


if __name__ == "__main__":
    main()
