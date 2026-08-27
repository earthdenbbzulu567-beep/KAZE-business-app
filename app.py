# Business App - Web Version with PostgreSQL (Aiven)
# Merged version: includes original features + activity feed, pagination, bulk stock actions,
# global search, enhanced reports, and timesince filter.

from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import io
import csv
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
import re

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# --------------------- Helper: time since (for activity feed) ---------------------
@app.template_filter('timesince')
def timesince_filter(dt):
    """
    Jinja filter to show relative time like "2 hours ago".
    Expects dt as a datetime object or string.
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            return dt
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        m = int(seconds // 60)
        return f"{m} minute{'s' if m > 1 else ''} ago"
    elif seconds < 86400:
        h = int(seconds // 3600)
        return f"{h} hour{'s' if h > 1 else ''} ago"
    elif seconds < 604800:
        d = int(seconds // 86400)
        return f"{d} day{'s' if d > 1 else ''} ago"
    else:
        return dt.strftime('%Y-%m-%d %H:%M')

# --------------------- Login setup ---------------------
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# --------------------- Database ---------------------
def get_db():
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT DEFAULT 'owner'")
    cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS owner_id INTEGER REFERENCES users(id)")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            doc_type TEXT NOT NULL,
            title TEXT NOT NULL,
            client TEXT NOT NULL,
            amount REAL,
            date TEXT NOT NULL,
            notes TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cash_books (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            entry_type TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            unit TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            address TEXT,
            notes TEXT
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            stock_id INTEGER NOT NULL REFERENCES stock(id),
            quantity_sold REAL NOT NULL,
            selling_price_at_time REAL NOT NULL,
            total_amount REAL NOT NULL,
            profit REAL NOT NULL,
            sale_date TEXT NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            customer_id INTEGER REFERENCES customers(id)
        )
    ''')
    cur.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS customer_id INTEGER REFERENCES customers(id)")
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            low_stock_threshold REAL DEFAULT 10,
            email_notifications INTEGER DEFAULT 1,
            notify_email TEXT,
            theme TEXT DEFAULT 'dark',
            font_family TEXT DEFAULT 'Inter',
            font_size TEXT DEFAULT 'medium',
            default_chart_type TEXT DEFAULT 'line',
            animations_enabled INTEGER DEFAULT 1,
            show_low_stock_widget INTEGER DEFAULT 1,
            show_sales_trend INTEGER DEFAULT 1,
            about_text TEXT DEFAULT '',
            currency_code TEXT DEFAULT 'USD',
            currency_symbol TEXT DEFAULT '$',
            tax_rate REAL DEFAULT 0,
            business_name TEXT DEFAULT '',
            monthly_revenue_goal REAL DEFAULT 0,
            tutorial_completed INTEGER DEFAULT 0
        )
    ''')
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS currency_code TEXT DEFAULT 'USD'")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS currency_symbol TEXT DEFAULT '$'")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS tax_rate REAL DEFAULT 0")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS business_name TEXT DEFAULT ''")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS monthly_revenue_goal REAL DEFAULT 0")
    cur.execute("ALTER TABLE settings ADD COLUMN IF NOT EXISTS tutorial_completed INTEGER DEFAULT 0")
    # User activity log (for tracking logins)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS user_activity (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            username TEXT NOT NULL,
            login_time TEXT NOT NULL,
            ip_address TEXT
        )
    ''')
    # SWOT
    cur.execute('''
        CREATE TABLE IF NOT EXISTS swot_analyses (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            strengths TEXT,
            weaknesses TEXT,
            opportunities TEXT,
            threats TEXT,
            created_date TEXT NOT NULL
        )
    ''')
    # Business plan
    cur.execute('''
        CREATE TABLE IF NOT EXISTS business_plans (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
            business_name TEXT DEFAULT '',
            mission TEXT DEFAULT '',
            products_services TEXT DEFAULT '',
            target_market TEXT DEFAULT '',
            marketing_strategy TEXT DEFAULT '',
            operations_plan TEXT DEFAULT '',
            financial_plan TEXT DEFAULT '',
            goals TEXT DEFAULT '',
            updated_date TEXT
        )
    ''')
    # Recurring
    cur.execute('''
        CREATE TABLE IF NOT EXISTS recurring_items (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            item_type TEXT NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT DEFAULT '',
            client TEXT DEFAULT '',
            frequency TEXT NOT NULL DEFAULT 'monthly',
            next_run_date TEXT NOT NULL,
            active INTEGER DEFAULT 1,
            created_date TEXT NOT NULL
        )
    ''')
    # Suppliers
    cur.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            name TEXT NOT NULL,
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        )
    ''')
    # Purchase orders
    cur.execute('''
        CREATE TABLE IF NOT EXISTS purchase_orders (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            supplier_id INTEGER REFERENCES suppliers(id),
            item_description TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_cost REAL NOT NULL,
            total_cost REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            order_date TEXT NOT NULL,
            expected_date TEXT DEFAULT '',
            stock_id INTEGER REFERENCES stock(id)
        )
    ''')
    # Budgets
    cur.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            category TEXT NOT NULL,
            monthly_limit REAL NOT NULL,
            created_date TEXT NOT NULL,
            UNIQUE(user_id, category)
        )
    ''')
    # Notifications
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            message TEXT NOT NULL,
            category TEXT DEFAULT 'info',
            is_read INTEGER DEFAULT 0,
            created_date TEXT NOT NULL
        )
    ''')
    # ─── NEW: Activities table ───
    cur.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cur.close()
    conn.close()

init_db()

# --------------------- Helper: log activity ---------------------
def log_activity(user_id, username, action, details=None):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO activities (user_id, username, action, details, created_at)
        VALUES (%s, %s, %s, %s, NOW())
    ''', (user_id, username, action, details))
    conn.commit()
    cur.close()
    conn.close()

# --------------------- Email function ---------------------
def send_email(to_email, subject, body):
    from_email = os.environ.get('MAIL_USERNAME')
    password = os.environ.get('MAIL_PASSWORD')
    if not from_email or not password:
        print("Email error: MAIL_USERNAME/MAIL_PASSWORD environment variables are not set")
        return False
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# --------------------- User class ---------------------
def _business_id_for(role, owner_id, own_id):
    if role == 'staff' and owner_id:
        return owner_id
    return own_id

class User(UserMixin):
    def __init__(self, db_id, username, email, role='owner', owner_id=None):
        self.db_id = db_id
        self.username = username
        self.email = email
        self.role = role or 'owner'
        self.owner_id = owner_id
        self.id = _business_id_for(self.role, self.owner_id, self.db_id)

    def get_id(self):
        return str(self.db_id)

@app.context_processor
def inject_settings():
    if current_user.is_authenticated:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM settings WHERE user_id = %s', (current_user.id,))
        settings = cur.fetchone()
        cur.execute('SELECT COUNT(*) as unread_count FROM notifications WHERE user_id = %s AND is_read = 0', (current_user.id,))
        unread_row = cur.fetchone()
        cur.close()
        conn.close()
        return dict(user_settings=settings, unread_notifications=unread_row['unread_count'] if unread_row else 0)
    return dict(user_settings=None, unread_notifications=0)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email, role, owner_id FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'], user['role'], user['owner_id'])
    return None

# ======================== Routes ========================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed = generate_password_hash(password)
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                        (username, email, hashed))
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except psycopg2.IntegrityError:
            conn.rollback()
            flash('Username or email already exists. Try another.', 'danger')
        finally:
            cur.close()
            conn.close()
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_input = request.form['login_input']
        password = request.form['password']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s OR email = %s', (login_input, login_input))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['email'], user.get('role'), user.get('owner_id')))
            # Log activity
            try:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                business_id = _business_id_for(user.get('role'), user.get('owner_id'), user['id'])
                conn = get_db()
                cur = conn.cursor()
                cur.execute('INSERT INTO user_activity (user_id, username, login_time, ip_address) VALUES (%s, %s, %s, %s)',
                            (business_id, user['username'], now, ip))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                print(f"Activity log error: {e}")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    _process_due_recurring_items(current_user.id)
    conn = get_db()
    cur = conn.cursor()
    
    # Low stock items
    cur.execute('SELECT low_stock_threshold FROM settings WHERE user_id = %s', (current_user.id,))
    row = cur.fetchone()
    threshold = row['low_stock_threshold'] if row else 10
    cur.execute('SELECT product_name, quantity, unit FROM stock WHERE user_id = %s AND quantity < %s',
                (current_user.id, threshold))
    low_stock_items = cur.fetchall()
    
    # Sales trend last 7 days
    sales_trend = {}
    for i in range(7):
        d = (datetime.today() - timedelta(days=i)).strftime('%Y-%m-%d')
        sales_trend[d] = 0
    cur.execute('''
        SELECT sale_date, SUM(total_amount) as total 
        FROM sales 
        WHERE user_id = %s AND sale_date::date >= (NOW() - INTERVAL '7 days')::date
        GROUP BY sale_date
    ''', (current_user.id,))
    for row in cur.fetchall():
        sales_trend[row['sale_date']] = row['total']
    
    # Income / expenses
    cur.execute('SELECT * FROM income WHERE user_id = %s ORDER BY date DESC', (current_user.id,))
    income = cur.fetchall()
    cur.execute('SELECT * FROM expenses WHERE user_id = %s ORDER BY date DESC', (current_user.id,))
    expenses = cur.fetchall()
    
    total_income = sum(i['amount'] for i in income)
    total_expenses = sum(e['amount'] for e in expenses)
    
    cur.execute('SELECT SUM(profit) as total_profit FROM sales WHERE user_id = %s', (current_user.id,))
    sales_data = cur.fetchone()
    total_sales_profit = sales_data['total_profit'] or 0
    
    cur.execute('SELECT SUM(amount) as total_in FROM cash_books WHERE user_id = %s AND entry_type = %s',
                (current_user.id, 'in'))
    cash_in = cur.fetchone()['total_in'] or 0
    cur.execute('SELECT SUM(amount) as total_out FROM cash_books WHERE user_id = %s AND entry_type = %s',
                (current_user.id, 'out'))
    cash_out = cur.fetchone()['total_out'] or 0
    cash_net = cash_in - cash_out
    
    total_profit = (total_income - total_expenses) + total_sales_profit + cash_net
    
    # Monthly revenue goal progress
    cur.execute('SELECT monthly_revenue_goal, tutorial_completed FROM settings WHERE user_id = %s', (current_user.id,))
    goal_row = cur.fetchone()
    monthly_goal = (goal_row['monthly_revenue_goal'] if goal_row else 0) or 0
    tutorial_completed = (goal_row['tutorial_completed'] if goal_row else 0) or 0
    month_start = datetime.today().replace(day=1).strftime('%Y-%m-%d')
    cur.execute('''
        SELECT COALESCE(SUM(total_amount), 0) as month_revenue FROM sales
        WHERE user_id = %s AND sale_date >= %s
    ''', (current_user.id, month_start))
    month_revenue = cur.fetchone()['month_revenue'] or 0
    goal_progress_pct = min(100, round((month_revenue / monthly_goal) * 100, 1)) if monthly_goal else 0
    
    income_by_date = {}
    for item in income:
        income_by_date[item['date']] = income_by_date.get(item['date'], 0) + item['amount']
    expense_by_date = {}
    for item in expenses:
        expense_by_date[item['date']] = expense_by_date.get(item['date'], 0) + item['amount']
    
    # ─── Activity feed ───
    cur.execute('''
        SELECT username, action, details, created_at
        FROM activities
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 10
    ''', (current_user.id,))
    activities = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('dashboard.html',
                         income=income,
                         expenses=expenses,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         profit=total_profit,
                         sales_profit=total_sales_profit,
                         cash_net=cash_net,
                         income_by_date=income_by_date,
                         expense_by_date=expense_by_date,
                         low_stock_items=low_stock_items,
                         sales_trend_data=sales_trend,
                         monthly_goal=monthly_goal,
                         month_revenue=month_revenue,
                         goal_progress_pct=goal_progress_pct,
                         tutorial_completed=tutorial_completed,
                         activities=activities)

# ======================== Add Income / Expense ========================

@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    source = request.form['source']
    amount = float(request.form['amount'])
    date = request.form['date'] or datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO income (user_id, source, amount, date) VALUES (%s, %s, %s, %s)',
                (current_user.id, source, amount, date))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Added income', f'{source} ${amount:.2f}')
    flash('Income added!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/add_expense', methods=['POST'])
@login_required
def add_expense():
    name = request.form['name']
    amount = float(request.form['amount'])
    category = request.form['category']
    date = request.form['date'] or datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO expenses (user_id, name, amount, category, date) VALUES (%s, %s, %s, %s, %s)',
                (current_user.id, name, amount, category, date))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Added expense', f'{name} ${amount:.2f}')
    flash('Expense added!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_income/<int:id>')
@login_required
def delete_income(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM income WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Deleted income', f'ID {id}')
    flash('Income deleted', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM expenses WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Deleted expense', f'ID {id}')
    flash('Expense deleted', 'success')
    return redirect(url_for('dashboard'))

# ======================== Documents ========================

@app.route('/docs')
@login_required
def docs():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM documents WHERE user_id = %s ORDER BY id DESC', (current_user.id,))
    user_docs = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('docs.html', docs=user_docs)

@app.route('/docs/add', methods=['POST'])
@login_required
def add_doc():
    doc_type = request.form['doc_type']
    title = request.form['title']
    client = request.form['client']
    amount = request.form.get('amount')
    amount = float(amount) if amount else None
    date = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
    notes = request.form.get('notes')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO documents (user_id, doc_type, title, client, amount, date, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (current_user.id, doc_type, title, client, amount, date, notes))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Created document', title)
    flash('Document saved!', 'success')
    return redirect(url_for('docs'))

@app.route('/docs/delete/<int:id>')
@login_required
def delete_doc(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM documents WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Deleted document', f'ID {id}')
    flash('Document deleted.', 'success')
    return redirect(url_for('docs'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ======================== Customers ========================

@app.route('/customers')
@login_required
def customers():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as total FROM customers WHERE user_id = %s', (current_user.id,))
    total = cur.fetchone()['total']
    
    cur.execute('''
        SELECT * FROM customers WHERE user_id = %s ORDER BY name
        LIMIT %s OFFSET %s
    ''', (current_user.id, per_page, offset))
    all_customers = cur.fetchall()
    
    cur.execute('''
        SELECT customer_id, COALESCE(SUM(total_amount), 0) as total_spent, COUNT(*) as order_count
        FROM sales WHERE user_id = %s AND customer_id IS NOT NULL
        GROUP BY customer_id
    ''', (current_user.id,))
    spend_by_customer = {row['customer_id']: row for row in cur.fetchall()}
    cur.close()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    return render_template('customers.html', 
                         customers=all_customers,
                         spend_by_customer=spend_by_customer,
                         page=page,
                         total_pages=total_pages,
                         per_page=per_page)

@app.route('/customers/add', methods=['POST'])
@login_required
def add_customer():
    name = request.form['name']
    email = request.form.get('email', '')
    phone = request.form.get('phone', '')
    address = request.form.get('address', '')
    notes = request.form.get('notes', '')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO customers (user_id, name, email, phone, address, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (current_user.id, name, email, phone, address, notes))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Added customer', name)
    flash('Customer added.', 'success')
    return redirect(url_for('customers'))

@app.route('/customers/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM customers WHERE id = %s AND user_id = %s', (id, current_user.id))
    customer = cur.fetchone()
    if not customer:
        flash('Customer not found.', 'danger')
        return redirect(url_for('customers'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        address = request.form.get('address', '')
        notes = request.form.get('notes', '')
        cur.execute('''
            UPDATE customers SET name=%s, email=%s, phone=%s, address=%s, notes=%s
            WHERE id=%s AND user_id=%s
        ''', (name, email, phone, address, notes, id, current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        log_activity(current_user.id, current_user.username, 'Updated customer', name)
        flash('Customer updated.', 'success')
        return redirect(url_for('customers'))

    cur.close()
    conn.close()
    return render_template('edit_customer.html', customer=customer)

@app.route('/customers/delete/<int:id>')
@login_required
def delete_customer(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM customers WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Deleted customer', f'ID {id}')
    flash('Customer deleted.', 'success')
    return redirect(url_for('customers'))

# ======================== Stock Management ========================

@app.route('/stock')
@login_required
def stock():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as total FROM stock WHERE user_id = %s', (current_user.id,))
    total = cur.fetchone()['total']
    
    cur.execute('''
        SELECT * FROM stock WHERE user_id = %s
        ORDER BY product_name
        LIMIT %s OFFSET %s
    ''', (current_user.id, per_page, offset))
    items = cur.fetchall()
    cur.close()
    conn.close()
    
    product_names = [item['product_name'] for item in items]
    inventory_values = [item['quantity'] * item['cost_price'] for item in items]
    total_pages = (total + per_page - 1) // per_page
    return render_template('stock.html', 
                         items=items,
                         product_names=product_names,
                         inventory_values=inventory_values,
                         page=page,
                         total_pages=total_pages,
                         per_page=per_page)

@app.route('/stock/add', methods=['POST'])
@login_required
def add_stock():
    product_name = request.form['product_name']
    quantity = float(request.form['quantity'])
    cost_price = float(request.form['cost_price'])
    selling_price = float(request.form['selling_price'])
    unit = request.form.get('unit', '')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO stock (user_id, product_name, quantity, cost_price, selling_price, unit)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (current_user.id, product_name, quantity, cost_price, selling_price, unit))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Added stock', f'{product_name} qty {quantity}')
    flash('Stock item added.', 'success')
    return redirect(url_for('stock'))

@app.route('/stock/update/<int:id>', methods=['POST'])
@login_required
def update_stock(id):
    new_quantity = float(request.form['quantity'])
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute('SELECT product_name FROM stock WHERE id = %s AND user_id = %s', (id, current_user.id))
    product = cur.fetchone()
    if not product:
        flash('Stock item not found.', 'danger')
        return redirect(url_for('stock'))
    
    cur.execute('SELECT email FROM users WHERE id = %s', (current_user.id,))
    user = cur.fetchone()
    user_email = user['email']
    
    cur.execute('SELECT low_stock_threshold, email_notifications, notify_email FROM settings WHERE user_id = %s',
                (current_user.id,))
    settings = cur.fetchone()
    
    cur.execute('UPDATE stock SET quantity = %s WHERE id = %s AND user_id = %s',
                (new_quantity, id, current_user.id))
    conn.commit()
    
    if settings and settings['email_notifications']:
        threshold = settings['low_stock_threshold'] or 10
        if new_quantity < threshold:
            to_email = settings['notify_email'] or user_email
            subject = f"Low Stock Alert: {product['product_name']}"
            body = f"Your product '{product['product_name']}' has only {new_quantity} units left (threshold {threshold}). Please restock."
            send_email(to_email, subject, body)
            flash(f'Low stock alert sent to {to_email}', 'info')
    elif not settings:
        if new_quantity < 10:
            send_email(user_email, f"Low Stock: {product['product_name']}", f"{product['product_name']} is down to {new_quantity}.")
            flash('Low stock alert sent (default settings).', 'info')
    
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Updated stock', f'{product["product_name"]} to {new_quantity}')
    flash('Stock updated.', 'success')
    return redirect(url_for('stock'))

@app.route('/stock/delete/<int:id>')
@login_required
def delete_stock(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM stock WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Deleted stock', f'ID {id}')
    flash('Stock item deleted.', 'success')
    return redirect(url_for('stock'))

@app.route('/stock/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_stock(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM stock WHERE id = %s AND user_id = %s', (id, current_user.id))
    item = cur.fetchone()
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('stock'))
    
    if request.method == 'POST':
        product_name = request.form['product_name']
        quantity = float(request.form['quantity'])
        cost_price = float(request.form['cost_price'])
        selling_price = float(request.form['selling_price'])
        unit = request.form.get('unit', '')
        cur.execute('''
            UPDATE stock 
            SET product_name=%s, quantity=%s, cost_price=%s, selling_price=%s, unit=%s
            WHERE id=%s AND user_id=%s
        ''', (product_name, quantity, cost_price, selling_price, unit, id, current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        log_activity(current_user.id, current_user.username, 'Edited stock', product_name)
        flash('Stock updated.', 'success')
        return redirect(url_for('stock'))
    
    cur.close()
    conn.close()
    return render_template('edit_stock.html', item=item)

@app.route('/stock/check_low_stock')
@login_required
def check_low_stock():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT low_stock_threshold, email_notifications, notify_email FROM settings WHERE user_id = %s',
                (current_user.id,))
    settings_row = cur.fetchone()
    threshold = settings_row['low_stock_threshold'] if settings_row else 10
    to_email = (settings_row['notify_email'] if settings_row else None) or current_user.email

    cur.execute('SELECT product_name, quantity, unit FROM stock WHERE user_id = %s AND quantity < %s',
                (current_user.id, threshold))
    low_items = cur.fetchall()
    cur.close()
    conn.close()

    if not low_items:
        flash('No items are currently below the low stock threshold.', 'info')
        return redirect(url_for('stock'))

    body = f"Low Stock Report (threshold: {threshold})\n\n"
    for item in low_items:
        body += f"- {item['product_name']}: {item['quantity']} {item['unit'] or ''} remaining\n"
    send_email(to_email, "Low Stock Report", body)
    _notify(current_user.id, f"Low stock report sent: {len(low_items)} item(s) below threshold.", 'low_stock')
    log_activity(current_user.id, current_user.username, 'Checked low stock', f'{len(low_items)} items')
    flash(f'Low stock report sent to {to_email} ({len(low_items)} item(s)).', 'success')
    return redirect(url_for('stock'))

# ─── Bulk actions for stock ───
@app.route('/stock/bulk', methods=['POST'])
@login_required
def stock_bulk():
    action = request.form.get('action')
    ids = request.form.getlist('selected_ids')
    if not ids:
        flash('No items selected.', 'danger')
        return redirect(url_for('stock'))
    
    conn = get_db()
    cur = conn.cursor()
    if action == 'delete':
        cur.execute('DELETE FROM stock WHERE id = ANY(%s) AND user_id = %s', (ids, current_user.id))
        conn.commit()
        log_activity(current_user.id, current_user.username, 'Bulk delete stock', f'{len(ids)} items')
        flash(f'Deleted {len(ids)} items.', 'success')
    elif action == 'update_quantity':
        new_qty = request.form.get('new_quantity')
        if new_qty is None or new_qty == '':
            flash('Please enter a new quantity.', 'danger')
            return redirect(url_for('stock'))
        cur.execute('UPDATE stock SET quantity = %s WHERE id = ANY(%s) AND user_id = %s', (new_qty, ids, current_user.id))
        conn.commit()
        log_activity(current_user.id, current_user.username, 'Bulk update stock quantity', f'{len(ids)} items to {new_qty}')
        flash(f'Updated quantity for {len(ids)} items.', 'success')
    elif action == 'export':
        cur.execute('SELECT product_name, quantity, unit, cost_price, selling_price FROM stock WHERE id = ANY(%s) AND user_id = %s', (ids, current_user.id))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return _csv_response('selected_stock.csv',
                          ['Product', 'Quantity', 'Unit', 'Cost Price', 'Selling Price'],
                          [(r['product_name'], r['quantity'], r['unit'], r['cost_price'], r['selling_price']) for r in rows])
    else:
        flash('Invalid action.', 'danger')
    cur.close()
    conn.close()
    return redirect(url_for('stock'))

# ─── Bulk actions for sales ───
@app.route('/sales/bulk', methods=['POST'])
@login_required
def sales_bulk():
    action = request.form.get('action')
    ids = request.form.getlist('selected_ids')
    if not ids:
        flash('No sales selected.', 'danger')
        return redirect(url_for('sales'))

    conn = get_db()
    cur = conn.cursor()
    if action == 'delete':
        # Restore stock for each sale before deleting
        for sid in ids:
            cur.execute('SELECT stock_id, quantity_sold FROM sales WHERE id = %s AND user_id = %s', (sid, current_user.id))
            sale = cur.fetchone()
            if sale:
                cur.execute('UPDATE stock SET quantity = quantity + %s WHERE id = %s AND user_id = %s',
                            (sale['quantity_sold'], sale['stock_id'], current_user.id))
        cur.execute('DELETE FROM sales WHERE id = ANY(%s) AND user_id = %s', (ids, current_user.id))
        conn.commit()
        log_activity(current_user.id, current_user.username, 'Bulk delete sales', f'{len(ids)} items')
        flash(f'Deleted {len(ids)} sales and restored stock.', 'success')
    elif action == 'export':
        cur.execute('''
            SELECT stock.product_name, sales.quantity_sold, sales.selling_price_at_time,
                   sales.total_amount, sales.profit, sales.sale_date, sales.customer_name, sales.customer_email
            FROM sales JOIN stock ON sales.stock_id = stock.id
            WHERE sales.id = ANY(%s) AND sales.user_id = %s
        ''', (ids, current_user.id))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return _csv_response('selected_sales.csv',
                             ['Product', 'Quantity', 'Selling Price', 'Total', 'Profit', 'Date', 'Customer', 'Customer Email'],
                             [(r['product_name'], r['quantity_sold'], r['selling_price_at_time'], r['total_amount'],
                               r['profit'], r['sale_date'], r['customer_name'], r['customer_email']) for r in rows])
    else:
        flash('Invalid action.', 'danger')
    cur.close()
    conn.close()
    return redirect(url_for('sales'))

# ─── Bulk actions for customers ───
@app.route('/customers/bulk', methods=['POST'])
@login_required
def customers_bulk():
    action = request.form.get('action')
    ids = request.form.getlist('selected_ids')
    if not ids:
        flash('No customers selected.', 'danger')
        return redirect(url_for('customers'))

    conn = get_db()
    cur = conn.cursor()
    if action == 'delete':
        cur.execute('DELETE FROM customers WHERE id = ANY(%s) AND user_id = %s', (ids, current_user.id))
        conn.commit()
        log_activity(current_user.id, current_user.username, 'Bulk delete customers', f'{len(ids)} items')
        flash(f'Deleted {len(ids)} customers.', 'success')
    elif action == 'export':
        cur.execute('SELECT name, email, phone, address, notes FROM customers WHERE id = ANY(%s) AND user_id = %s',
                    (ids, current_user.id))
        rows = [(r['name'], r['email'], r['phone'], r['address'], r['notes']) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return _csv_response('selected_customers.csv',
                             ['Name', 'Email', 'Phone', 'Address', 'Notes'], rows)
    else:
        flash('Invalid action.', 'danger')
    cur.close()
    conn.close()
    return redirect(url_for('customers'))

# ======================== Settings ========================

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO settings (user_id, notify_email) VALUES (%s, %s) ON CONFLICT (user_id) DO NOTHING',
                (current_user.id, current_user.email))
    conn.commit()
    
    if request.method == 'POST':
        low_stock_threshold = float(request.form['low_stock_threshold'])
        email_notifications = 1 if request.form.get('email_notifications') == 'on' else 0
        notify_email = request.form.get('notify_email') or current_user.email
        theme = request.form.get('theme', 'dark')
        font_family = request.form.get('font_family', 'Inter')
        font_size = request.form.get('font_size', 'medium')
        default_chart_type = request.form.get('default_chart_type', 'line')
        animations_enabled = 1 if request.form.get('animations_enabled') == 'on' else 0
        show_low_stock_widget = 1 if request.form.get('show_low_stock_widget') == 'on' else 0
        show_sales_trend = 1 if request.form.get('show_sales_trend') == 'on' else 0
        about_text = request.form.get('about_text', '')
        business_name = request.form.get('business_name', '')
        currency_code = request.form.get('currency_code', 'USD')
        currency_symbol = request.form.get('currency_symbol', '$')
        tax_rate = float(request.form.get('tax_rate') or 0)
        monthly_revenue_goal = float(request.form.get('monthly_revenue_goal') or 0)
        
        cur.execute('''
            UPDATE settings 
            SET low_stock_threshold=%s, email_notifications=%s, notify_email=%s,
                theme=%s, font_family=%s, font_size=%s, default_chart_type=%s,
                animations_enabled=%s, show_low_stock_widget=%s, show_sales_trend=%s,
                about_text=%s, business_name=%s, currency_code=%s, currency_symbol=%s, tax_rate=%s,
                monthly_revenue_goal=%s
            WHERE user_id=%s
        ''', (low_stock_threshold, email_notifications, notify_email,
              theme, font_family, font_size, default_chart_type,
              animations_enabled, show_low_stock_widget, show_sales_trend,
              about_text, business_name, currency_code, currency_symbol, tax_rate,
              monthly_revenue_goal, current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        flash('Settings saved.', 'success')
        return redirect(url_for('settings'))
    
    cur.execute('SELECT * FROM settings WHERE user_id = %s', (current_user.id,))
    settings_row = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('settings.html', settings=settings_row)

# ======================== Cash Book ========================

@app.route('/cashbook')
@login_required
def cashbook():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM cash_books WHERE user_id = %s ORDER BY date DESC', (current_user.id,))
    entries = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('cashbook.html', entries=entries)

@app.route('/cashbook/add', methods=['POST'])
@login_required
def add_cash_entry():
    entry_type = request.form['entry_type']
    category = request.form['category']
    description = request.form['description']
    amount = float(request.form['amount'])
    date = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO cash_books (user_id, entry_type, category, description, amount, date)
        VALUES (%s, %s, %s, %s, %s, %s)
    ''', (current_user.id, entry_type, category, description, amount, date))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Added cash entry', f'{entry_type} ${amount:.2f}')
    flash('Cash entry added.', 'success')
    return redirect(url_for('cashbook'))

@app.route('/cashbook/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_cash_entry(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM cash_books WHERE id = %s AND user_id = %s', (id, current_user.id))
    entry = cur.fetchone()
    if not entry:
        flash('Entry not found.', 'danger')
        return redirect(url_for('cashbook'))
    
    if request.method == 'POST':
        entry_type = request.form['entry_type']
        category = request.form['category']
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        cur.execute('''
            UPDATE cash_books 
            SET entry_type=%s, category=%s, description=%s, amount=%s, date=%s
            WHERE id=%s AND user_id=%s
        ''', (entry_type, category, description, amount, date, id, current_user.id))
        conn.commit()
        cur.close()
        conn.close()
        log_activity(current_user.id, current_user.username, 'Edited cash entry', f'ID {id}')
        flash('Cash entry updated.', 'success')
        return redirect(url_for('cashbook'))
    
    cur.close()
    conn.close()
    return render_template('edit_cashbook.html', entry=entry)

@app.route('/cashbook/delete/<int:id>')
@login_required
def delete_cash_entry(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM cash_books WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    log_activity(current_user.id, current_user.username, 'Deleted cash entry', f'ID {id}')
    flash('Cash entry deleted.', 'success')
    return redirect(url_for('cashbook'))

# ======================== Sales ========================

@app.route('/sales')
@login_required
def sales():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as total FROM sales WHERE user_id = %s', (current_user.id,))
    total = cur.fetchone()['total']
    
    cur.execute('''
        SELECT sales.*, stock.product_name 
        FROM sales 
        JOIN stock ON sales.stock_id = stock.id
        WHERE sales.user_id = %s 
        ORDER BY sale_date DESC
        LIMIT %s OFFSET %s
    ''', (current_user.id, per_page, offset))
    all_sales = cur.fetchall()
    
    cur.execute('SELECT id, product_name, selling_price, quantity FROM stock WHERE user_id = %s AND quantity > 0',
                (current_user.id,))
    stock_items = cur.fetchall()
    cur.execute('SELECT id, name, email FROM customers WHERE user_id = %s ORDER BY name', (current_user.id,))
    customer_list = cur.fetchall()
    
    sales_by_date = {}
    for sale in all_sales:
        d = sale['sale_date']
        sales_by_date[d] = sales_by_date.get(d, 0) + sale['total_amount']
    
    cur.close()
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    return render_template('sales.html', 
                         sales=all_sales,
                         stock_items=stock_items,
                         sales_by_date=sales_by_date,
                         customer_list=customer_list,
                         page=page,
                         total_pages=total_pages,
                         per_page=per_page)

@app.route('/sales/add', methods=['POST'])
@login_required
def add_sale():
    stock_id = int(request.form['stock_id'])
    quantity_sold = float(request.form['quantity'])
    customer_id = request.form.get('customer_id') or None
    customer_name = request.form.get('customer_name', '')
    customer_email = request.form.get('customer_email', '')
    sale_date = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
    
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM stock WHERE id = %s AND user_id = %s', (stock_id, current_user.id))
    stock_item = cur.fetchone()
    if not stock_item:
        flash('Stock item not found.', 'danger')
        return redirect(url_for('sales'))
    
    if stock_item['quantity'] < quantity_sold:
        flash(f'Insufficient stock. Only {stock_item["quantity"]} available.', 'danger')
        return redirect(url_for('sales'))

    if customer_id:
        cur.execute('SELECT name, email FROM customers WHERE id = %s AND user_id = %s', (customer_id, current_user.id))
        saved_customer = cur.fetchone()
        if saved_customer:
            customer_name = saved_customer['name']
            customer_email = saved_customer['email'] or customer_email
    
    selling_price = stock_item['selling_price']
    cost_price = stock_item['cost_price']
    total_amount = selling_price * quantity_sold
    profit = (selling_price - cost_price) * quantity_sold
    
    cur.execute('''
        INSERT INTO sales (user_id, stock_id, quantity_sold, selling_price_at_time, total_amount, profit, sale_date, customer_name, customer_email, customer_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (current_user.id, stock_id, quantity_sold, selling_price, total_amount, profit, sale_date, customer_name, customer_email, customer_id))
    
    new_quantity = stock_item['quantity'] - quantity_sold
    cur.execute('UPDATE stock SET quantity = %s WHERE id = %s', (new_quantity, stock_id))
    conn.commit()
    cur.close()
    conn.close()
    
    log_activity(current_user.id, current_user.username, 'Recorded sale', f'{stock_item["product_name"]} x{quantity_sold} ${total_amount:.2f}')
    flash(f'Sale recorded. Profit: ${profit:.2f}', 'success')
    return redirect(url_for('sales'))

@app.route('/sales/delete/<int:id>')
@login_required
def delete_sale(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sales WHERE id = %s AND user_id = %s', (id, current_user.id))
    sale = cur.fetchone()
    if sale:
        cur.execute('UPDATE stock SET quantity = quantity + %s WHERE id = %s', (sale['quantity_sold'], sale['stock_id']))
        cur.execute('DELETE FROM sales WHERE id = %s', (id,))
        conn.commit()
        log_activity(current_user.id, current_user.username, 'Deleted sale', f'ID {id}')
        flash('Sale deleted and stock restored.', 'success')
    else:
        flash('Sale not found.', 'danger')
    cur.close()
    conn.close()
    return redirect(url_for('sales'))

# ======================== CSV Export ========================

def _csv_response(filename, header, rows):
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return Response(
        buf.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@app.route('/export/income.csv')
@login_required
def export_income_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT source, amount, date FROM income WHERE user_id = %s ORDER BY date DESC', (current_user.id,))
    rows = [(r['source'], r['amount'], r['date']) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return _csv_response('income.csv', ['Source', 'Amount', 'Date'], rows)

@app.route('/export/expenses.csv')
@login_required
def export_expenses_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT name, amount, category, date FROM expenses WHERE user_id = %s ORDER BY date DESC', (current_user.id,))
    rows = [(r['name'], r['amount'], r['category'], r['date']) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return _csv_response('expenses.csv', ['Name', 'Amount', 'Category', 'Date'], rows)

@app.route('/export/sales.csv')
@login_required
def export_sales_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT stock.product_name, sales.quantity_sold, sales.selling_price_at_time,
               sales.total_amount, sales.profit, sales.sale_date, sales.customer_name, sales.customer_email
        FROM sales JOIN stock ON sales.stock_id = stock.id
        WHERE sales.user_id = %s ORDER BY sale_date DESC
    ''', (current_user.id,))
    rows = [(r['product_name'], r['quantity_sold'], r['selling_price_at_time'], r['total_amount'],
              r['profit'], r['sale_date'], r['customer_name'], r['customer_email']) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return _csv_response('sales.csv',
                          ['Product', 'Quantity', 'Selling Price', 'Total', 'Profit', 'Date', 'Customer', 'Customer Email'],
                          rows)

@app.route('/export/cashbook.csv')
@login_required
def export_cashbook_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT entry_type, category, description, amount, date FROM cash_books WHERE user_id = %s ORDER BY date DESC',
                (current_user.id,))
    rows = [(r['entry_type'], r['category'], r['description'], r['amount'], r['date']) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return _csv_response('cashbook.csv', ['Type', 'Category', 'Description', 'Amount', 'Date'], rows)

@app.route('/export/stock.csv')
@login_required
def export_stock_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT product_name, quantity, unit, cost_price, selling_price FROM stock WHERE user_id = %s ORDER BY product_name',
                (current_user.id,))
    rows = [(r['product_name'], r['quantity'], r['unit'], r['cost_price'], r['selling_price']) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return _csv_response('stock.csv', ['Product', 'Quantity', 'Unit', 'Cost Price', 'Selling Price'], rows)

@app.route('/export/customers.csv')
@login_required
def export_customers_csv():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT name, email, phone, address, notes FROM customers WHERE user_id = %s ORDER BY name', (current_user.id,))
    rows = [(r['name'], r['email'], r['phone'], r['address'], r['notes']) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return _csv_response('customers.csv', ['Name', 'Email', 'Phone', 'Address', 'Notes'], rows)

# ======================== CSV Import ========================

def _read_uploaded_csv(file_storage):
    """Parse an uploaded CSV file into a list of dict rows. Returns None on failure."""
    if not file_storage or file_storage.filename == '':
        return None
    try:
        stream = io.StringIO(file_storage.stream.read().decode('utf-8-sig'), newline=None)
        return list(csv.DictReader(stream))
    except Exception:
        return None

@app.route('/import/stock', methods=['POST'])
@login_required
def import_stock_csv():
    rows = _read_uploaded_csv(request.files.get('file'))
    if rows is None:
        flash('Could not read that file. Please upload a CSV exported from this app (or matching columns: Product, Quantity, Unit, Cost Price, Selling Price).', 'danger')
        return redirect(url_for('stock'))
    conn = get_db()
    cur = conn.cursor()
    count = 0
    for row in rows:
        try:
            product_name = (row.get('Product') or '').strip()
            if not product_name:
                continue
            cur.execute('''
                INSERT INTO stock (user_id, product_name, quantity, unit, cost_price, selling_price)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (current_user.id, product_name, float(row.get('Quantity') or 0),
                  row.get('Unit', ''), float(row.get('Cost Price') or 0), float(row.get('Selling Price') or 0)))
            count += 1
        except (ValueError, KeyError):
            continue
    conn.commit()
    cur.close()
    conn.close()
    flash(f'Imported {count} stock item(s).' if count else 'No rows imported — check the file has a Product column with values in it.', 'success' if count else 'danger')
    return redirect(url_for('stock'))

@app.route('/import/customers', methods=['POST'])
@login_required
def import_customers_csv():
    rows = _read_uploaded_csv(request.files.get('file'))
    if rows is None:
        flash('Could not read that file. Please upload a CSV with columns: Name, Email, Phone, Address, Notes.', 'danger')
        return redirect(url_for('customers'))
    conn = get_db()
    cur = conn.cursor()
    count = 0
    for row in rows:
        name = (row.get('Name') or '').strip()
        if not name:
            continue
        cur.execute('''
            INSERT INTO customers (user_id, name, email, phone, address, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        ''', (current_user.id, name, row.get('Email', ''), row.get('Phone', ''), row.get('Address', ''), row.get('Notes', '')))
        count += 1
    conn.commit()
    cur.close()
    conn.close()
    flash(f'Imported {count} customer(s).' if count else 'No rows imported — check the file has a Name column with values in it.', 'success' if count else 'danger')
    return redirect(url_for('customers'))

@app.route('/import/income', methods=['POST'])
@login_required
def import_income_csv():
    rows = _read_uploaded_csv(request.files.get('file'))
    if rows is None:
        flash('Could not read that file. Please upload a CSV with columns: Source, Amount, Date.', 'danger')
        return redirect(url_for('dashboard'))
    conn = get_db()
    cur = conn.cursor()
    count = 0
    for row in rows:
        try:
            source = (row.get('Source') or '').strip()
            if not source:
                continue
            cur.execute('INSERT INTO income (user_id, source, amount, date) VALUES (%s, %s, %s, %s)',
                        (current_user.id, source, float(row.get('Amount') or 0),
                         row.get('Date') or datetime.today().strftime('%Y-%m-%d')))
            count += 1
        except (ValueError, KeyError):
            continue
    conn.commit()
    cur.close()
    conn.close()
    flash(f'Imported {count} income record(s).' if count else 'No rows imported — check the file has a Source column with values in it.', 'success' if count else 'danger')
    return redirect(url_for('dashboard'))

@app.route('/import/expenses', methods=['POST'])
@login_required
def import_expenses_csv():
    rows = _read_uploaded_csv(request.files.get('file'))
    if rows is None:
        flash('Could not read that file. Please upload a CSV with columns: Name, Amount, Category, Date.', 'danger')
        return redirect(url_for('dashboard'))
    conn = get_db()
    cur = conn.cursor()
    count = 0
    for row in rows:
        try:
            name = (row.get('Name') or '').strip()
            if not name:
                continue
            cur.execute('INSERT INTO expenses (user_id, name, amount, category, date) VALUES (%s, %s, %s, %s, %s)',
                        (current_user.id, name, float(row.get('Amount') or 0),
                         row.get('Category') or 'Other', row.get('Date') or datetime.today().strftime('%Y-%m-%d')))
            count += 1
        except (ValueError, KeyError):
            continue
    conn.commit()
    cur.close()
    conn.close()
    flash(f'Imported {count} expense(s).' if count else 'No rows imported — check the file has a Name column with values in it.', 'success' if count else 'danger')
    return redirect(url_for('dashboard'))

@app.route('/import/cashbook', methods=['POST'])
@login_required
def import_cashbook_csv():
    rows = _read_uploaded_csv(request.files.get('file'))
    if rows is None:
        flash('Could not read that file. Please upload a CSV with columns: Type, Category, Description, Amount, Date.', 'danger')
        return redirect(url_for('cashbook'))
    conn = get_db()
    cur = conn.cursor()
    count = 0
    for row in rows:
        try:
            entry_type = (row.get('Type') or '').strip().lower()
            if entry_type not in ('in', 'out'):
                continue
            cur.execute('''
                INSERT INTO cash_books (user_id, entry_type, category, description, amount, date)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (current_user.id, entry_type, row.get('Category', ''), row.get('Description', ''),
                  float(row.get('Amount') or 0), row.get('Date') or datetime.today().strftime('%Y-%m-%d')))
            count += 1
        except (ValueError, KeyError):
            continue
    conn.commit()
    cur.close()
    conn.close()
    flash((f'Imported {count} cash book entr{"y" if count == 1 else "ies"}.') if count else 'No rows imported — check the file has a Type column with "in" or "out" values.', 'success' if count else 'danger')
    return redirect(url_for('cashbook'))

# ======================== PDF Generation ========================

def _get_settings_row(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM settings WHERE user_id = %s', (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def _brand_logo_image(size=36):
    """Embed the actual KAZE Traders logo image in generated PDFs."""
    logo_path = os.path.join(app.root_path, 'static', 'logo_icon.png')
    return RLImage(logo_path, width=size, height=size)

def _build_pdf(buffer, title, business_name, meta_lines, table_data, footer_lines=None):
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Title'], textColor=colors.HexColor('#1f8a3d'), alignment=TA_LEFT)
    elements = []

    header_text = []
    if business_name:
        header_text.append(Paragraph(business_name, styles['Heading2']))
    header_text.append(Paragraph(title, title_style))
    header_table = Table([[_brand_logo_image(36), header_text]], colWidths=[50, 460])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('LEFTPADDING', (1, 0), (1, 0), 8),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 12))
    for line in meta_lines:
        elements.append(Paragraph(line, styles['Normal']))
    elements.append(Spacer(1, 16))

    table = Table(table_data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a1a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)

    if footer_lines:
        elements.append(Spacer(1, 20))
        for line in footer_lines:
            elements.append(Paragraph(line, styles['Normal']))

    doc.build(elements)

@app.route('/docs/<int:id>/pdf')
@login_required
def doc_pdf(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM documents WHERE id = %s AND user_id = %s', (id, current_user.id))
    doc_row = cur.fetchone()
    cur.close()
    conn.close()
    if not doc_row:
        flash('Document not found.', 'danger')
        return redirect(url_for('docs'))

    settings_row = _get_settings_row(current_user.id)
    business_name = (settings_row['business_name'] if settings_row else '') or 'Your Business'
    symbol = (settings_row['currency_symbol'] if settings_row else '$') or '$'
    tax_rate = (settings_row['tax_rate'] if settings_row else 0) or 0

    subtotal = doc_row['amount'] or 0
    tax_amount = subtotal * (tax_rate / 100)
    total = subtotal + tax_amount

    meta_lines = [
        f"<b>Document Type:</b> {doc_row['doc_type'].capitalize()}",
        f"<b>Title:</b> {doc_row['title']}",
        f"<b>Client:</b> {doc_row['client']}",
        f"<b>Date:</b> {doc_row['date']}",
    ]
    if doc_row['notes']:
        meta_lines.append(f"<b>Notes:</b> {doc_row['notes']}")

    table_data = [['Description', 'Amount']]
    table_data.append([doc_row['title'], f"{symbol}{subtotal:.2f}"])
    if tax_rate:
        table_data.append([f"Tax ({tax_rate:.1f}%)", f"{symbol}{tax_amount:.2f}"])
    table_data.append(['Total', f"{symbol}{total:.2f}"])

    buffer = io.BytesIO()
    _build_pdf(buffer, doc_row['title'], business_name, meta_lines, table_data,
               footer_lines=[f"Generated on {datetime.today().strftime('%Y-%m-%d')}"])
    buffer.seek(0)
    safe_title = "".join(c for c in doc_row['title'] if c.isalnum() or c in (' ', '_', '-')).rstrip()
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                      download_name=f"{safe_title or 'document'}.pdf")

@app.route('/sales/<int:id>/receipt')
@login_required
def sale_receipt(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT sales.*, stock.product_name FROM sales
        JOIN stock ON sales.stock_id = stock.id
        WHERE sales.id = %s AND sales.user_id = %s
    ''', (id, current_user.id))
    sale = cur.fetchone()
    cur.close()
    conn.close()
    if not sale:
        flash('Sale not found.', 'danger')
        return redirect(url_for('sales'))

    settings_row = _get_settings_row(current_user.id)
    business_name = (settings_row['business_name'] if settings_row else '') or 'Your Business'
    symbol = (settings_row['currency_symbol'] if settings_row else '$') or '$'

    meta_lines = [
        f"<b>Receipt #:</b> {sale['id']}",
        f"<b>Date:</b> {sale['sale_date']}",
        f"<b>Customer:</b> {sale['customer_name'] or 'Walk-in'}",
    ]
    if sale['customer_email']:
        meta_lines.append(f"<b>Email:</b> {sale['customer_email']}")

    table_data = [
        ['Product', 'Quantity', 'Unit Price', 'Total'],
        [sale['product_name'], str(sale['quantity_sold']), f"{symbol}{sale['selling_price_at_time']:.2f}",
         f"{symbol}{sale['total_amount']:.2f}"],
        ['', '', 'Total', f"{symbol}{sale['total_amount']:.2f}"]
    ]

    buffer = io.BytesIO()
    _build_pdf(buffer, "Sales Receipt", business_name, meta_lines, table_data,
               footer_lines=["Thank you for your business!"])
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                      download_name=f"receipt_{sale['id']}.pdf")

# ======================== SWOT Analysis ========================

@app.route('/swot')
@login_required
def swot():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM swot_analyses WHERE user_id = %s ORDER BY created_date DESC', (current_user.id,))
    analyses = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('swot.html', analyses=analyses)

@app.route('/swot/add', methods=['POST'])
@login_required
def add_swot():
    title = request.form.get('title') or f"SWOT Analysis - {datetime.today().strftime('%Y-%m-%d')}"
    strengths = request.form.get('strengths', '')
    weaknesses = request.form.get('weaknesses', '')
    opportunities = request.form.get('opportunities', '')
    threats = request.form.get('threats', '')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO swot_analyses (user_id, title, strengths, weaknesses, opportunities, threats, created_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    ''', (current_user.id, title, strengths, weaknesses, opportunities, threats,
          datetime.today().strftime('%Y-%m-%d')))
    conn.commit()
    cur.close()
    conn.close()
    flash('SWOT analysis saved.', 'success')
    return redirect(url_for('swot'))

@app.route('/swot/delete/<int:id>')
@login_required
def delete_swot(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM swot_analyses WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('SWOT analysis deleted.', 'success')
    return redirect(url_for('swot'))

@app.route('/swot/<int:id>/pdf')
@login_required
def swot_pdf(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM swot_analyses WHERE id = %s AND user_id = %s', (id, current_user.id))
    s = cur.fetchone()
    cur.close()
    conn.close()
    if not s:
        flash('SWOT analysis not found.', 'danger')
        return redirect(url_for('swot'))

    settings_row = _get_settings_row(current_user.id)
    business_name = (settings_row['business_name'] if settings_row else '') or 'Your Business'

    meta_lines = [f"<b>Date:</b> {s['created_date']}"]
    table_data = [
        ['Category', 'Notes'],
        ['Strengths', s['strengths'] or '—'],
        ['Weaknesses', s['weaknesses'] or '—'],
        ['Opportunities', s['opportunities'] or '—'],
        ['Threats', s['threats'] or '—'],
    ]
    buffer = io.BytesIO()
    _build_pdf(buffer, s['title'], business_name, meta_lines, table_data,
               footer_lines=[f"Generated on {datetime.today().strftime('%Y-%m-%d')}"])
    buffer.seek(0)
    safe_title = "".join(c for c in s['title'] if c.isalnum() or c in (' ', '_', '-')).rstrip()
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                      download_name=f"{safe_title or 'swot'}.pdf")

# ======================== Business Plan ========================

@app.route('/business-plan', methods=['GET', 'POST'])
@login_required
def business_plan():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM business_plans WHERE user_id = %s', (current_user.id,))
    plan = cur.fetchone()

    if request.method == 'POST':
        fields = {
            'business_name': request.form.get('business_name', ''),
            'mission': request.form.get('mission', ''),
            'products_services': request.form.get('products_services', ''),
            'target_market': request.form.get('target_market', ''),
            'marketing_strategy': request.form.get('marketing_strategy', ''),
            'operations_plan': request.form.get('operations_plan', ''),
            'financial_plan': request.form.get('financial_plan', ''),
            'goals': request.form.get('goals', ''),
        }
        today = datetime.today().strftime('%Y-%m-%d')
        if plan:
            cur.execute('''
                UPDATE business_plans SET business_name=%s, mission=%s, products_services=%s,
                    target_market=%s, marketing_strategy=%s, operations_plan=%s,
                    financial_plan=%s, goals=%s, updated_date=%s
                WHERE user_id=%s
            ''', (fields['business_name'], fields['mission'], fields['products_services'],
                  fields['target_market'], fields['marketing_strategy'], fields['operations_plan'],
                  fields['financial_plan'], fields['goals'], today, current_user.id))
        else:
            cur.execute('''
                INSERT INTO business_plans (user_id, business_name, mission, products_services,
                    target_market, marketing_strategy, operations_plan, financial_plan, goals, updated_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (current_user.id, fields['business_name'], fields['mission'], fields['products_services'],
                  fields['target_market'], fields['marketing_strategy'], fields['operations_plan'],
                  fields['financial_plan'], fields['goals'], today))
        conn.commit()
        cur.close()
        conn.close()
        flash('Business plan saved.', 'success')
        return redirect(url_for('business_plan'))

    cur.close()
    conn.close()
    return render_template('business_plan.html', plan=plan)

@app.route('/business-plan/pdf')
@login_required
def business_plan_pdf():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM business_plans WHERE user_id = %s', (current_user.id,))
    plan = cur.fetchone()
    cur.close()
    conn.close()
    if not plan:
        flash('Create your business plan first.', 'info')
        return redirect(url_for('business_plan'))

    settings_row = _get_settings_row(current_user.id)
    business_name = plan['business_name'] or (settings_row['business_name'] if settings_row else '') or 'Your Business'

    meta_lines = [f"<b>Last updated:</b> {plan['updated_date'] or '—'}"]
    table_data = [
        ['Section', 'Details'],
        ['Mission', plan['mission'] or '—'],
        ['Products / Services', plan['products_services'] or '—'],
        ['Target Market', plan['target_market'] or '—'],
        ['Marketing Strategy', plan['marketing_strategy'] or '—'],
        ['Operations Plan', plan['operations_plan'] or '—'],
        ['Financial Plan', plan['financial_plan'] or '—'],
        ['Goals', plan['goals'] or '—'],
    ]
    buffer = io.BytesIO()
    _build_pdf(buffer, "Business Plan", business_name, meta_lines, table_data,
               footer_lines=[f"Generated on {datetime.today().strftime('%Y-%m-%d')}"])
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf', as_attachment=True,
                      download_name="business_plan.pdf")

# ======================== Tutorial / Onboarding ========================

@app.route('/tutorial')
@login_required
def tutorial():
    return render_template('tutorial.html')

@app.route('/tutorial/dismiss')
@login_required
def dismiss_tutorial():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE settings SET tutorial_completed = 1 WHERE user_id = %s', (current_user.id,))
    conn.commit()
    cur.close()
    conn.close()
    return ('', 204)

# ======================== Team / Staff Accounts ========================

@app.route('/team')
@login_required
def team():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email FROM users WHERE owner_id = %s AND role = 'staff' ORDER BY username",
                (current_user.id,))
    staff = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('team.html', staff=staff)

@app.route('/team/invite', methods=['POST'])
@login_required
def invite_staff():
    if current_user.role == 'staff':
        flash('Only the account owner can invite team members.', 'danger')
        return redirect(url_for('team'))
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    hashed = generate_password_hash(password)
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute('''
            INSERT INTO users (username, email, password, role, owner_id)
            VALUES (%s, %s, %s, 'staff', %s)
        ''', (username, email, hashed, current_user.id))
        conn.commit()
        flash(f'{username} added to your team. Share their username/email and password so they can log in.', 'success')
    except psycopg2.IntegrityError:
        conn.rollback()
        flash('That username or email is already taken.', 'danger')
    finally:
        cur.close()
        conn.close()
    return redirect(url_for('team'))

@app.route('/team/remove/<int:id>')
@login_required
def remove_staff(id):
    if current_user.role == 'staff':
        flash('Only the account owner can remove team members.', 'danger')
        return redirect(url_for('team'))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = %s AND owner_id = %s AND role = 'staff'", (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Team member removed.', 'success')
    return redirect(url_for('team'))

# ======================== Recurring Invoices / Expenses ========================

def _add_months(date_str, months):
    d = datetime.strptime(date_str, '%Y-%m-%d')
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, [31,29 if year%4==0 and (year%100!=0 or year%400==0) else 28,31,30,31,30,31,31,30,31,30,31][month-1])
    return d.replace(year=year, month=month, day=day).strftime('%Y-%m-%d')

def _advance_date(date_str, frequency):
    if frequency == 'weekly':
        return (datetime.strptime(date_str, '%Y-%m-%d') + timedelta(days=7)).strftime('%Y-%m-%d')
    elif frequency == 'monthly':
        return _add_months(date_str, 1)
    elif frequency == 'quarterly':
        return _add_months(date_str, 3)
    elif frequency == 'yearly':
        return _add_months(date_str, 12)
    return date_str

def _notify(user_id, message, category='info'):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO notifications (user_id, message, category, created_date) VALUES (%s, %s, %s, %s)',
                (user_id, message, category, datetime.today().strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    cur.close()
    conn.close()

def _process_due_recurring_items(user_id):
    """Auto-generate expenses/invoices for any recurring item that's come due. Safe to call often."""
    conn = get_db()
    cur = conn.cursor()
    today = datetime.today().strftime('%Y-%m-%d')
    cur.execute('SELECT * FROM recurring_items WHERE user_id = %s AND active = 1 AND next_run_date <= %s',
                (user_id, today))
    due_items = cur.fetchall()
    for item in due_items:
        if item['item_type'] == 'expense':
            cur.execute('INSERT INTO expenses (user_id, name, amount, category, date) VALUES (%s, %s, %s, %s, %s)',
                        (user_id, item['name'], item['amount'], item['category'] or 'Other', today))
        else:
            cur.execute('''
                INSERT INTO documents (user_id, doc_type, title, client, amount, date, notes)
                VALUES (%s, 'invoice', %s, %s, %s, %s, %s)
            ''', (user_id, item['name'], item['client'] or 'Recurring client', item['amount'], today,
                  'Auto-generated from a recurring invoice.'))
        new_next = _advance_date(item['next_run_date'], item['frequency'])
        cur.execute('UPDATE recurring_items SET next_run_date = %s WHERE id = %s', (new_next, item['id']))
        _notify(user_id, f"Recurring {item['item_type']} \"{item['name']}\" (${item['amount']:.2f}) was generated.", 'recurring')
    conn.commit()
    cur.close()
    conn.close()

