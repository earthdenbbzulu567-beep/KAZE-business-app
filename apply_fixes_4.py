"""
apply_fixes_4.py — combines all outstanding fixes:
  1) the 3 never-applied fixes from apply_fixes.py (search, PDF escape, mode_runtime, Pillow)
  2) SQL fixes for all the new routes (insights, health, rfm, etc.)
Run from the folder with app.py:
    python apply_fixes_4.py
"""

import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
FAILED, APPLIED, SKIPPED = [], [], []


def backup(path):
    if os.path.isfile(path):
        b = f"{path}.bak.{STAMP}"
        if not os.path.isfile(b):
            shutil.copy2(path, b)


def patch(path, label, old, new, required=True):
    if not os.path.isfile(path):
        print(f"  [SKIP] {label} — {path} missing"); return
    with open(path, 'r', encoding='utf-8') as fh:
        src = fh.read()
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label} — already updated"); SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found")
            if required: FAILED.append(label)
        return
    backup(path)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(src.replace(old, new))
    print(f"  [OK]   {label}")
    APPLIED.append(label)


# ═════════════════════════════════════════════════════════════════
print("[1] mode_runtime.py — remove row limit on P/L fetch")
patch('mode_runtime.py', 'fetch_sales limit 150 -> 5000',
      "def fetch_sales(cur, user_id, limit=150):",
      "def fetch_sales(cur, user_id, limit=5000):")
patch('mode_runtime.py', 'fetch_income limit 200 -> 5000',
      "def fetch_income(cur, user_id, limit=200):",
      "def fetch_income(cur, user_id, limit=5000):")
patch('mode_runtime.py', 'fetch_expenses limit 200 -> 5000',
      "def fetch_expenses(cur, user_id, limit=200):",
      "def fetch_expenses(cur, user_id, limit=5000):")


# ═════════════════════════════════════════════════════════════════
print("\n[2] requirements.txt — add Pillow")
if os.path.isfile('requirements.txt'):
    with open('requirements.txt', 'r', encoding='utf-8') as fh:
        rq = fh.read()
    if 'Pillow' not in rq:
        backup('requirements.txt')
        if not rq.endswith('\n'): rq += '\n'
        with open('requirements.txt', 'w', encoding='utf-8') as fh:
            fh.write(rq + 'Pillow\n')
        print("  [OK]   Pillow added"); APPLIED.append('Pillow')
    else:
        print("  [SKIP] already present"); SKIPPED.append('Pillow')


# ═════════════════════════════════════════════════════════════════
print("\n[3] app.py — search() cursor ordering")
patch('app.py', 'search savepoint refactor',
'''    cur.close()
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
    return render_template('search_results.html', results=results, q=q)''',
'''    def _safe_query(sql, params):
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
        (current_user.id, like, like, like))
    session_hits = _safe_query(
        "SELECT id, customer_name as name, 'session' as type FROM service_sessions "
        "WHERE user_id = %s AND (customer_name ILIKE %s OR notes ILIKE %s) LIMIT 10",
        (current_user.id, like, like))
    bank_hits = _safe_query(
        "SELECT id, name, 'bank' as type FROM bank_accounts "
        "WHERE user_id = %s AND (name ILIKE %s OR bank_name ILIKE %s) LIMIT 8",
        (current_user.id, like, like))
    invest_hits = _safe_query(
        "SELECT id, name, 'investment' as type FROM investments "
        "WHERE user_id = %s AND name ILIKE %s LIMIT 8",
        (current_user.id, like))
    shop_hits = _safe_query(
        "SELECT id, title as name, 'listing' as type FROM shop_listings "
        "WHERE user_id = %s AND (title ILIKE %s OR description ILIKE %s) LIMIT 8",
        (current_user.id, like, like))

    cur.close()
    conn.close()

    results = (list(customers) + list(products) + list(docs) + list(note_hits)
               + list(task_hits) + list(book_hits) + list(sku_hits)
               + list(service_hits) + list(session_hits)
               + list(bank_hits) + list(invest_hits) + list(shop_hits))
    return render_template('search_results.html', results=results, q=q)''')


