# KAZE Traders Business Manager

A small-business web app for stock, sales, customers, bookkeeping documents, journals, and simple financial statements.

## Licence

This project is released under the **MIT Licence**. The full legal text, plus an information section about the application, is in `LICENCE`.

In short: you may use, copy, change, and share the software if you keep the copyright and permission notice. There is **no warranty**.

## What the application does

KAZE helps a shop or trading business keep daily records in one place:

- Stock and low-stock alerts
- Sales and purchase orders
- Customers and suppliers
- Book keeping documents (quotation, invoice, receipt, delivery note, payslip, and others)
- Account tracking (cash book, journals, ledgers, profit and loss, balance sheet, cash flow)
- Budgets, recurring items, reports, tasks, notes, calendar, reminders
- SWOT and a simple business plan
- Team logins, settings, backup, and an owner-only clear-data reset

It is a practical record keeper, not a substitute for a qualified accountant or official tax filing.

## How to run

Python 3.11. Install dependencies from `requirements.txt`:

```
Flask
Flask-Login
Werkzeug
gunicorn
psycopg2-binary
reportlab
```

Set `DATABASE_URL` for PostgreSQL, then start the Flask app (`app.py`) or Gunicorn in production.

## Files

| File | Purpose |
| --- | --- |
| `app.py` | Server, routes, database, PDFs |
| `templates/` | Pages (dashboard, stock, sales, accounts, and so on) |
| `requirements.txt` | Python packages |
| `runtime.txt` | Python version |
| `LICENCE` | MIT licence and application information |