@app.route('/recurring')
@login_required
def recurring():
    _process_due_recurring_items(current_user.id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM recurring_items WHERE user_id = %s ORDER BY active DESC, next_run_date', (current_user.id,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('recurring.html', items=items)

@app.route('/recurring/add', methods=['POST'])
@login_required
def add_recurring():
    item_type = request.form['item_type']
    name = request.form['name']
    amount = float(request.form['amount'])
    category = request.form.get('category', '')
    client = request.form.get('client', '')
    frequency = request.form.get('frequency', 'monthly')
    start_date = request.form.get('start_date') or datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO recurring_items (user_id, item_type, name, amount, category, client, frequency, next_run_date, active, created_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
    ''', (current_user.id, item_type, name, amount, category, client, frequency, start_date,
          datetime.today().strftime('%Y-%m-%d')))
    conn.commit()
    cur.close()
    conn.close()
    flash('Recurring item scheduled.', 'success')
    return redirect(url_for('recurring'))

@app.route('/recurring/toggle/<int:id>')
@login_required
def toggle_recurring(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('UPDATE recurring_items SET active = 1 - active WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('recurring'))

@app.route('/recurring/delete/<int:id>')
@login_required
def delete_recurring(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM recurring_items WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Recurring item deleted.', 'success')
    return redirect(url_for('recurring'))

# ======================== Suppliers & Purchase Orders ========================

@app.route('/suppliers')
@login_required
def suppliers():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM suppliers WHERE user_id = %s ORDER BY name', (current_user.id,))
    all_suppliers = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('suppliers.html', suppliers=all_suppliers)

@app.route('/suppliers/add', methods=['POST'])
@login_required
def add_supplier():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('INSERT INTO suppliers (user_id, name, email, phone, address, notes) VALUES (%s, %s, %s, %s, %s, %s)',
                (current_user.id, request.form['name'], request.form.get('email',''), request.form.get('phone',''),
                 request.form.get('address',''), request.form.get('notes','')))
    conn.commit()
    cur.close()
    conn.close()
    flash('Supplier added.', 'success')
    return redirect(url_for('suppliers'))

@app.route('/suppliers/delete/<int:id>')
@login_required
def delete_supplier(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM suppliers WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Supplier deleted.', 'success')
    return redirect(url_for('suppliers'))

@app.route('/purchase-orders')
@login_required
def purchase_orders():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT po.*, s.name as supplier_name FROM purchase_orders po
        LEFT JOIN suppliers s ON po.supplier_id = s.id
        WHERE po.user_id = %s ORDER BY po.order_date DESC
    ''', (current_user.id,))
    orders = cur.fetchall()
    cur.execute('SELECT id, name FROM suppliers WHERE user_id = %s ORDER BY name', (current_user.id,))
    supplier_list = cur.fetchall()
    cur.execute('SELECT id, product_name FROM stock WHERE user_id = %s ORDER BY product_name', (current_user.id,))
    stock_list = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('purchase_orders.html', orders=orders, supplier_list=supplier_list, stock_list=stock_list)

@app.route('/purchase-orders/add', methods=['POST'])
@login_required
def add_purchase_order():
    supplier_id = request.form.get('supplier_id') or None
    stock_id = request.form.get('stock_id') or None
    item_description = request.form['item_description']
    quantity = float(request.form['quantity'])
    unit_cost = float(request.form['unit_cost'])
    total_cost = quantity * unit_cost
    expected_date = request.form.get('expected_date', '')
    order_date = datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO purchase_orders (user_id, supplier_id, item_description, quantity, unit_cost, total_cost, status, order_date, expected_date, stock_id)
        VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s, %s, %s)
    ''', (current_user.id, supplier_id, item_description, quantity, unit_cost, total_cost, order_date, expected_date, stock_id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Purchase order created.', 'success')
    return redirect(url_for('purchase_orders'))

@app.route('/purchase-orders/receive/<int:id>')
@login_required
def receive_purchase_order(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM purchase_orders WHERE id = %s AND user_id = %s', (id, current_user.id))
    po = cur.fetchone()
    if not po:
        flash('Purchase order not found.', 'danger')
        return redirect(url_for('purchase_orders'))
    cur.execute("UPDATE purchase_orders SET status = 'received' WHERE id = %s", (id,))
    if po['stock_id']:
        cur.execute('UPDATE stock SET quantity = quantity + %s WHERE id = %s AND user_id = %s',
                    (po['quantity'], po['stock_id'], current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    _notify(current_user.id, f"Purchase order for \"{po['item_description']}\" marked received"
            + (" and added to stock." if po['stock_id'] else "."), 'purchase_order')
    flash('Purchase order received.', 'success')
    return redirect(url_for('purchase_orders'))

@app.route('/purchase-orders/delete/<int:id>')
@login_required
def delete_purchase_order(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM purchase_orders WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Purchase order deleted.', 'success')
    return redirect(url_for('purchase_orders'))

# ======================== Budgeting ========================

@app.route('/budgets')
@login_required
def budgets():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM budgets WHERE user_id = %s ORDER BY category', (current_user.id,))
    budget_rows = cur.fetchall()
    month_start = datetime.today().replace(day=1).strftime('%Y-%m-%d')
    spend_by_category = {}
    for b in budget_rows:
        cur.execute('SELECT COALESCE(SUM(amount),0) as spent FROM expenses WHERE user_id = %s AND category = %s AND date >= %s',
                    (current_user.id, b['category'], month_start))
        spend_by_category[b['category']] = cur.fetchone()['spent']
    cur.close()
    conn.close()
    return render_template('budgets.html', budgets=budget_rows, spend_by_category=spend_by_category)

@app.route('/budgets/add', methods=['POST'])
@login_required
def add_budget():
    category = request.form['category']
    monthly_limit = float(request.form['monthly_limit'])
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO budgets (user_id, category, monthly_limit, created_date)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, category) DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
    ''', (current_user.id, category, monthly_limit, datetime.today().strftime('%Y-%m-%d')))
    conn.commit()
    cur.close()
    conn.close()
    flash('Budget saved.', 'success')
    return redirect(url_for('budgets'))

