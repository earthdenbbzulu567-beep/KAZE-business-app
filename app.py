# Business App - Web Version with User Login
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import json
import os

def get_db():
    # Use a persistent directory on Render (or local folder fallback)
    if os.environ.get('RENDER'):
        # On Render, use /opt/render/project/src/ (the app's root)
        db_path = os.path.join(os.getcwd(), 'business.db')
    else:
        # Local development
        db_path = 'business.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

from datetime import datetime
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database setup

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            doc_type TEXT NOT NULL,
            title TEXT NOT NULL,
            client TEXT NOT NULL,
            amount REAL,
            date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS cash_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            entry_type TEXT NOT NULL,  -- 'in' or 'out'
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            cost_price REAL NOT NULL,
            selling_price REAL NOT NULL,
            unit TEXT,  -- e.g., 'kg', 'piece', 'liter'
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            stock_id INTEGER NOT NULL,
            quantity_sold REAL NOT NULL,
            selling_price_at_time REAL NOT NULL,
            total_amount REAL NOT NULL,
            profit REAL NOT NULL,
            sale_date TEXT NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (stock_id) REFERENCES stock (id)
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
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
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

init_db()
def send_email(to_email, subject, body):
    from_email = "earthdenbbzulu567@gmail.com" # Replace with your real Gmail address
    password = "yjjnerakfbsycryt" # Paste your new 16-digit App Password here
    
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

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@app.context_processor
def inject_settings():
    if current_user.is_authenticated:
        conn = get_db()
        settings = conn.execute('SELECT * FROM settings WHERE user_id = ?', (current_user.id,)).fetchone()
        conn.close()
        return dict(user_settings=settings)
    return dict(user_settings=None)

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute('SELECT id, username, email FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user['id'], user['username'], user['email'])
    return None

# Routes
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
        try:
            conn.execute('INSERT INTO users (username, email, password) VALUES (?, ?, ?)', (username, email, hashed))
            conn.commit()
            flash('Account created! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists. Try another.', 'danger')
        finally:
            conn.close()
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
   if request.method == 'POST':
        login_input = request.form['login_input']
        password = request.form['password']
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE username = ? OR email = ?',
                            (login_input, login_input)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            login_user(User(user['id'], user['username'], user['email']))
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'danger')

   return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db()
        # Low stock items (using user's threshold)
    settings_row = conn.execute('SELECT low_stock_threshold FROM settings WHERE user_id = ?', (current_user.id,)).fetchone()
    threshold = settings_row['low_stock_threshold'] if settings_row else 10
    low_stock_items = conn.execute('SELECT product_name, quantity, unit FROM stock WHERE user_id = ? AND quantity < ?', (current_user.id, threshold)).fetchall()
    
    # Sales trend last 7 days
    import datetime
    today = datetime.date.today()
    sales_trend = {}
    for i in range(7):
        d = (today - datetime.timedelta(days=i)).strftime('%Y-%m-%d')
        sales_trend[d] = 0
    trend_sales = conn.execute('SELECT sale_date, SUM(total_amount) as total FROM sales WHERE user_id = ? AND sale_date >= date("now", "-7 days") GROUP BY sale_date', (current_user.id,)).fetchall()
    for row in trend_sales:
        sales_trend[row['sale_date']] = row['total']
    income = conn.execute('SELECT * FROM income WHERE user_id = ? ORDER BY date DESC', (current_user.id,)).fetchall()
    expenses = conn.execute('SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC', (current_user.id,)).fetchall()
    
    total_income = sum(i['amount'] for i in income)
    total_expenses = sum(e['amount'] for e in expenses)
    
    # Get sales profit
    sales_data = conn.execute('SELECT SUM(profit) as total_profit FROM sales WHERE user_id = ?', (current_user.id,)).fetchone()
    total_sales_profit = sales_data['total_profit'] or 0
    
    # Get cash book net (ins - outs)
    cash_in = conn.execute('SELECT SUM(amount) as total_in FROM cash_books WHERE user_id = ? AND entry_type = "in"', (current_user.id,)).fetchone()['total_in'] or 0
    cash_out = conn.execute('SELECT SUM(amount) as total_out FROM cash_books WHERE user_id = ? AND entry_type = "out"', (current_user.id,)).fetchone()['total_out'] or 0
    cash_net = cash_in - cash_out
    
    # Overall profit = (income - expenses) + sales profit + cash_net? Actually careful:
    # Income/expenses already capture some cash flows. To avoid double-counting, we should either treat sales separately.
    # A simpler approach: Show each component separately.
    total_profit = (total_income - total_expenses) + total_sales_profit + cash_net
    
    # Group data for chart (same as before)
    income_by_date = {}
    for item in income:
        date = item['date']
        income_by_date[date] = income_by_date.get(date, 0) + item['amount']
    
    expense_by_date = {}
    for item in expenses:
        date = item['date']
        expense_by_date[date] = expense_by_date.get(date, 0) + item['amount']
    
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