# ═════════════════════════════════════════════════════════════════
print("\n[4] app.py — PDF escape in _build_pdf")
patch('app.py', 'PDF escape helper',
'''def _build_pdf(buffer, title, business_name, meta_lines, table_data, footer_lines=None):
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor('#1f8a3d'), alignment=TA_LEFT)
    elements = []

    header_text = []
    if business_name:
        header_text.append(Paragraph(business_name, styles['Heading2']))
    header_text.append(Paragraph(title, title_style))''',
'''def _build_pdf(buffer, title, business_name, meta_lines, table_data, footer_lines=None):
    from xml.sax.saxutils import escape as _xml_escape
    def _safe_paragraph(text, style):
        return Paragraph(_xml_escape(str(text)), style)
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor('#1f8a3d'), alignment=TA_LEFT)
    elements = []

    header_text = []
    if business_name:
        header_text.append(_safe_paragraph(business_name, styles['Heading2']))
    header_text.append(_safe_paragraph(title, title_style))''')
patch('app.py', 'PDF table cell escape',
      "    table = Table(table_data, hAlign='LEFT')",
      "    safe_table = [[_xml_escape(str(cell)) for cell in row] for row in table_data]\n    table = Table(safe_table, hAlign='LEFT')")


# ═════════════════════════════════════════════════════════════════
print("\n[5] app.py — pay_plan uses stored_key")
patch('app.py', 'pay_plan stored_key',
      "    current = plan_info(settings)\n    if PLAN_RANK[wanted] <= PLAN_RANK[current['key']]:",
      "    current = plan_info(settings)\n    if PLAN_RANK[wanted] <= PLAN_RANK[current['stored_key']]:")


# ═════════════════════════════════════════════════════════════════
print("\n[6] app.py — SQL fixes for new routes")

# /insights
patch('app.py', 'insights SQL fix',
'''    cur.execute("SELECT COALESCE(SUM(total),0) as sales FROM sales WHERE user_id=%s AND date >= CURRENT_DATE - INTERVAL '30 days'", (current_user.id,))
    recent_sales = cur.fetchone()['sales']
    cur.execute("SELECT COUNT(*) as low FROM stock WHERE user_id=%s AND quantity <= low_stock_threshold", (current_user.id,))
    low_stock = cur.fetchone()['low']''',
'''    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS sales FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY-MM-DD')",
        (current_user.id,))
    recent_sales = (cur.fetchone() or {}).get('sales') or 0
    cur.execute(
        "SELECT COUNT(*) AS low FROM stock st "
        "WHERE st.user_id=%s AND st.quantity <= COALESCE("
        "(SELECT low_stock_threshold FROM settings WHERE user_id=%s), 10)",
        (current_user.id, current_user.id))
    low_stock = (cur.fetchone() or {}).get('low') or 0''')

# /health
patch('app.py', 'health SQL fix',
'''    cur.execute("SELECT COALESCE(SUM(total),0) as sales FROM sales WHERE user_id=%s AND date >= CURRENT_DATE - INTERVAL '30 days'", (current_user.id,))
    sales = cur.fetchone()['sales'] or 0
    cur.execute("SELECT COUNT(*) as low FROM stock WHERE user_id=%s AND quantity <= COALESCE(low_stock_threshold,5)", (current_user.id,))
    low = cur.fetchone()['low'] or 0''',
'''    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS sales FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY-MM-DD')",
        (current_user.id,))
    sales = (cur.fetchone() or {}).get('sales') or 0
    cur.execute(
        "SELECT COUNT(*) AS low FROM stock st "
        "WHERE st.user_id=%s AND st.quantity <= COALESCE("
        "(SELECT low_stock_threshold FROM settings WHERE user_id=%s), 5)",
        (current_user.id, current_user.id))
    low = (cur.fetchone() or {}).get('low') or 0''')

# /rfm
patch('app.py', 'rfm SQL fix',
'''    cur.execute("""
        SELECT c.name, 
               MAX(s.date) as last_purchase,
               COUNT(s.id) as frequency,
               COALESCE(SUM(s.total),0) as monetary
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id = %s
        GROUP BY c.id, c.name
        ORDER BY monetary DESC
        LIMIT 20
    """, (current_user.id,))''',
'''    cur.execute("""
        SELECT c.name,
               MAX(s.sale_date) AS last_purchase,
               COUNT(s.id) AS frequency,
               COALESCE(SUM(s.total_amount),0) AS monetary
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id = %s
        GROUP BY c.id, c.name
        ORDER BY monetary DESC
        LIMIT 20
    """, (current_user.id,))''')

