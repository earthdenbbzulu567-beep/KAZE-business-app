"""
apply_fixes.py — patches app.py with all 12 KAZE bug fixes.

Run from the folder that contains app.py:
    python apply_fixes.py

A backup app.py.bak.<timestamp> is created before any change is made.
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

APP = 'app.py'

if not os.path.isfile(APP):
    print(f"ERROR: {APP} not found in this folder.")
    print(f"Current folder: {os.getcwd()}")
    sys.exit(1)

BACKUP = f"{APP}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
shutil.copy2(APP, BACKUP)
print(f"Backup saved: {BACKUP}\n")

with open(APP, 'r', encoding='utf-8') as fh:
    src = fh.read()

original = src
FAILED = []
SKIPPED = []
APPLIED = []


def apply(label, old, new, *, required=True):
    global src
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label} — already fixed")
            SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found")
            if required:
                FAILED.append(label)
        return
    count = src.count(old)
    src = src.replace(old, new)
    print(f"  [OK]   {label} — {count} replacement(s)")
    APPLIED.append(label)


# ─────────────────────────────────────────────────────────────────────────
# Fix 1 — search() closes cursor before optional queries
# ─────────────────────────────────────────────────────────────────────────
print("[1/12] Fix search() cursor close")
apply(
    "search() cursor order",
    """    cur.close()
    conn.close()


    service_hits = []
    session_hits = []
    try:
        cur.execute(
            "SELECT id, name, 'service' as type FROM services WHERE user_id = %s AND (name ILIKE %s OR category ILIKE %s OR description ILIKE %s) LIMIT 10",
            (current_user.id, '%'+q+'%', '%'+q+'%', '%'+q+'%')
        )
        service_hits = cur.fetchall()
        cur.execute(
            "SELECT id, customer_name as name, 'session' as type FROM service_sessions WHERE user_id = %s AND (customer_name ILIKE %s OR notes ILIKE %s) LIMIT 10",
            (current_user.id, '%'+q+'%', '%'+q+'%')
        )
        session_hits = cur.fetchall()
    except Exception:
        pass

    bank_hits = invest_hits = shop_hits = []
    try:
        cur.execute(
            "SELECT id, name, 'bank' as type FROM bank_accounts WHERE user_id = %s AND (name ILIKE %s OR bank_name ILIKE %s) LIMIT 8",
            (current_user.id, '%'+q+'%', '%'+q+'%')
        )
        bank_hits = cur.fetchall()
        cur.execute(
            "SELECT id, name, 'investment' as type FROM investments WHERE user_id = %s AND name ILIKE %s LIMIT 8",
            (current_user.id, '%'+q+'%')
        )
        invest_hits = cur.fetchall()
        cur.execute(
            "SELECT id, title as name, 'listing' as type FROM shop_listings WHERE user_id = %s AND (title ILIKE %s OR description ILIKE %s) LIMIT 8",
            (current_user.id, '%'+q+'%', '%'+q+'%')
        )
        shop_hits = cur.fetchall()
    except Exception:
        pass

    results = customers + products + docs + note_hits + task_hits + book_hits + sku_hits + service_hits + session_hits + bank_hits + invest_hits + shop_hits
    return render_template('search_results.html', results=results, q=q)""",
    """    def _safe_query(sql, params):
        try:
            cur.execute("SAVEPOINT sp_search")
            cur.execute(sql, params)
            rows = cur.fetchall()
            cur.execute("RELEASE SAVEPOINT sp_search")
            return rows
        except Exception:
            try:
                cur.execute("ROLLBACK TO SAVEPOINT sp_search")
            except Exception:
                pass
            return []

    like = '%' + q + '%'
    service_hits = _safe_query(
        "SELECT id, name, 'service' as type FROM services WHERE user_id = %s "
        "AND (name ILIKE %s OR category ILIKE %s OR description ILIKE %s) LIMIT 10",
        (current_user.id, like, like, like),
    )
    session_hits = _safe_query(
        "SELECT id, customer_name as name, 'session' as type FROM service_sessions "
        "WHERE user_id = %s AND (customer_name ILIKE %s OR notes ILIKE %s) LIMIT 10",
        (current_user.id, like, like),
    )
    bank_hits = _safe_query(
        "SELECT id, name, 'bank' as type FROM bank_accounts "
        "WHERE user_id = %s AND (name ILIKE %s OR bank_name ILIKE %s) LIMIT 8",
        (current_user.id, like, like),
    )
    invest_hits = _safe_query(
        "SELECT id, name, 'investment' as type FROM investments "
        "WHERE user_id = %s AND name ILIKE %s LIMIT 8",
        (current_user.id, like),
    )
    shop_hits = _safe_query(
        "SELECT id, title as name, 'listing' as type FROM shop_listings "
        "WHERE user_id = %s AND (title ILIKE %s OR description ILIKE %s) LIMIT 8",
        (current_user.id, like, like),
    )

    cur.close()
    conn.close()

    results = (
        list(customers) + list(products) + list(docs) + list(note_hits)
        + list(task_hits) + list(book_hits) + list(sku_hits)
        + list(service_hits) + list(session_hits)
        + list(bank_hits) + list(invest_hits) + list(shop_hits)
    )
    return render_template('search_results.html', results=results, q=q)""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 2 — Settings plan_tier bypass
