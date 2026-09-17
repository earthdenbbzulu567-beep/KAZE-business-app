# KAZE Traders Business Manager

Flask + PostgreSQL shop, books, and office app.

## Run locally
1. Put this folder on the machine (HTML files sit next to `app.py`).
2. Set `DATABASE_URL` and `SECRET_KEY`.
3. `pip install -r requirements.txt`
4. `gunicorn app:app`

## Deploy on Render
- Build: `pip install -r requirements.txt`
- Start: `gunicorn app:app`
- Set `DATABASE_URL` and `SECRET_KEY` in the service environment.

## Modes
Shop / Books / Office / Full / Custom live in Settings. Unused modules stay off.

## Health
`GET /healthz` returns `{"ok": true}`.