@app.route('/budgets/delete/<int:id>')
@login_required
def delete_budget(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM budgets WHERE id = %s AND user_id = %s', (id, current_user.id))
    conn.commit()
    cur.close()
    conn.close()
    flash('Budget removed.', 'success')
    return redirect(url_for('budgets'))

# ======================== Notifications ========================

@app.route('/notifications')
@login_required
def notifications():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM notifications WHERE user_id = %s ORDER BY created_date DESC LIMIT 100', (current_user.id,))
    items = cur.fetchall()
    cur.execute('UPDATE notifications SET is_read = 1 WHERE user_id = %s AND is_read = 0', (current_user.id,))
    conn.commit()
    cur.close()
    conn.close()
    return render_template('notifications.html', notifications=items)

@app.route('/notifications/clear')
@login_required
def clear_notifications():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM notifications WHERE user_id = %s', (current_user.id,))
    conn.commit()
    cur.close()
    conn.close()
    flash('Notifications cleared.', 'success')
    return redirect(url_for('notifications'))

# ======================== Reports with date range and charts ========================

@app.route('/reports')
@login_required
def reports():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date:
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = get_db()
    cur = conn.cursor()
    
    # Expenses by category (pie chart)
    cur.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = %s AND date BETWEEN %s AND %s
        GROUP BY category
        ORDER BY total DESC
    ''', (current_user.id, start_date, end_date))
    expense_by_category = cur.fetchall()
    
    # Top products by revenue (bar chart) — FIXED: now includes profit
    cur.execute('''
        SELECT stock.product_name,
               SUM(sales.quantity_sold) as units_sold,
               SUM(sales.total_amount) as revenue,
               SUM(sales.profit) as profit
        FROM sales JOIN stock ON sales.stock_id = stock.id
        WHERE sales.user_id = %s AND sales.sale_date BETWEEN %s AND %s
        GROUP BY stock.product_name
        ORDER BY revenue DESC
        LIMIT 5
    ''', (current_user.id, start_date, end_date))
    top_products = cur.fetchall()
    
    # Also the monthly profit trend (keep existing)
    months = []
    for i in range(5, -1, -1):
        m = _add_months(datetime.today().replace(day=1).strftime('%Y-%m-%d'), -i)
        months.append(m[:7])
    
    monthly_income = {m: 0 for m in months}
    monthly_expenses = {m: 0 for m in months}
    monthly_sales_profit = {m: 0 for m in months}
    
    cur.execute('SELECT date, amount FROM income WHERE user_id = %s', (current_user.id,))
    for row in cur.fetchall():
        key = row['date'][:7]
        if key in monthly_income:
            monthly_income[key] += row['amount']
    
    cur.execute('SELECT date, amount FROM expenses WHERE user_id = %s', (current_user.id,))
    for row in cur.fetchall():
        key = row['date'][:7]
        if key in monthly_expenses:
            monthly_expenses[key] += row['amount']
    
    cur.execute('SELECT sale_date, profit FROM sales WHERE user_id = %s', (current_user.id,))
    for row in cur.fetchall():
        key = row['sale_date'][:7]
        if key in monthly_sales_profit:
            monthly_sales_profit[key] += row['profit']
    
    monthly_profit = {m: monthly_income[m] - monthly_expenses[m] + monthly_sales_profit[m] for m in months}
    
    # Top customers (keep existing)
    cur.execute('''
        SELECT COALESCE(NULLIF(customer_name, ''), 'Walk-in') as customer_name,
               SUM(total_amount) as spent, COUNT(*) as orders
        FROM sales WHERE user_id = %s
        GROUP BY customer_name ORDER BY spent DESC LIMIT 5
    ''', (current_user.id,))
    top_customers = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('reports.html',
                           months=months,
                           monthly_income=monthly_income,
                           monthly_expenses=monthly_expenses,
                           monthly_profit=monthly_profit,
                           top_products=top_products,
                           top_customers=top_customers,
                           expense_by_category=expense_by_category,
                           start_date=start_date,
                           end_date=end_date)

# ======================== Daily Summary ========================

@app.route('/send_daily_summary')
@login_required
def send_daily_summary():
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM sales WHERE user_id = %s AND sale_date = %s', (current_user.id, today))
    sales_today = cur.fetchall()
    
    if not sales_today:
        flash('No sales recorded for today.', 'info')
        return redirect(url_for('dashboard'))
    
    total_revenue = sum(sale['total_amount'] for sale in sales_today)
    total_profit = sum(sale['profit'] for sale in sales_today)
    
    body = f"Daily Sales Summary for {today}\n\n"
    body += f"Total Sales: {len(sales_today)} transactions\n"
    body += f"Total Revenue: ${total_revenue:.2f}\n"
    body += f"Total Profit: ${total_profit:.2f}\n\n"
    body += "Details:\n"
    for sale in sales_today:
        body += f"- {sale['customer_name'] or 'Anonymous'}: ${sale['total_amount']:.2f}\n"
    
    cur.execute('SELECT notify_email FROM settings WHERE user_id = %s', (current_user.id,))
    settings = cur.fetchone()
    to_email = settings['notify_email'] if settings else current_user.email
    cur.close()
    conn.close()
    
    subject = f"Daily Sales Summary - {today}"
    send_email(to_email, subject, body)
    flash(f'Daily sales summary sent to {to_email}', 'success')
    return redirect(url_for('dashboard'))

# ======================== Activity Log ========================

@app.route('/activity')
@login_required
def activity():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT username, login_time, ip_address 
        FROM user_activity 
        WHERE user_id = %s
        ORDER BY login_time DESC 
        LIMIT 50
    ''', (current_user.id,))
    logs = cur.fetchall()
    today = datetime.now().strftime('%Y-%m-%d')
    cur.execute('''
    SELECT COUNT(*) as active_count
    FROM user_activity 
    WHERE user_id = %s AND login_time::date = %s
    ''', (current_user.id, today))
    active_count = cur.fetchone()['active_count']
    cur.close()
    conn.close()
    return render_template('activity.html', logs=logs, active_count=active_count)