# /collections
patch('app.py', 'collections SQL fix',
'''    cur.execute("""
        SELECT c.name, SUM(s.total - COALESCE(s.paid,0)) as outstanding
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.user_id = %s AND (s.total - COALESCE(s.paid,0)) > 0
        GROUP BY c.id, c.name
        ORDER BY outstanding DESC
        LIMIT 15
    """, (current_user.id,))''',
'''    cur.execute("""
        SELECT c.name, COALESCE(SUM(s.total_amount),0) AS outstanding
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.user_id = %s AND COALESCE(s.payment_method,'cash') NOT IN ('cash')
        GROUP BY c.id, c.name
        HAVING COALESCE(SUM(s.total_amount),0) > 0
        ORDER BY outstanding DESC
        LIMIT 15
    """, (current_user.id,))''')

# /loyalty
patch('app.py', 'loyalty SQL fix',
'''    cur.execute("SELECT name, COALESCE(SUM(total),0) as spent FROM customers c LEFT JOIN sales s ON s.customer_id=c.id WHERE c.user_id=%s GROUP BY c.id ORDER BY spent DESC LIMIT 15", (current_user.id,))''',
'''    cur.execute(
        "SELECT c.name, COALESCE(SUM(s.total_amount),0) AS spent "
        "FROM customers c LEFT JOIN sales s ON s.customer_id=c.id AND s.user_id=c.user_id "
        "WHERE c.user_id=%s GROUP BY c.id, c.name ORDER BY spent DESC LIMIT 15",
        (current_user.id,))''')

# /expense_analytics
patch('app.py', 'expense_analytics SQL fix',
'''    cur.execute("SELECT category, COALESCE(SUM(amount),0) as total FROM cashbook WHERE user_id=%s AND type='expense' GROUP BY category ORDER BY total DESC LIMIT 10", (current_user.id,))''',
'''    cur.execute(
        "SELECT category, COALESCE(SUM(amount),0) AS total FROM cash_books "
        "WHERE user_id=%s AND entry_type='out' GROUP BY category ORDER BY total DESC LIMIT 10",
        (current_user.id,))''')

# /top_customers
patch('app.py', 'top_customers SQL fix',
'''    cur.execute("SELECT c.name, COALESCE(SUM(s.total),0) as total FROM customers c LEFT JOIN sales s ON s.customer_id=c.id WHERE c.user_id=%s GROUP BY c.id ORDER BY total DESC LIMIT 10", (current_user.id,))''',
'''    cur.execute(
        "SELECT c.name, COALESCE(SUM(s.total_amount),0) AS total "
        "FROM customers c LEFT JOIN sales s ON s.customer_id=c.id AND s.user_id=c.user_id "
        "WHERE c.user_id=%s GROUP BY c.id, c.name ORDER BY total DESC LIMIT 10",
        (current_user.id,))''')

# /daily_summary
patch('app.py', 'daily_summary SQL fix',
'''    cur.execute("SELECT COALESCE(SUM(total_amount),0) as sales FROM sales WHERE user_id=%s AND sale_date = CURRENT_DATE", (current_user.id,))
    today_sales = cur.fetchone()['sales']''',
'''    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS sales FROM sales "
        "WHERE user_id=%s AND sale_date = to_char(CURRENT_DATE, 'YYYY-MM-DD')",
        (current_user.id,))
    today_sales = (cur.fetchone() or {}).get('sales') or 0''')

# /forecast
patch('app.py', 'forecast SQL fix',
'''    cur.execute("SELECT COALESCE(AVG(total),0) as avg_daily FROM sales WHERE user_id=%s AND date >= CURRENT_DATE - INTERVAL '30 days'", (current_user.id,))
    avg = cur.fetchone()['avg_daily'] or 0''',
'''    cur.execute(
        "SELECT COALESCE(AVG(total_amount),0) AS avg_daily FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY-MM-DD')",
        (current_user.id,))
    avg = (cur.fetchone() or {}).get('avg_daily') or 0''')