# ─────────────────────────────────────────────────────────────────────────
print("\n[2/12] Fix Settings plan_tier bypass")
apply(
    "settings plan_tier lockdown",
    """        plan_tier = normalize_plan(request.form.get('plan_tier') or 'ceo')
        if getattr(current_user, 'role', 'owner') != 'owner':
            plan_tier = normalize_plan((prior_keys.get('plan_tier') if prior_keys else None) or 'ceo')""",
    """        # Plan changes flow ONLY through /plans/upgrade -> payment -> webhook,
        # or the free-tier switch in set_plan(). Never trust the form here.
        plan_tier = normalize_plan((prior_keys.get('plan_tier') if prior_keys else None) or 'ceo')""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 3a — Plan block in auto_sale()
# ─────────────────────────────────────────────────────────────────────────
print("\n[3a/12] Plan block in auto_sale")
apply(
    "auto_sale plan block",
    """def auto_sale():
    \"\"\"One-step sale: current selling price, today, default qty 1.\"\"\"
    try:
        stock_id = int(request.form['stock_id'])
    except (TypeError, ValueError, KeyError):
        flash('Pick a product for auto sale.', 'danger')
        return redirect(url_for('sales'))
    try:
        quantity_sold = float(request.form.get('quantity') or 1)""",
    """def auto_sale():
    \"\"\"One-step sale: current selling price, today, default qty 1.\"\"\"
    try:
        stock_id = int(request.form['stock_id'])
    except (TypeError, ValueError, KeyError):
        flash('Pick a product for auto sale.', 'danger')
        return redirect(url_for('sales'))
    blocked = _plan_block('sales_month')
    if blocked:
        flash(blocked, 'danger')
        return redirect(url_for('plans'))
    try:
        quantity_sold = float(request.form.get('quantity') or 1)""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 3b — Plan block in counter_sale()
# ─────────────────────────────────────────────────────────────────────────
print("\n[3b/12] Plan block in counter_sale")
apply(
    "counter_sale plan block",
    """    if quantity_sold <= 0:
        flash('Quantity must be more than zero.', 'danger')
        return redirect(url_for('counter'))

    customer_id = request.form.get('customer_id') or None
    customer_name = request.form.get('customer_name', '')
    customer_email = ''
    sale_date = datetime.today().strftime('%Y-%m-%d')

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM stock WHERE id = %s AND user_id = %s', (stock_id, current_user.id))""",
    """    if quantity_sold <= 0:
        flash('Quantity must be more than zero.', 'danger')
        return redirect(url_for('counter'))
    blocked = _plan_block('sales_month')
    if blocked:
        flash(blocked, 'danger')
        return redirect(url_for('plans'))

    customer_id = request.form.get('customer_id') or None
    customer_name = request.form.get('customer_name', '')
    customer_email = ''
    sale_date = datetime.today().strftime('%Y-%m-%d')

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM stock WHERE id = %s AND user_id = %s', (stock_id, current_user.id))""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 3c — Plan block in counter_checkout()
# ─────────────────────────────────────────────────────────────────────────
print("\n[3c/12] Plan block in counter_checkout")
apply(
    "counter_checkout plan block",
    """    ids = request.form.getlist('line_stock_id')
    qtys = request.form.getlist('line_qty')
    if not ids:
        flash('Add at least one product to the ticket.', 'danger')
        return redirect(url_for('counter'))
    customer_id = request.form.get('customer_id') or None""",
    """    ids = request.form.getlist('line_stock_id')
    qtys = request.form.getlist('line_qty')
    if not ids:
        flash('Add at least one product to the ticket.', 'danger')
        return redirect(url_for('counter'))
    blocked = _plan_block('sales_month', extra=1)
    if blocked:
        flash(blocked, 'danger')
        return redirect(url_for('plans'))
    customer_id = request.form.get('customer_id') or None""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 3d — Plan block in repeat_sale()
# ─────────────────────────────────────────────────────────────────────────
print("\n[3d/12] Plan block in repeat_sale")
apply(
    "repeat_sale plan block",
    """def repeat_sale(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sales WHERE id=%s AND user_id=%s', (id, current_user.id))""",
    """def repeat_sale(id):
    blocked = _plan_block('sales_month')
    if blocked:
        flash(blocked, 'danger')
        return redirect(url_for('plans'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sales WHERE id=%s AND user_id=%s', (id, current_user.id))""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 3e — Plan block in multi_add(kind='sales')
# ─────────────────────────────────────────────────────────────────────────
print("\n[3e/12] Plan block in multi_add sales")
apply(
    "multi_add sales plan block",
    """        if kind == 'sales':
            if not module_on('sales'):
                flash('Sales is dormant in this mode.', 'danger')
                return redirect(url_for('dashboard'))
            bag, n = _form_lists('stock_id', 'quantity', 'customer_id', 'customer_name', 'date', 'discount', 'payment_method', 'sale_notes')
            for i in range(n):""",
    """        if kind == 'sales':
            if not module_on('sales'):
                flash('Sales is dormant in this mode.', 'danger')
                return redirect(url_for('dashboard'))
            bag, n = _form_lists('stock_id', 'quantity', 'customer_id', 'customer_name', 'date', 'discount', 'payment_method', 'sale_notes')
            blocked = _plan_block('sales_month', extra=n)
            if blocked:
                flash(blocked, 'danger')
                return redirect(url_for('plans'))
            for i in range(n):""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 3f — Plan block in import_stock_csv()
# ─────────────────────────────────────────────────────────────────────────
print("\n[3f/12] Plan block in import_stock_csv")
apply(
    "import_stock_csv plan block",
    """def import_stock_csv():
    rows = _read_uploaded_csv(request.files.get('file'))
    if rows is None:
        flash('Could not read that file. Please upload a CSV exported from this app (or matching columns: Product, Quantity, Unit, Cost Price, Selling Price).', 'danger')
        return redirect(url_for('stock'))
    conn = get_db()""",
    """def import_stock_csv():
    rows = _read_uploaded_csv(request.files.get('file'))
    if rows is None:
        flash('Could not read that file. Please upload a CSV exported from this app (or matching columns: Product, Quantity, Unit, Cost Price, Selling Price).', 'danger')
        return redirect(url_for('stock'))
    blocked = _plan_block('stock', extra=len(rows))
    if blocked:
        flash(blocked, 'danger')
        return redirect(url_for('plans'))
    conn = get_db()""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 4 — clear_data misses code_snippets and day_closes
# ─────────────────────────────────────────────────────────────────────────
print("\n[4/12] Fix clear_data missing tables")
apply(
    "clear_data extra tables",
    """            'DELETE FROM user_activity WHERE user_id = %s',
        ):
            cur.execute(sql, (uid,))""",
    """            'DELETE FROM user_activity WHERE user_id = %s',
            'DELETE FROM code_snippets WHERE user_id = %s',
            'DELETE FROM day_closes WHERE user_id = %s',
        ):
            cur.execute(sql, (uid,))""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 5 — delete_customer aborts transaction
# ─────────────────────────────────────────────────────────────────────────
print("\n[5/12] Fix delete_customer transaction abort")
apply(
    "delete_customer rollback",
    """    try:
        cur.execute('UPDATE service_sessions SET customer_id=NULL WHERE user_id=%s AND customer_id=%s', (current_user.id, id))
    except Exception:
        pass
    cur.execute('DELETE FROM customers WHERE id = %s AND user_id = %s', (id, current_user.id))""",
    """    try:
        cur.execute('UPDATE service_sessions SET customer_id=NULL WHERE user_id=%s AND customer_id=%s', (current_user.id, id))
    except Exception:
        # An error inside a Postgres transaction aborts it — roll back and
        # replay the sales unlink so the following DELETE can succeed.
        conn.rollback()
        cur.execute('UPDATE sales SET customer_id=NULL WHERE user_id=%s AND customer_id=%s', (current_user.id, id))
    cur.execute('DELETE FROM customers WHERE id = %s AND user_id = %s', (id, current_user.id))""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 6 — PDF escape of user-controlled text
# ─────────────────────────────────────────────────────────────────────────
print("\n[6/12] Fix PDF escape")
apply(
    "PDF escape _build_pdf",
    """def _build_pdf(buffer, title, business_name, meta_lines, table_data, footer_lines=None):
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor('#1f8a3d'), alignment=TA_LEFT)
    elements = []

    header_text = []
    if business_name:
        header_text.append(Paragraph(business_name, styles['Heading2']))
    header_text.append(Paragraph(title, title_style))""",
    """def _build_pdf(buffer, title, business_name, meta_lines, table_data, footer_lines=None):
    from xml.sax.saxutils import escape as _xml_escape

    def _safe_paragraph(text, style):
        \"\"\"Escape user-controlled text so ReportLab's mini-HTML parser never chokes.\"\"\"
        return Paragraph(_xml_escape(str(text)), style)

    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor('#1f8a3d'), alignment=TA_LEFT)
    elements = []

    header_text = []
    if business_name:
        header_text.append(_safe_paragraph(business_name, styles['Heading2']))
    header_text.append(_safe_paragraph(title, title_style))""",
)

apply(
    "PDF escape table cells",
    """    table = Table(table_data, hAlign='LEFT')""",
    """    safe_table = []
    for row in table_data:
        safe_table.append([_xml_escape(str(cell)) for cell in row])
    table = Table(safe_table, hAlign='LEFT')""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 7 — stats date filter on income, by_product, by_expense
# ─────────────────────────────────────────────────────────────────────────
print("\n[7/12] Fix stats date filter")
apply(
    "stats income date filter",
    """    cur.execute(
        'SELECT COUNT(*) AS n, COALESCE(SUM(amount),0) AS s FROM income WHERE user_id = %s', (uid,))
    income = cur.fetchone()""",
    """    inc_date_clause = ''
    inc_params = [uid]
    if start_date and end_date:
        inc_date_clause = ' AND date BETWEEN %s AND %s'
        inc_params += [start_date, end_date]
    cur.execute(
        'SELECT COUNT(*) AS n, COALESCE(SUM(amount),0) AS s FROM income WHERE user_id = %s'
        + inc_date_clause,
        inc_params)
    income = cur.fetchone()""",
)

apply(
    "stats by_product/by_expense date filter",
    """    cur.execute(
        'SELECT stock.product_name AS name, COUNT(sales.id) AS n, '
        'COALESCE(SUM(sales.quantity_sold),0) AS units, '
        'COALESCE(SUM(sales.total_amount),0) AS revenue, '
        'COALESCE(AVG(sales.total_amount),0) AS avg_sale, '
        'COALESCE(SUM(sales.profit),0) AS profit '
        'FROM sales JOIN stock ON sales.stock_id = stock.id '
        'WHERE sales.user_id = %s '
        'GROUP BY stock.product_name ORDER BY revenue DESC LIMIT 12',
        (uid,))
    by_product = cur.fetchall()
    cur.execute(
        'SELECT category AS name, COUNT(*) AS n, COALESCE(SUM(amount),0) AS total, '
        'COALESCE(AVG(amount),0) AS avg FROM expenses WHERE user_id = %s '
        'GROUP BY category ORDER BY total DESC',
        (uid,))
    by_expense = cur.fetchall()""",
    """    sales_date_clause = ''
    sales_params = [uid]
    if start_date and end_date:
        sales_date_clause = ' AND sales.sale_date BETWEEN %s AND %s'
        sales_params += [start_date, end_date]
    cur.execute(
        'SELECT stock.product_name AS name, COUNT(sales.id) AS n, '
        'COALESCE(SUM(sales.quantity_sold),0) AS units, '
        'COALESCE(SUM(sales.total_amount),0) AS revenue, '
        'COALESCE(AVG(sales.total_amount),0) AS avg_sale, '
        'COALESCE(SUM(sales.profit),0) AS profit '
        'FROM sales JOIN stock ON sales.stock_id = stock.id '
        'WHERE sales.user_id = %s' + sales_date_clause + ' '
        'GROUP BY stock.product_name ORDER BY revenue DESC LIMIT 12',
        sales_params)
    by_product = cur.fetchall()
    exp_date_clause = ''
    exp_params = [uid]
    if start_date and end_date:
        exp_date_clause = ' AND date BETWEEN %s AND %s'
        exp_params += [start_date, end_date]
    cur.execute(
        'SELECT category AS name, COUNT(*) AS n, COALESCE(SUM(amount),0) AS total, '
        'COALESCE(AVG(amount),0) AS avg FROM expenses WHERE user_id = %s'
        + exp_date_clause + ' GROUP BY category ORDER BY total DESC',
        exp_params)
    by_expense = cur.fetchall()""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 8 — sales chart shows only current page
# ─────────────────────────────────────────────────────────────────────────
print("\n[8/12] Fix sales chart pagination")
apply(
    "sales chart full dataset",
    """    sales_by_date = {}
    for sale in all_sales:
        d = str(sale['sale_date'] or '')[:10]
        sales_by_date[d] = sales_by_date.get(d, 0) + (sale['total_amount'] or 0)
    
    cur.close()
    conn.close()""",
    """    cur.execute(
        "SELECT substr(sale_date, 1, 10) AS d, COALESCE(SUM(total_amount), 0) AS t "
        "FROM sales WHERE user_id = %s "
        "GROUP BY substr(sale_date, 1, 10) ORDER BY d",
        (current_user.id,)
    )
    sales_by_date = {row['d']: float(row['t'] or 0) for row in cur.fetchall() if row['d']}

    cur.close()
    conn.close()""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 9 — stock chart shows only current page
# ─────────────────────────────────────────────────────────────────────────
print("\n[9/12] Fix stock chart pagination")
apply(
    "stock chart full dataset",
    """    items = cur.fetchall()
    cur.close()
    conn.close()
    
    product_names = [item['product_name'] for item in items]
    inventory_values = [item['quantity'] * item['cost_price'] for item in items]
    total_pages = (total + per_page - 1) // per_page""",
    """    items = cur.fetchall()
    cur.execute(
        'SELECT product_name, quantity, cost_price FROM stock '
        'WHERE user_id = %s ORDER BY product_name',
        (current_user.id,)
    )
    chart_rows = cur.fetchall()
    cur.close()
    conn.close()

    product_names = [r['product_name'] for r in chart_rows]
    inventory_values = [float(r['quantity'] or 0) * float(r['cost_price'] or 0) for r in chart_rows]
    total_pages = (total + per_page - 1) // per_page""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 10 — login loses `next`
# ─────────────────────────────────────────────────────────────────────────
print("\n[10/12] Fix login next redirect")
apply(
    "login _safe_next helper",
    """def _complete_local_login(user):
    login_user(User(user['id'], user['username'], user['email'], user.get('role'), user.get('owner_id')))""",
    """def _safe_next(default_endpoint='dashboard'):
    \"\"\"Return a safe same-origin path from ?next=, or None.\"\"\"
    raw = (request.form.get('next') or request.args.get('next') or '').strip()
    if not raw:
        return None
    # Only allow internal paths — reject //evil.com, http://, javascript:, etc.
    if not raw.startswith('/') or raw.startswith('//'):
        return None
    return raw


def _complete_local_login(user):
    login_user(User(user['id'], user['username'], user['email'], user.get('role'), user.get('owner_id')))""",
)

apply(
    "login return next",
    """    except Exception as exc:
        print('Activity log error:', exc)
    return redirect(url_for('dashboard'))""",
    """    except Exception as exc:
        print('Activity log error:', exc)
    return redirect(_safe_next() or url_for('dashboard'))""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 11 — PDF escape in guide_pdf (uses Paragraph directly)
# ─────────────────────────────────────────────────────────────────────────
print("\n[11/12] Fix guide_pdf escape")
apply(
    "guide_pdf escape business name",
    """    story = [
        Paragraph('KAZE Traders — Practical Guide', title),
        Paragraph('For {}. Version 2.6. How to run the shop in the app, step by step.'.format(business_name), body),
        Spacer(1, 8),
    ]""",
    """    from xml.sax.saxutils import escape as _xml_escape
    story = [
        Paragraph('KAZE Traders — Practical Guide', title),
        Paragraph('For {}. Version 2.6. How to run the shop in the app, step by step.'.format(_xml_escape(str(business_name))), body),
        Spacer(1, 8),
    ]""",
)


# ─────────────────────────────────────────────────────────────────────────
# Fix 12 — force HTTPS behind proxy
# ─────────────────────────────────────────────────────────────────────────
print("\n[12/12] ProxyFix upgrade (for HTTPS redirects behind Render)")
apply(
    "ProxyFix x_for=2",
    "app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)",
    "app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=2, x_host=2, x_prefix=1)",
    required=False,
)


# ─────────────────────────────────────────────────────────────────────────
# Write the patched file
# ─────────────────────────────────────────────────────────────────────────
if src == original:
    print("\nNo changes were made — the file may already be fixed.")
else:
    with open(APP, 'w', encoding='utf-8') as fh:
        fh.write(src)
    print(f"\nWrote {len(src):,} bytes to {APP}")


# ─────────────────────────────────────────────────────────────────────────
# Verify the result compiles
# ─────────────────────────────────────────────────────────────────────────
print("\nRunning py_compile to verify syntax...")
result = subprocess.run(
    [sys.executable, '-m', 'py_compile', APP],
    capture_output=True,
    text=True,
)
if result.returncode == 0:
    print("  [OK]   app.py compiles cleanly.")
else:
    print("  [FAIL] app.py has a syntax error:")
    print(result.stderr)
    print(f"\nRestore the backup if needed:")
    print(f"  copy \"{BACKUP}\" \"{APP}\"")


# ─────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print(f"Applied:  {len(APPLIED)}")
print(f"Skipped:  {len(SKIPPED)} (already fixed)")
print(f"Failed:   {len(FAILED)}")
if FAILED:
    print("\nFailed fixes (pattern not found in your app.py):")
    for name in FAILED:
        print(f"  - {name}")
    print("\nThis usually means you already edited that region by hand.")
    print("Send me your current app.py and I'll re-check.")
print("=" * 60)