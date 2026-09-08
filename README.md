# KAZE 2.6.3

Currency from Settings is used across the app.

## Currency
Set symbol and decimal places under Settings. Then:
- Tables use the money() helper
- Charts, till, calculator, and dashboard counters use the same symbol in the browser
- Flash messages, activity log, and daily summary email use the same format
- Tax page uses money() instead of a separate symbol prefix

## Run
templates/ + app.py. DATABASE_URL. pip install -r requirements.txt. gunicorn app:app.


See PYTHONANYWHERE.md for PythonAnywhere deploy (wsgi.py).