# /sales/margin-alert
patch('app.py', 'sales_margin_alert SQL fix',
'''        SELECT s.product_name, AVG(s.selling_price_at_time) as avg_sell, AVG(COALESCE(st.cost_price,0)) as avg_cost
        FROM sales s LEFT JOIN stock st ON s.stock_id = st.id''',
'''        SELECT st.product_name, AVG(s.selling_price_at_time) AS avg_sell, AVG(COALESCE(st.cost_price,0)) AS avg_cost
        FROM sales s LEFT JOIN stock st ON s.stock_id = st.id''')

# /sales/velocity
patch('app.py', 'sales_velocity SQL fix',
'''        SELECT product_name, SUM(quantity_sold)/14.0 as vel FROM sales
        WHERE user_id=%s AND sale_date >= CURRENT_DATE - INTERVAL '14 days'
        GROUP BY product_name ORDER BY vel DESC LIMIT 12''',
'''        SELECT st.product_name, SUM(s.quantity_sold)/14.0 AS vel
        FROM sales s JOIN stock st ON st.id = s.stock_id
        WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '14 days', 'YYYY-MM-DD')
        GROUP BY st.product_name ORDER BY vel DESC LIMIT 12''')

# /reminders/context
patch('app.py', 'reminders_context SQL fix',
'''    cur.execute("SELECT title, due_date FROM reminders WHERE user_id=%s AND done=0 LIMIT 8", (current_user.id,))
    rows = cur.fetchall()''',
'''    cur.execute(
        "SELECT title, due_date FROM tasks WHERE user_id=%s AND done=0 LIMIT 8",
        (current_user.id,))
    rows = cur.fetchall()''')

# /team/permissions
patch('app.py', 'team_permissions SQL fix',
'''    cur.execute("SELECT username, role FROM users WHERE id=%s OR invited_by=%s", (current_user.id, current_user.id))
    rows = cur.fetchall()''',
'''    cur.execute(
        "SELECT username, role FROM users WHERE id=%s OR owner_id=%s",
        (current_user.id, current_user.id))
    rows = cur.fetchall()''')

# /profit_matrix
patch('app.py', 'profit_matrix SQL fix',
'''    cur.execute("""
        SELECT s.name, SUM(si.quantity * (si.price - COALESCE(st.cost_price,0))) as profit
        FROM sales_items si
        JOIN sales s ON si.sale_id = s.id
        LEFT JOIN stock st ON si.product_name = st.name AND st.user_id = s.user_id
        WHERE s.user_id = %s
        GROUP BY s.name
        ORDER BY profit DESC
        LIMIT 15
    """, (current_user.id,))''',
'''    cur.execute("""
        SELECT st.product_name AS name,
               COALESCE(SUM(s.profit),0) AS profit
        FROM sales s
        LEFT JOIN stock st ON st.id = s.stock_id
        WHERE s.user_id = %s
        GROUP BY st.product_name
        ORDER BY profit DESC
        LIMIT 15
    """, (current_user.id,))''')


# ═════════════════════════════════════════════════════════════════
print("\n[7] app.py — remove dead lru_cache import")
patch('app.py', 'remove lru_cache import',
      "from functools import lru_cache\n# KAZE Traders Business Manager",
      "# KAZE Traders Business Manager")


# ═════════════════════════════════════════════════════════════════
print("\nVerifying app.py compiles…")
r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK]   app.py compiles cleanly.")
else:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)

print("\n" + "=" * 60)
print(f"Applied: {len(APPLIED)}   Skipped: {len(SKIPPED)}   Failed: {len(FAILED)}")
if FAILED:
    print("\nFailed (pattern not found — you may have edited by hand):")
    for f in FAILED:
        print(f"  - {f}")
"""
apply_fixes_4.py — combines all outstanding fixes:
  1) the 3 never-applied fixes from apply_fixes.py (search, PDF escape, mode_runtime, Pillow)
  2) SQL fixes for all the new routes (insights, health, rfm, etc.)
Run from the folder with app.py:
    python apply_fixes_4.py
"""

