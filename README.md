# KAZE 2.6.2 polish

Same Flask app. Fixes plus a Statistics page.

## Fixes
- Stock edit saves SKU and category.
- Stock table shows SKU and category.
- Low-stock highlight uses your Settings threshold, not a hardcoded 10.
- Stock page size uses Settings rows-per-page.
- Removed invalid nested quantity form inside the stock bulk form.
- Tasks empty row spans all columns.
- Money filter uses Settings currency; format is cached on the request.
- Fake sidebar integrations replaced with Team / Activity / Settings / Backup.
- Documents outside AI call removed; local notes draft instead.

## New
- Statistics page (/stats): count, total, average, min, max tables plus bar and doughnut charts.
- Date filter for sales, expenses, and cash.
- Dashboard quick statistics table.
- Reports links through to Statistics.

## Run
Put HTML in templates/. Set DATABASE_URL. pip install -r requirements.txt then gunicorn app:app.