# ======================== Global Search ========================

@app.route('/search')
@login_required
def search():
    q = request.args.get('q', '').strip()
    if not q:
        flash('Please enter a search term.', 'info')
        return redirect(url_for('dashboard'))
    
    conn = get_db()
    cur = conn.cursor()
    # Search customers
    cur.execute('''
        SELECT id, name, 'customer' as type
        FROM customers
        WHERE user_id = %s AND (name ILIKE %s OR email ILIKE %s OR phone ILIKE %s)
        LIMIT 10
    ''', (current_user.id, f'%{q}%', f'%{q}%', f'%{q}%'))
    customers = cur.fetchall()
    
    # Search products
    cur.execute('''
        SELECT id, product_name as name, 'product' as type
        FROM stock
        WHERE user_id = %s AND product_name ILIKE %s
        LIMIT 10
    ''', (current_user.id, f'%{q}%'))
    products = cur.fetchall()
    
    # Search documents (invoices)
    cur.execute('''
        SELECT id, title as name, 'document' as type
        FROM documents
        WHERE user_id = %s AND (title ILIKE %s OR client ILIKE %s)
        LIMIT 10
    ''', (current_user.id, f'%{q}%', f'%{q}%'))
    docs = cur.fetchall()
    
    cur.close()
    conn.close()
    
    results = customers + products + docs
    return render_template('search_results.html', results=results, q=q)

# ======================== Main ========================

if __name__ == '__main__':
    app.run(debug=True)