import os, re, shutil, subprocess, sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
FAILED, APPLIED, SKIPPED = [], [], []


def backup(path):
    if os.path.isfile(path):
        b = f"{path}.bak.{STAMP}"
        if not os.path.isfile(b):
            shutil.copy2(path, b)


def patch(path, label, old, new, required=True):
    if not os.path.isfile(path):
        print(f"  [SKIP] {label} — {path} missing"); return
    with open(path, 'r', encoding='utf-8') as fh:
        src = fh.read()
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label} — already updated"); SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found")
            if required: FAILED.append(label)
        return
    backup(path)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(src.replace(old, new))
    print(f"  [OK]   {label}")
    APPLIED.append(label)


# ═════════════════════════════════════════════════════════════════
print("[1] mode_runtime.py — remove row limit on P/L fetch")
patch('mode_runtime.py', 'fetch_sales limit 150 -> 5000',
      "def fetch_sales(cur, user_id, limit=150):",
      "def fetch_sales(cur, user_id, limit=5000):")
patch('mode_runtime.py', 'fetch_income limit 200 -> 5000',
      "def fetch_income(cur, user_id, limit=200):",
      "def fetch_income(cur, user_id, limit=5000):")
patch('mode_runtime.py', 'fetch_expenses limit 200 -> 5000',
      "def fetch_expenses(cur, user_id, limit=200):",
      "def fetch_expenses(cur, user_id, limit=5000):")


# ═════════════════════════════════════════════════════════════════
print("\n[2] requirements.txt — add Pillow")
if os.path.isfile('requirements.txt'):
    with open('requirements.txt', 'r', encoding='utf-8') as fh:
        rq = fh.read()
    if 'Pillow' not in rq:
        backup('requirements.txt')
        if not rq.endswith('\n'): rq += '\n'
        with open('requirements.txt', 'w', encoding='utf-8') as fh:
            fh.write(rq + 'Pillow\n')
        print("  [OK]   Pillow added"); APPLIED.append('Pillow')
    else:
        print("  [SKIP] already present"); SKIPPED.append('Pillow')


# ═════════════════════════════════════════════════════════════════
print("\n[3] app.py — search() cursor ordering")
patch('app.py', 'search savepoint refactor',
'''    cur.close()
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
    return render_template('search_results.html', results=results, q=q)''',
'''    def _safe_query(sql, params):
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
        (current_user.id, like, like, like))
    session_hits = _safe_query(
        "SELECT id, customer_name as name, 'session' as type FROM service_sessions "
        "WHERE user_id = %s AND (customer_name ILIKE %s OR notes ILIKE %s) LIMIT 10",
        (current_user.id, like, like))
    bank_hits = _safe_query(
        "SELECT id, name, 'bank' as type FROM bank_accounts "
        "WHERE user_id = %s AND (name ILIKE %s OR bank_name ILIKE %s) LIMIT 8",
        (current_user.id, like, like))
    invest_hits = _safe_query(
        "SELECT id, name, 'investment' as type FROM investments "
        "WHERE user_id = %s AND name ILIKE %s LIMIT 8",
        (current_user.id, like))
    shop_hits = _safe_query(
        "SELECT id, title as name, 'listing' as type FROM shop_listings "
        "WHERE user_id = %s AND (title ILIKE %s OR description ILIKE %s) LIMIT 8",
        (current_user.id, like, like))

    cur.close()
    conn.close()

    results = (list(customers) + list(products) + list(docs) + list(note_hits)
               + list(task_hits) + list(book_hits) + list(sku_hits)
               + list(service_hits) + list(session_hits)
               + list(bank_hits) + list(invest_hits) + list(shop_hits))
    return render_template('search_results.html', results=results, q=q)''')


# ═════════════════════════════════════════════════════════════════
print("\n[4] app.py — PDF escape in _build_pdf")
patch('app.py', 'PDF escape helper',
'''def _build_pdf(buffer, title, business_name, meta_lines, table_data, footer_lines=None):
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor('#1f8a3d'), alignment=TA_LEFT)
    elements = []

    header_text = []
    if business_name:
        header_text.append(Paragraph(business_name, styles['Heading2']))
    header_text.append(Paragraph(title, title_style))''',
'''def _build_pdf(buffer, title, business_name, meta_lines, table_data, footer_lines=None):
    from xml.sax.saxutils import escape as _xml_escape
    def _safe_paragraph(text, style):
        return Paragraph(_xml_escape(str(text)), style)
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor('#1f8a3d'), alignment=TA_LEFT)
    elements = []

    header_text = []
    if business_name:
        header_text.append(_safe_paragraph(business_name, styles['Heading2']))
    header_text.append(_safe_paragraph(title, title_style))''')