@app.route('/add_income', methods=['POST'])
@login_required
def add_income():
    source = request.form['source']
    amount = float(request.form['amount'])
    date = request.form['date'] or datetime.today().strftime('%Y-%m-%d')
    
    conn = get_db()
    conn.execute('INSERT INTO income (user_id, source, amount, date) VALUES (?, ?, ?, ?)',
                (current_user.id, source, amount, date))
    conn.commit()
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
    conn.execute('INSERT INTO expenses (user_id, name, amount, category, date) VALUES (?, ?, ?, ?, ?)',
                (current_user.id, name, amount, category, date))
    conn.commit()
    conn.close()
    
    flash('Expense added!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_income/<int:id>')
@login_required
def delete_income(id):
    conn = get_db()
    conn.execute('DELETE FROM income WHERE id = ? AND user_id = ?', (id, current_user.id))
    conn.commit()
    conn.close()
    flash('Income deleted', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_expense/<int:id>')
@login_required
def delete_expense(id):
    conn = get_db()
    conn.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?', (id, current_user.id))
    conn.commit()
    conn.close()
    flash('Expense deleted', 'success')
    return redirect(url_for('dashboard'))

@app.route('/docs')
@login_required
def docs():
    conn = get_db()
    user_docs = conn.execute('SELECT * FROM documents WHERE user_id = ? ORDER BY id DESC', (current_user.id,)).fetchall()
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
    conn.execute(
        'INSERT INTO documents (user_id, doc_type, title, client, amount, date, notes) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (current_user.id, doc_type, title, client, amount, date, notes)
    )
    conn.commit()
    conn.close()
    flash('Document saved!', 'success')
    return redirect(url_for('docs'))

@app.route('/docs/delete/<int:id>')
@login_required
def delete_doc(id):
    conn = get_db()
    doc = conn.execute('SELECT * FROM documents WHERE id = ? AND user_id = ?', (id, current_user.id)).fetchone()
    if not doc:
        flash('Document not found or unauthorised.', 'danger')
        return redirect(url_for('docs'))
    conn.execute('DELETE FROM documents WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Document deleted.', 'success')
    return redirect(url_for('docs'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
# ========================
# Stock Management
# ========================
@app.route('/stock')
@login_required
def stock():
    conn = get_db()
    items = conn.execute('SELECT * FROM stock WHERE user_id = ? ORDER BY product_name', (current_user.id,)).fetchall()
    conn.close()
    
    # Prepare data for chart: product names and total value (quantity * cost_price)
    product_names = [item['product_name'] for item in items]
    inventory_values = [item['quantity'] * item['cost_price'] for item in items]
    
    return render_template('stock.html', 
                         items=items,
                         product_names=product_names,
                         inventory_values=inventory_values)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    conn = get_db()
    # Ensure a settings row exists for this user
    conn.execute('INSERT OR IGNORE INTO settings (user_id, notify_email) VALUES (?, ?)',
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
        
        conn.execute('''
            UPDATE settings 
            SET low_stock_threshold = ?,
                email_notifications = ?,
                notify_email = ?,
                theme = ?,
                font_family = ?,
                font_size = ?,
                default_chart_type = ?,
                animations_enabled = ?,
                show_low_stock_widget = ?,
                show_sales_trend = ?,
                about_text = ?
            WHERE user_id = ?
        ''', (low_stock_threshold, email_notifications, notify_email,
              theme, font_family, font_size, default_chart_type,
              animations_enabled, show_low_stock_widget, show_sales_trend,
              about_text, current_user.id))
        conn.commit()
        conn.close()
        flash('Settings saved.', 'success')
        return redirect(url_for('settings'))
    
    # GET: load current settings
    settings_row = conn.execute('SELECT * FROM settings WHERE user_id = ?', (current_user.id,)).fetchone()
    conn.close()
    return render_template('settings.html', settings=settings_row)

@app.route('/stock/add', methods=['POST'])
@login_required
def add_stock():
    product_name = request.form['product_name']
    quantity = float(request.form['quantity'])
    cost_price = float(request.form['cost_price'])
    selling_price = float(request.form['selling_price'])
    unit = request.form.get('unit', '')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO stock (user_id, product_name, quantity, cost_price, selling_price, unit)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, product_name, quantity, cost_price, selling_price, unit))
    conn.commit()
    conn.close()
    flash('Stock item added.', 'success')
    return redirect(url_for('stock'))

@app.route('/stock/update/<int:id>', methods=['POST'])
@login_required
def update_stock(id):
    new_quantity = float(request.form['quantity'])
    conn = get_db()
    
    # Get product name
    product = conn.execute('SELECT product_name FROM stock WHERE id = ? AND user_id = ?', (id, current_user.id)).fetchone()
    if not product:
        flash('Stock item not found.', 'danger')
        return redirect(url_for('stock'))
    
    # Get user email (fallback) and settings
    user = conn.execute('SELECT email FROM users WHERE id = ?', (current_user.id,)).fetchone()
    user_email = user['email']
    settings = conn.execute('SELECT low_stock_threshold, email_notifications, notify_email FROM settings WHERE user_id = ?', (current_user.id,)).fetchone()
    
    # Update quantity
    conn.execute('UPDATE stock SET quantity = ? WHERE id = ? AND user_id = ?', (new_quantity, id, current_user.id))
    conn.commit()
    
    # Check low stock based on user's threshold
    if settings and settings['email_notifications']:
        threshold = settings['low_stock_threshold'] or 10
        if new_quantity < threshold:
            to_email = settings['notify_email'] or user_email
            subject = f"Low Stock Alert: {product['product_name']}"
            body = f"Your product '{product['product_name']}' has only {new_quantity} units left (threshold {threshold}). Please restock."
            send_email(to_email, subject, body)
            flash(f'Low stock alert sent to {to_email}', 'info')
    elif not settings:
        # fallback: no settings row yet, use defaults
        if new_quantity < 10:
            send_email(user_email, f"Low Stock: {product['product_name']}", f"{product['product_name']} is down to {new_quantity}.")
            flash('Low stock alert sent (default settings).', 'info')
    
    conn.close()
    flash('Stock updated.', 'success')
    return redirect(url_for('stock'))

@app.route('/stock/delete/<int:id>')
@login_required
def delete_stock(id):
    conn = get_db()
    conn.execute('DELETE FROM stock WHERE id = ? AND user_id = ?', (id, current_user.id))
    conn.commit()
    conn.close()
    flash('Stock item deleted.', 'success')
    return redirect(url_for('stock'))

@app.route('/stock/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_stock(id):
    conn = get_db()
    item = conn.execute('SELECT * FROM stock WHERE id = ? AND user_id = ?', (id, current_user.id)).fetchone()
    if not item:
        flash('Item not found.', 'danger')
        return redirect(url_for('stock'))
    
    if request.method == 'POST':
        product_name = request.form['product_name']
        quantity = float(request.form['quantity'])
        cost_price = float(request.form['cost_price'])
        selling_price = float(request.form['selling_price'])
        unit = request.form.get('unit', '')
        conn.execute('''
            UPDATE stock 
            SET product_name=?, quantity=?, cost_price=?, selling_price=?, unit=?
            WHERE id=? AND user_id=?
        ''', (product_name, quantity, cost_price, selling_price, unit, id, current_user.id))
        conn.commit()
        conn.close()
        flash('Stock updated.', 'success')
        return redirect(url_for('stock'))
    
    conn.close()
    return render_template('edit_stock.html', item=item)
# ========================
# Cash Book
# ========================
@app.route('/cashbook')
@login_required
def cashbook():
    conn = get_db()
    entries = conn.execute('SELECT * FROM cash_books WHERE user_id = ? ORDER BY date DESC', (current_user.id,)).fetchall()
    conn.close()
    return render_template('cashbook.html', entries=entries)

@app.route('/cashbook/add', methods=['POST'])
@login_required
def add_cash_entry():
    entry_type = request.form['entry_type']  # 'in' or 'out'
    category = request.form['category']
    description = request.form['description']
    amount = float(request.form['amount'])
    date = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
    
    conn = get_db()
    conn.execute('''
        INSERT INTO cash_books (user_id, entry_type, category, description, amount, date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (current_user.id, entry_type, category, description, amount, date))
    conn.commit()
    conn.close()
    flash('Cash entry added.', 'success')
    return redirect(url_for('cashbook'))

@app.route('/cashbook/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_cash_entry(id):
    conn = get_db()
    entry = conn.execute('SELECT * FROM cash_books WHERE id = ? AND user_id = ?', (id, current_user.id)).fetchone()
    if not entry:
        flash('Entry not found.', 'danger')
        return redirect(url_for('cashbook'))
    
    if request.method == 'POST':
        entry_type = request.form['entry_type']
        category = request.form['category']
        description = request.form['description']
        amount = float(request.form['amount'])
        date = request.form['date']
        conn.execute('''
            UPDATE cash_books 
            SET entry_type=?, category=?, description=?, amount=?, date=?
            WHERE id=? AND user_id=?
        ''', (entry_type, category, description, amount, date, id, current_user.id))
        conn.commit()
        conn.close()
        flash('Cash entry updated.', 'success')
        return redirect(url_for('cashbook'))
    
    conn.close()
    return render_template('edit_cashbook.html', entry=entry)

@app.route('/cashbook/delete/<int:id>')
@login_required
def delete_cash_entry(id):
    conn = get_db()
    conn.execute('DELETE FROM cash_books WHERE id = ? AND user_id = ?', (id, current_user.id))
    conn.commit()
    conn.close()
    flash('Cash entry deleted.', 'success')
    return redirect(url_for('cashbook'))
# ========================
# Sales (with stock deduction and profit)
# ========================
@app.route('/sales')
@login_required
def sales():
    conn = get_db()
    all_sales = conn.execute('''
        SELECT sales.*, stock.product_name 
        FROM sales 
        JOIN stock ON sales.stock_id = stock.id
        WHERE sales.user_id = ? 
        ORDER BY sale_date DESC
    ''', (current_user.id,)).fetchall()
    
    stock_items = conn.execute('SELECT id, product_name, selling_price, quantity FROM stock WHERE user_id = ? AND quantity > 0', (current_user.id,)).fetchall()
    
    # Group sales by date (for chart)
    sales_by_date = {}
    for sale in all_sales:
        d = sale['sale_date']
        sales_by_date[d] = sales_by_date.get(d, 0) + sale['total_amount']
    
    conn.close()
    return render_template('sales.html', 
                         sales=all_sales, 
                         stock_items=stock_items,
                         sales_by_date=sales_by_date)
@app.route('/sales/add', methods=['POST'])
@login_required
def add_sale():
    stock_id = int(request.form['stock_id'])
    quantity_sold = float(request.form['quantity'])
    customer_name = request.form.get('customer_name', '')
    customer_email = request.form.get('customer_email', '')
    sale_date = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
    
    conn = get_db()
    # Get the stock item
    stock_item = conn.execute('SELECT * FROM stock WHERE id = ? AND user_id = ?', (stock_id, current_user.id)).fetchone()
    if not stock_item:
        flash('Stock item not found.', 'danger')
        return redirect(url_for('sales'))
    
    if stock_item['quantity'] < quantity_sold:
        flash(f'Insufficient stock. Only {stock_item["quantity"]} available.', 'danger')
        return redirect(url_for('sales'))
    
    # Calculate profit
    selling_price = stock_item['selling_price']
    cost_price = stock_item['cost_price']
    total_amount = selling_price * quantity_sold
    profit = (selling_price - cost_price) * quantity_sold
    
    # Record sale
    conn.execute('''
        INSERT INTO sales (user_id, stock_id, quantity_sold, selling_price_at_time, total_amount, profit, sale_date, customer_name, customer_email)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (current_user.id, stock_id, quantity_sold, selling_price, total_amount, profit, sale_date, customer_name, customer_email))
    
    # Deduct stock
    new_quantity = stock_item['quantity'] - quantity_sold
    conn.execute('UPDATE stock SET quantity = ? WHERE id = ?', (new_quantity, stock_id))
    
    # Also automatically add income? Actually the sale is income. But you already have income table. 
    # We can optionally add to income as well, but to avoid duplication, we'll keep sales separate and compute overall profit/loss from sales + income/expenses.
    # For now, we just record sale and deduct stock.
    
    conn.commit()
    conn.close()
    flash(f'Sale recorded. Profit: ${profit:.2f}', 'success')
    return redirect(url_for('sales'))

@app.route('/sales/delete/<int:id>')
@login_required
def delete_sale(id):
    conn = get_db()
    # Before deleting sale, we need to add stock back
    sale = conn.execute('SELECT * FROM sales WHERE id = ? AND user_id = ?', (id, current_user.id)).fetchone()
    if sale:
        # Restore stock
        conn.execute('UPDATE stock SET quantity = quantity + ? WHERE id = ?', (sale['quantity_sold'], sale['stock_id']))
        conn.execute('DELETE FROM sales WHERE id = ?', (id,))
        conn.commit()
        flash('Sale deleted and stock restored.', 'success')
    else:
        flash('Sale not found.', 'danger')
    conn.close()
    return redirect(url_for('sales'))

@app.route('/send_daily_summary')
@login_required
def send_daily_summary():
    today = datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    
    # Get today's sales
    sales_today = conn.execute('''
        SELECT * FROM sales WHERE user_id = ? AND sale_date = ?
    ''', (current_user.id, today)).fetchall()
    
    if not sales_today:
        flash('No sales recorded for today.', 'info')
        return redirect(url_for('dashboard'))
    
    total_revenue = sum(sale['total_amount'] for sale in sales_today)
    total_profit = sum(sale['profit'] for sale in sales_today)
    
    # Build email body
    body = f"Daily Sales Summary for {today}\n\n"
    body += f"Total Sales: {len(sales_today)} transactions\n"
    body += f"Total Revenue: ${total_revenue:.2f}\n"
    body += f"Total Profit: ${total_profit:.2f}\n\n"
    body += "Details:\n"
    for sale in sales_today:
        body += f"- {sale['customer_name'] or 'Anonymous'}: ${sale['total_amount']:.2f}\n"
    
    # Get user's notification email
    settings = conn.execute('SELECT notify_email FROM settings WHERE user_id = ?', (current_user.id,)).fetchone()
    to_email = settings['notify_email'] if settings else current_user.email
    conn.close()
    
    subject = f"Daily Sales Summary - {today}"
    send_email(to_email, subject, body)
    flash(f'Daily sales summary sent to {to_email}', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)