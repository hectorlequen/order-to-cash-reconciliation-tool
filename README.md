# Order-to-Cash Reconciliation Tool

A Python pipeline that automatically reconciles e-commerce orders, Stripe payments and customer data, detects anomalies, and generates an actionable Excel report for business teams.

> **"Replacing a manual, error-prone Excel process with a reliable, automated tool."**

---

## The Problem

In a small e-commerce business, reconciling orders with Stripe payments is often done manually in Excel. It's time-consuming, risky, and prone to human error. This tool automates the entire control process in seconds.

---

## Features

- Cleaning and validation of input data (CSV and Excel)
- Automatic currency conversion via the Frankfurter API
- Order ↔ Stripe payment reconciliation with status assignment
- Anomaly detection: missing payments, amount mismatches, refunds, orphan payments
- Order enrichment with customer data
- Multi-sheet Excel report generation

---

## Reconciliation Statuses

| Status | Description |
|--------|-------------|
| `reconciled` | Order paid, Stripe payment confirmed, amounts match |
| `missing_payment` | Order marked as paid but no valid Stripe payment found |
| `unexpected_payment` | Stripe payment received for an order not marked as paid |
| `awaiting_payment` | Unpaid order with no associated payment |
| `underpaid` | Amount paid is less than expected |
| `overpaid` | Amount paid is more than expected |
| `full_refund` | Full refund successfully processed |
| `partial_refund` | Partial refund successfully processed |
| `orphan_payment` | Stripe payment with no matching order |
| `payment_for_rejected_order` | Payment linked to an order rejected during validation |
| `to_refund` | Cancelled order with a received payment — refund required |
| `order_cancelled` | Cancelled order with no payment |
| `rejected` | Invalid row (bad date, missing critical field) |

---

## Excel Report Structure

The generated report contains 5 sheets:

| Sheet | Content |
|-------|---------|
| `summary` | High-level counts by status |
| `reconciled_orders` | Successfully reconciled orders |
| `exceptions_to_review` | Anomalies requiring action |
| `payments_refunds` | Detected refunds |
| `rejected_rows` | Invalid rows with rejection reason |

---

## Installation

```bash
git clone https://github.com/hectorlequen/order-to-cash-reconciliation-tool.git
cd order-to-cash-reconciliation-tool
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Usage

```bash
python main.py \
  --orders data/orders.csv \
  --payments data/payments.csv \
  --customers data/customers.xlsx \
  --output output/report.xlsx
```

All arguments have defaults matching the paths above, so this also works:

```bash
python main.py
```

---

## Project Structure

```
order-to-cash-reconciliation-tool/
├── src/
│   └── order_to_cash/
│       ├── cleaning.py        # Data cleaning, validation and normalisation
│       ├── reconciliation.py  # Reconciliation logic and status assignment
│       └── reporting.py       # Excel report generation
├── tests/
│   ├── test_cleaning.py
│   ├── test_reconciliation.py
│   └── test_reporting.py
├── data/                      # Input files (orders, payments, customers)
├── output/                    # Generated Excel report
└── main.py                    # CLI entry point
```

---

## Tech Stack

- **Python 3.14**
- **pandas** — data manipulation
- **openpyxl** — Excel report generation
- **requests** — API calls (Frankfurter exchange rates)
- **pycountry** — country name normalisation
- **pytest** — unit tests (79 tests)
- **ruff** — linting and formatting
- **pre-commit** — quality hooks

---

## Running Tests

```bash
pytest tests/
```

79 tests covering data cleaning, reconciliation logic and report generation.

---

## Input Files

| File | Format | Description |
|------|--------|-------------|
| `orders.csv` | CSV | E-commerce order export |
| `payments.csv` | CSV | Stripe payment export |
| `customers.xlsx` | Excel | Customer file maintained by the business team |