patch('app.py', 'PDF table cell escape',
      "    table = Table(table_data, hAlign='LEFT')",
      "    safe_table = [[_xml_escape(str(cell)) for cell in row] for row in table_data]\n    table = Table(safe_table, hAlign='LEFT')")


# ═════════════════════════════════════════════════════════════════
print("\n[5] app.py — pay_plan uses stored_key")
patch('app.py', 'pay_plan stored_key',
      "    current = plan_info(settings)\n    if PLAN_RANK[wanted] <= PLAN_RANK[current['key']]:",
      "    current = plan_info(settings)\n    if PLAN_RANK[wanted] <= PLAN_RANK[current['stored_key']]:")


# ═════════════════════════════════════════════════════════════════
print("\n[6] app.py — SQL fixes for new routes")

# /insights
patch('app.py', 'insights SQL fix',
'''    cur.execute("SELECT COALESCE(SUM(total),0) as sales FROM sales WHERE user_id=%s AND date >= CURRENT_DATE - INTERVAL '30 days'", (current_user.id,))
    recent_sales = cur.fetchone()['sales']
    cur.execute("SELECT COUNT(*) as low FROM stock WHERE user_id=%s AND quantity <= low_stock_threshold", (current_user.id,))
    low_stock = cur.fetchone()['low']''',
'''    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS sales FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY-MM-DD')",
        (current_user.id,))
    recent_sales = (cur.fetchone() or {}).get('sales') or 0
    cur.execute(
        "SELECT COUNT(*) AS low FROM stock st "
        "WHERE st.user_id=%s AND st.quantity <= COALESCE("
        "(SELECT low_stock_threshold FROM settings WHERE user_id=%s), 10)",
        (current_user.id, current_user.id))
    low_stock = (cur.fetchone() or {}).get('low') or 0''')

# /health
patch('app.py', 'health SQL fix',
'''    cur.execute("SELECT COALESCE(SUM(total),0) as sales FROM sales WHERE user_id=%s AND date >= CURRENT_DATE - INTERVAL '30 days'", (current_user.id,))
    sales = cur.fetchone()['sales'] or 0
    cur.execute("SELECT COUNT(*) as low FROM stock WHERE user_id=%s AND quantity <= COALESCE(low_stock_threshold,5)", (current_user.id,))
    low = cur.fetchone()['low'] or 0''',
'''    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS sales FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY-MM-DD')",
        (current_user.id,))
    sales = (cur.fetchone() or {}).get('sales') or 0
    cur.execute(
        "SELECT COUNT(*) AS low FROM stock st "
        "WHERE st.user_id=%s AND st.quantity <= COALESCE("
        "(SELECT low_stock_threshold FROM settings WHERE user_id=%s), 5)",
        (current_user.id, current_user.id))
    low = (cur.fetchone() or {}).get('low') or 0''')

# /rfm
patch('app.py', 'rfm SQL fix',
'''    cur.execute("""
        SELECT c.name, 
               MAX(s.date) as last_purchase,
               COUNT(s.id) as frequency,
               COALESCE(SUM(s.total),0) as monetary
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id = %s
        GROUP BY c.id, c.name
        ORDER BY monetary DESC
        LIMIT 20
    """, (current_user.id,))''',
'''    cur.execute("""
        SELECT c.name,
               MAX(s.sale_date) AS last_purchase,
               COUNT(s.id) AS frequency,
               COALESCE(SUM(s.total_amount),0) AS monetary
        FROM customers c
        LEFT JOIN sales s ON s.customer_id = c.id AND s.user_id = c.user_id
        WHERE c.user_id = %s
        GROUP BY c.id, c.name
        ORDER BY monetary DESC
        LIMIT 20
    """, (current_user.id,))''')

