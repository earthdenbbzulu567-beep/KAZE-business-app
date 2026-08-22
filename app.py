# Business App - Web Version with PostgreSQL (Aiven)
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database connection (Aiven PostgreSQL)
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
            customer_email TEXT
        )
    ''')
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
            about_text TEXT DEFAULT ''
        )
    ''')
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
    conn.commit()
    cur.close()
    conn.close()

init_db()

# Email function
def send_email(to_email, subject, body):
    from_email = "earthdenbbzulu567@gmail.com"
    password = "yjjnerakfbsycryt"  # Your app password
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

# User class
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@app.context_processor
def inject_settings():
    if current_user.is_authenticated:
        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM settings WHERE user_id = %s', (current_user.id,))
        settings = cur.fetchone()
        cur.close()
        conn.close()
        return dict(user_settings=settings)
    return dict(user_settings=None)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email FROM users WHERE id = %s', (user_id,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'])
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
            login_user(User(user['id'], user['username'], user['email']))
            # Log activity – catches any error so login never fails
            try:
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                conn = get_db()
                cur = conn.cursor()
                cur.execute('INSERT INTO user_activity (user_id, username, login_time, ip_address) VALUES (%s, %s, %s, %s)',
                            (user['id'], user['username'], now, ip))
                conn.commit()
                cur.close()
                conn.close()
            except Exception as e:
                # Log the error but don't block login
                print(f"Activity log error: {e}")
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
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
        WHERE user_id = %s AND sale_date >= NOW() - INTERVAL '7 days'
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
    
    income_by_date = {}
    for item in income:
        income_by_date[item['date']] = income_by_date.get(item['date'], 0) + item['amount']
    expense_by_date = {}
    for item in expenses:
        expense_by_date[item['date']] = expense_by_date.get(item['date'], 0) + item['amount']
    
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
                         sales_trend_data=sales_trend)

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
    flash('Document deleted.', 'success')
    return redirect(url_for('docs'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# ======================== Stock Management ========================

@app.route('/stock')
@login_required
def stock():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM stock WHERE user_id = %s ORDER BY product_name', (current_user.id,))
    items = cur.fetchall()
    cur.close()
    conn.close()
    product_names = [item['product_name'] for item in items]
    inventory_values = [item['quantity'] * item['cost_price'] for item in items]
    return render_template('stock.html', items=items, product_names=product_names, inventory_values=inventory_values)

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
        flash('Stock updated.', 'success')
        return redirect(url_for('stock'))
    
    cur.close()
    conn.close()
    return render_template('edit_stock.html', item=item)

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
        
        cur.execute('''
            UPDATE settings 
            SET low_stock_threshold=%s, email_notifications=%s, notify_email=%s,
                theme=%s, font_family=%s, font_size=%s, default_chart_type=%s,
                animations_enabled=%s, show_low_stock_widget=%s, show_sales_trend=%s,
                about_text=%s
            WHERE user_id=%s
        ''', (low_stock_threshold, email_notifications, notify_email,
              theme, font_family, font_size, default_chart_type,
              animations_enabled, show_low_stock_widget, show_sales_trend,
              about_text, current_user.id))
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
    flash('Cash entry deleted.', 'success')
    return redirect(url_for('cashbook'))

# ======================== Sales ========================

@app.route('/sales')
@login_required
def sales():
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''
        SELECT sales.*, stock.product_name 
        FROM sales 
        JOIN stock ON sales.stock_id = stock.id
        WHERE sales.user_id = %s 
        ORDER BY sale_date DESC
    ''', (current_user.id,))
    all_sales = cur.fetchall()
    
    cur.execute('SELECT id, product_name, selling_price, quantity FROM stock WHERE user_id = %s AND quantity > 0',
                (current_user.id,))
    stock_items = cur.fetchall()
    
    sales_by_date = {}
    for sale in all_sales:
        d = sale['sale_date']
        sales_by_date[d] = sales_by_date.get(d, 0) + sale['total_amount']
    
    cur.close()
    conn.close()
    return render_template('sales.html', sales=all_sales, stock_items=stock_items, sales_by_date=sales_by_date)

@app.route('/sales/add', methods=['POST'])
@login_required
def add_sale():
    stock_id = int(request.form['stock_id'])
    quantity_sold = float(request.form['quantity'])
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
    
    selling_price = stock_item['selling_price']
    cost_price = stock_item['cost_price']
    total_amount = selling_price * quantity_sold
    profit = (selling_price - cost_price) * quantity_sold
    
    cur.execute('''
        INSERT INTO sales (user_id, stock_id, quantity_sold, selling_price_at_time, total_amount, profit, sale_date, customer_name, customer_email)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ''', (current_user.id, stock_id, quantity_sold, selling_price, total_amount, profit, sale_date, customer_name, customer_email))
    
    new_quantity = stock_item['quantity'] - quantity_sold
    cur.execute('UPDATE stock SET quantity = %s WHERE id = %s', (new_quantity, stock_id))
    conn.commit()
    cur.close()
    conn.close()
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
        flash('Sale deleted and stock restored.', 'success')
    else:
        flash('Sale not found.', 'danger')
    cur.close()
    conn.close()
    return redirect(url_for('sales'))

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
        ORDER BY login_time DESC 
        LIMIT 50
    ''')
    logs = cur.fetchall()
    today = datetime.now().strftime('%Y-%m-%d')
    cur.execute('''
        SELECT COUNT(DISTINCT user_id) 
        FROM user_activity 
        WHERE DATE(login_time) = %s
    ''', (today,))
    active_count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return render_template('activity.html', logs=logs, active_count=active_count)

# ======================== Main ========================

if __name__ == '__main__':
    app.run(debug=True)