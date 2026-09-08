# Deploy KAZE on PythonAnywhere

This pack is ready for a **manual Flask** web app on PythonAnywhere (Python 3.11).
PythonAnywhere does not use the `Procfile` (that is for Render/Heroku). It uses
`wsgi.py` instead.

Replace `YOUR_USERNAME` everywhere with your PythonAnywhere username.

## 1. Files you need on the server

| File | Role |
|---|---|
| `app.py` | Flask app |
| `wsgi.py` | WSGI entry (`application`) |
| `templates/` | HTML pages |
| `static/` | Logo and favicons |
| `requirements.txt` | Python packages |

## 2. Upload the code

**Git (preferred)** in a Bash console:

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git kaze-business-manager
cd kaze-business-manager
```

**Or** zip this folder (no `__pycache__`), upload it under the Files tab, unzip:

```bash
cd ~
unzip kaze_currency_v263.zip
mv kaze_currency kaze-business-manager
```

Then edit `wsgi.py` and set:

```python
project_home = "/home/YOUR_USERNAME/kaze-business-manager"
```

## 3. Virtualenv

```bash
cd ~/kaze-business-manager
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

`psycopg2-binary` talks to Aiven PostgreSQL. If install fails, try `psycopg2`
instead (PA often has the system lib already).

## 4. Web app

1. Web tab → **Add a new web app**
2. **Manual configuration**
3. Python **3.11**
4. Paths:
   - Source code: `/home/YOUR_USERNAME/kaze-business-manager`
   - Working directory: `/home/YOUR_USERNAME/kaze-business-manager`
   - WSGI file: `/home/YOUR_USERNAME/kaze-business-manager/wsgi.py`
     (or edit the default `/var/www/YOUR_USERNAME_pythonanywhere_com_wsgi.py`
     so it matches `wsgi.py`)
5. Virtualenv: `/home/YOUR_USERNAME/kaze-business-manager/venv`

## 5. Environment variables (Web tab)

Do **not** put passwords in `wsgi.py` if you can avoid it.

| Key | Value |
|---|---|
| `DATABASE_URL` | Aiven string, include `sslmode=require` |
| `SECRET_KEY` | Long random string |
| `MAIL_USERNAME` | Optional Gmail |
| `MAIL_PASSWORD` | Optional Gmail app password |

Save.

## 6. Static files

Web tab → Static files:

- URL: `/static/`
- Path: `/home/YOUR_USERNAME/kaze-business-manager/static/`

Put `logo_icon.png`, `logo_full.png`, `favicon-32.png`, `favicon-64.png`,
and `apple-touch-icon.png` in that folder. The templates look for those names.

## 7. Aiven firewall

PythonAnywhere outbound IPs must be allowed on Aiven (or allow `0.0.0.0/0`
briefly while testing). In a PA Bash console:

```bash
curl -s ifconfig.me
```

Add that IP on the Aiven PostgreSQL allowlist.

## 8. Reload

Green **Reload** on the Web tab.

Site: `https://YOUR_USERNAME.pythonanywhere.com`

`init_db()` runs when `app.py` is imported, so tables are created on first load.

Manual check:

```bash
cd ~/kaze-business-manager
source venv/bin/activate
python -c "from app import init_db; init_db(); print('db ok')"
```

## 9. After it is up

1. Open the site → Sign up (first user is owner).
2. Settings → business name and currency.
3. Add one stock item → Sales → Auto sale or Counter.

## Troubleshooting

| Problem | What to check |
|---|---|
| 500 error | Web tab → Error log. Missing `DATABASE_URL` or Aiven blocked. |
| Logo missing | Static mapping path ends at `.../static` |
| `ModuleNotFoundError` | `pip install -r requirements.txt` inside `venv` |
| `DATABASE_URL environment variable is not set` | Env vars not saved, or WSGI file imported `app` before vars were set |
| Connection refused | Aiven allowlist / `sslmode=require` |
| WSGI not found | Path on Web tab must match the file you uploaded |

Error logs: Web tab → Log files → Error log.