# /collections
patch('app.py', 'collections SQL fix',
'''    cur.execute("""
        SELECT c.name, SUM(s.total - COALESCE(s.paid,0)) as outstanding
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.user_id = %s AND (s.total - COALESCE(s.paid,0)) > 0
        GROUP BY c.id, c.name
        ORDER BY outstanding DESC
        LIMIT 15
    """, (current_user.id,))''',
'''    cur.execute("""
        SELECT c.name, COALESCE(SUM(s.total_amount),0) AS outstanding
        FROM sales s
        JOIN customers c ON s.customer_id = c.id
        WHERE s.user_id = %s AND COALESCE(s.payment_method,'cash') NOT IN ('cash')
        GROUP BY c.id, c.name
        HAVING COALESCE(SUM(s.total_amount),0) > 0
        ORDER BY outstanding DESC
        LIMIT 15
    """, (current_user.id,))''')

# /loyalty
patch('app.py', 'loyalty SQL fix',
'''    cur.execute("SELECT name, COALESCE(SUM(total),0) as spent FROM customers c LEFT JOIN sales s ON s.customer_id=c.id WHERE c.user_id=%s GROUP BY c.id ORDER BY spent DESC LIMIT 15", (current_user.id,))''',
'''    cur.execute(
        "SELECT c.name, COALESCE(SUM(s.total_amount),0) AS spent "
        "FROM customers c LEFT JOIN sales s ON s.customer_id=c.id AND s.user_id=c.user_id "
        "WHERE c.user_id=%s GROUP BY c.id, c.name ORDER BY spent DESC LIMIT 15",
        (current_user.id,))''')

# /expense_analytics
patch('app.py', 'expense_analytics SQL fix',
'''    cur.execute("SELECT category, COALESCE(SUM(amount),0) as total FROM cashbook WHERE user_id=%s AND type='expense' GROUP BY category ORDER BY total DESC LIMIT 10", (current_user.id,))''',
'''    cur.execute(
        "SELECT category, COALESCE(SUM(amount),0) AS total FROM cash_books "
        "WHERE user_id=%s AND entry_type='out' GROUP BY category ORDER BY total DESC LIMIT 10",
        (current_user.id,))''')

# /top_customers
patch('app.py', 'top_customers SQL fix',
'''    cur.execute("SELECT c.name, COALESCE(SUM(s.total),0) as total FROM customers c LEFT JOIN sales s ON s.customer_id=c.id WHERE c.user_id=%s GROUP BY c.id ORDER BY total DESC LIMIT 10", (current_user.id,))''',
'''    cur.execute(
        "SELECT c.name, COALESCE(SUM(s.total_amount),0) AS total "
        "FROM customers c LEFT JOIN sales s ON s.customer_id=c.id AND s.user_id=c.user_id "
        "WHERE c.user_id=%s GROUP BY c.id, c.name ORDER BY total DESC LIMIT 10",
        (current_user.id,))''')

# /daily_summary
patch('app.py', 'daily_summary SQL fix',
'''    cur.execute("SELECT COALESCE(SUM(total_amount),0) as sales FROM sales WHERE user_id=%s AND sale_date = CURRENT_DATE", (current_user.id,))
    today_sales = cur.fetchone()['sales']''',
'''    cur.execute(
        "SELECT COALESCE(SUM(total_amount),0) AS sales FROM sales "
        "WHERE user_id=%s AND sale_date = to_char(CURRENT_DATE, 'YYYY-MM-DD')",
        (current_user.id,))
    today_sales = (cur.fetchone() or {}).get('sales') or 0''')

# /forecast
patch('app.py', 'forecast SQL fix',
'''    cur.execute("SELECT COALESCE(AVG(total),0) as avg_daily FROM sales WHERE user_id=%s AND date >= CURRENT_DATE - INTERVAL '30 days'", (current_user.id,))
    avg = cur.fetchone()['avg_daily'] or 0''',
'''    cur.execute(
        "SELECT COALESCE(AVG(total_amount),0) AS avg_daily FROM sales "
        "WHERE user_id=%s AND sale_date >= to_char(CURRENT_DATE - INTERVAL '30 days', 'YYYY-MM-DD')",
        (current_user.id,))
    avg = (cur.fetchone() or {}).get('avg_daily') or 0''')

# /sales/margin-alert
patch('app.py', 'sales_margin_alert SQL fix',
'''        SELECT s.product_name, AVG(s.selling_price_at_time) as avg_sell, AVG(COALESCE(st.cost_price,0)) as avg_cost
        FROM sales s LEFT JOIN stock st ON s.stock_id = st.id''',
'''        SELECT st.product_name, AVG(s.selling_price_at_time) AS avg_sell, AVG(COALESCE(st.cost_price,0)) AS avg_cost
        FROM sales s LEFT JOIN stock st ON s.stock_id = st.id''')

# /sales/velocity
patch('app.py', 'sales_velocity SQL fix',
'''        SELECT product_name, SUM(quantity_sold)/14.0 as vel FROM sales
        WHERE user_id=%s AND sale_date >= CURRENT_DATE - INTERVAL '14 days'
        GROUP BY product_name ORDER BY vel DESC LIMIT 12''',
'''        SELECT st.product_name, SUM(s.quantity_sold)/14.0 AS vel
        FROM sales s JOIN stock st ON st.id = s.stock_id
        WHERE s.user_id=%s AND s.sale_date >= to_char(CURRENT_DATE - INTERVAL '14 days', 'YYYY-MM-DD')
        GROUP BY st.product_name ORDER BY vel DESC LIMIT 12''')

# /reminders/context
patch('app.py', 'reminders_context SQL fix',
'''    cur.execute("SELECT title, due_date FROM reminders WHERE user_id=%s AND done=0 LIMIT 8", (current_user.id,))
    rows = cur.fetchall()''',
'''    cur.execute(
        "SELECT title, due_date FROM tasks WHERE user_id=%s AND done=0 LIMIT 8",
        (current_user.id,))
    rows = cur.fetchall()''')

# /team/permissions
patch('app.py', 'team_permissions SQL fix',
'''    cur.execute("SELECT username, role FROM users WHERE id=%s OR invited_by=%s", (current_user.id, current_user.id))
    rows = cur.fetchall()''',
'''    cur.execute(
        "SELECT username, role FROM users WHERE id=%s OR owner_id=%s",
        (current_user.id, current_user.id))
    rows = cur.fetchall()''')

# /profit_matrix
patch('app.py', 'profit_matrix SQL fix',
'''    cur.execute("""
        SELECT s.name, SUM(si.quantity * (si.price - COALESCE(st.cost_price,0))) as profit
        FROM sales_items si
        JOIN sales s ON si.sale_id = s.id
        LEFT JOIN stock st ON si.product_name = st.name AND st.user_id = s.user_id
        WHERE s.user_id = %s
        GROUP BY s.name
        ORDER BY profit DESC
        LIMIT 15
    """, (current_user.id,))''',
'''    cur.execute("""
        SELECT st.product_name AS name,
               COALESCE(SUM(s.profit),0) AS profit
        FROM sales s
        LEFT JOIN stock st ON st.id = s.stock_id
        WHERE s.user_id = %s
        GROUP BY st.product_name
        ORDER BY profit DESC
        LIMIT 15
    """, (current_user.id,))''')


# ═════════════════════════════════════════════════════════════════
print("\n[7] app.py — remove dead lru_cache import")
patch('app.py', 'remove lru_cache import',
      "from functools import lru_cache\n# KAZE Traders Business Manager",
      "# KAZE Traders Business Manager")


# ═════════════════════════════════════════════════════════════════
print("\nVerifying app.py compiles…")
r = subprocess.run([sys.executable, '-m', 'py_compile', 'app.py'],
                   capture_output=True, text=True)
if r.returncode == 0:
    print("  [OK]   app.py compiles cleanly.")
else:
    print("  [FAIL] app.py syntax error:")
    print(r.stderr)

print("\n" + "=" * 60)
print(f"Applied: {len(APPLIED)}   Skipped: {len(SKIPPED)}   Failed: {len(FAILED)}")
if FAILED:
    print("\nFailed (pattern not found — you may have edited by hand):")
    for f in FAILED:
        print(f"  - {f}")
print("=" * 60)