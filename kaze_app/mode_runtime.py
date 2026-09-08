"""
KAZE mode runtime
=================
Only the selected app mode runs its pipeline. Other mode pipelines stay dormant.
Dashboard, P/L strip, and trackers consume the snapshot this module returns.
"""

from datetime import datetime, timedelta


# ---------------------------------------------------------------------------
# Safe casts
# ---------------------------------------------------------------------------

def as_float(value, default=0.0):
    try:
        if value is None or value == '':
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def as_int(value, default=0):
    try:
        if value is None or value == '':
            return int(default)
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def as_date(value):
    """Normalise DB dates / datetimes / strings to YYYY-MM-DD."""
    if value is None:
        return ''
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d')
    text = str(value).strip()
    if not text:
        return ''
    return text[:10]


def today_iso():
    return datetime.today().strftime('%Y-%m-%d')


def add_days(iso, days):
    try:
        base = datetime.strptime(iso[:10], '%Y-%m-%d')
    except (TypeError, ValueError):
        base = datetime.today()
    return (base + timedelta(days=days)).strftime('%Y-%m-%d')


def month_start_iso(iso=None):
    iso = iso or today_iso()
    return iso[:8] + '01'


def last_month_bounds(iso=None):
    iso = iso or today_iso()
    first = datetime.strptime(month_start_iso(iso), '%Y-%m-%d')
    last_end = first - timedelta(days=1)
    last_start = last_end.replace(day=1)
    return last_start.strftime('%Y-%m-%d'), last_end.strftime('%Y-%m-%d')


def pct(part, whole):
    whole = as_float(whole)
    if whole == 0:
        return 0.0
    return round((as_float(part) / whole) * 100.0, 1)


def delta_pct(now, then):
    then = as_float(then)
    now = as_float(now)
    if then == 0:
        return 100.0 if now > 0 else 0.0
    return round(((now - then) / abs(then)) * 100.0, 1)


def money_round(value):
    return round(as_float(value), 2)


# ---------------------------------------------------------------------------
# Empty snapshot
# ---------------------------------------------------------------------------

def empty_snapshot(mode='full'):
    today = today_iso()
    return {
        'mode': mode,
        'ran': [],
        'skipped': [],
        'today': today,
        'sales': {
            'rows': [],
            'today_revenue': 0.0,
            'today_profit': 0.0,
            'today_tickets': 0,
            'today_units': 0,
            'yesterday_revenue': 0.0,
            'yesterday_profit': 0.0,
            'week_revenue': 0.0,
            'week_profit': 0.0,
            'month_revenue': 0.0,
            'month_profit': 0.0,
            'last_month_revenue': 0.0,
            'last_month_profit': 0.0,
            'all_revenue': 0.0,
            'all_profit': 0.0,
            'all_tickets': 0,
            'all_units': 0,
            'avg_ticket': 0.0,
            'avg_margin_pct': 0.0,
            'day_vs_day_pct': 0.0,
            'month_vs_month_pct': 0.0,
            'best_day': '',
            'best_day_revenue': 0.0,
            'trend_7': {},
            'trend_30': {},
            'top_products': [],
            'recent': [],
        },
        'books': {
            'income_total': 0.0,
            'expense_total': 0.0,
            'income_month': 0.0,
            'expense_month': 0.0,
            'income_today': 0.0,
            'expense_today': 0.0,
            'income_rows': [],
            'expense_rows': [],
            'income_by_date': {},
            'expense_by_date': {},
            'expense_by_category': {},
        },
        'cash': {
            'in_total': 0.0,
            'out_total': 0.0,
            'net': 0.0,
            'today_in': 0.0,
            'today_out': 0.0,
        },
        'stock': {
            'skus': 0,
            'units': 0,
            'value_cost': 0.0,
            'value_sell': 0.0,
            'low': [],
            'out': [],
        },
        'office': {
            'open_tasks': [],
            'overdue_tasks': 0,
            'upcoming_recurring': [],
        },
        'alerts': [],
        'indicators': [],
        'pl': {
            'sales_revenue': 0.0,
            'sales_cost': 0.0,
            'sales_profit': 0.0,
            'other_income': 0.0,
            'expenses': 0.0,
            'operating': 0.0,
            'cash_net': 0.0,
            'combined': 0.0,
            'status': 'even',
            'label': 'Break even',
        },
    }


# ---------------------------------------------------------------------------
# Fetchers — only called by the live pipeline
# ---------------------------------------------------------------------------

def fetch_sales(cur, user_id, limit=400):
    cur.execute(
        '''
        SELECT sales.id, sales.stock_id, sales.quantity_sold, sales.selling_price_at_time,
               sales.total_amount, sales.profit, sales.sale_date, sales.customer_name,
               sales.discount, stock.product_name
        FROM sales
        LEFT JOIN stock ON sales.stock_id = stock.id
        WHERE sales.user_id = %s
        ORDER BY sales.id DESC
        LIMIT %s
        ''',
        (user_id, limit),
    )
    rows = []
    for raw in cur.fetchall() or []:
        row = dict(raw)
        row['sale_date'] = as_date(row.get('sale_date'))
        row['total_amount'] = as_float(row.get('total_amount'))
        row['profit'] = as_float(row.get('profit'))
        row['quantity_sold'] = as_float(row.get('quantity_sold'))
        row['discount'] = as_float(row.get('discount'))
        row['product_name'] = row.get('product_name') or 'Item removed'
        row['customer_name'] = row.get('customer_name') or 'Walk-in'
        rows.append(row)
    return rows


def fetch_income(cur, user_id):
    cur.execute(
        'SELECT id, source, amount, date FROM income WHERE user_id = %s ORDER BY date DESC, id DESC',
        (user_id,),
    )
    rows = []
    for raw in cur.fetchall() or []:
        row = dict(raw)
        row['date'] = as_date(row.get('date'))
        row['amount'] = as_float(row.get('amount'))
        rows.append(row)
    return rows


def fetch_expenses(cur, user_id):
    cur.execute(
        'SELECT id, name, amount, category, date FROM expenses WHERE user_id = %s ORDER BY date DESC, id DESC',
        (user_id,),
    )
    rows = []
    for raw in cur.fetchall() or []:
        row = dict(raw)
        row['date'] = as_date(row.get('date'))
        row['amount'] = as_float(row.get('amount'))
        row['category'] = row.get('category') or 'Other'
        rows.append(row)
    return rows


def fetch_cash(cur, user_id):
    cur.execute(
        'SELECT entry_type, amount, date FROM cash_books WHERE user_id = %s',
        (user_id,),
    )
    return [
        {
            'entry_type': (raw.get('entry_type') or '').lower(),
            'amount': as_float(raw.get('amount')),
            'date': as_date(raw.get('date')),
        }
        for raw in (cur.fetchall() or [])
    ]


def fetch_stock(cur, user_id, threshold=10):
    cur.execute(
        '''
        SELECT id, product_name, quantity, unit, cost_price, selling_price
        FROM stock WHERE user_id = %s ORDER BY product_name
        ''',
        (user_id,),
    )
    rows = []
    for raw in cur.fetchall() or []:
        row = dict(raw)
        row['quantity'] = as_float(row.get('quantity'))
        row['cost_price'] = as_float(row.get('cost_price'))
        row['selling_price'] = as_float(row.get('selling_price'))
        row['unit'] = row.get('unit') or ''
        rows.append(row)
    return rows, as_float(threshold, 10)


def fetch_open_tasks(cur, user_id):
    try:
        cur.execute(
            '''
            SELECT id, title, priority, due_date, done
            FROM tasks
            WHERE user_id = %s AND done = 0
            ORDER BY CASE WHEN due_date = '' OR due_date IS NULL THEN '9999-12-31' ELSE due_date END, id DESC
            LIMIT 8
            ''',
            (user_id,),
        )
        rows = []
        for raw in cur.fetchall() or []:
            row = dict(raw)
            row['due_date'] = as_date(row.get('due_date'))
            rows.append(row)
        return rows
    except Exception:
        return []


def fetch_upcoming_recurring(cur, user_id):
    try:
        soon = add_days(today_iso(), 14)
        cur.execute(
            '''
            SELECT name, next_run_date, item_type, amount
            FROM recurring_items
            WHERE user_id = %s AND active = 1 AND next_run_date <= %s
            ORDER BY next_run_date LIMIT 6
            ''',
            (user_id, soon),
        )
        rows = []
        for raw in cur.fetchall() or []:
            row = dict(raw)
            row['next_run_date'] = as_date(row.get('next_run_date'))
            row['amount'] = as_float(row.get('amount'))
            rows.append(row)
        return rows
    except Exception:
        return []


def fetch_settings_bits(cur, user_id):
    cur.execute(
        'SELECT low_stock_threshold, monthly_revenue_goal, tutorial_completed FROM settings WHERE user_id = %s',
        (user_id,),
    )
    row = cur.fetchone() or {}
    return {
        'threshold': as_float(row.get('low_stock_threshold'), 10),
        'monthly_goal': as_float(row.get('monthly_revenue_goal')),
        'tutorial_completed': as_int(row.get('tutorial_completed')),
    }


# ---------------------------------------------------------------------------
# Trackers
# ---------------------------------------------------------------------------

def build_sales_trackers(rows):
    today = today_iso()
    yesterday = add_days(today, -1)
    week_from = add_days(today, -6)
    month_from = month_start_iso(today)
    last_start, last_end = last_month_bounds(today)

    track = {
        'rows': rows,
        'today_revenue': 0.0,
        'today_profit': 0.0,
        'today_tickets': 0,
        'today_units': 0.0,
        'yesterday_revenue': 0.0,
        'yesterday_profit': 0.0,
        'week_revenue': 0.0,
        'week_profit': 0.0,
        'month_revenue': 0.0,
        'month_profit': 0.0,
        'last_month_revenue': 0.0,
        'last_month_profit': 0.0,
        'all_revenue': 0.0,
        'all_profit': 0.0,
        'all_tickets': len(rows),
        'all_units': 0.0,
        'avg_ticket': 0.0,
        'avg_margin_pct': 0.0,
        'day_vs_day_pct': 0.0,
        'month_vs_month_pct': 0.0,
        'best_day': '',
        'best_day_revenue': 0.0,
        'trend_7': {},
        'trend_30': {},
        'top_products': [],
        'recent': rows[:25],
    }

    for i in range(7):
        track['trend_7'][add_days(today, -i)] = 0.0
    for i in range(30):
        track['trend_30'][add_days(today, -i)] = 0.0

    by_product = {}
    by_day = {}

    for sale in rows:
        day = sale['sale_date']
        revenue = sale['total_amount']
        profit = sale['profit']
        units = sale['quantity_sold']
        track['all_revenue'] += revenue
        track['all_profit'] += profit
        track['all_units'] += units
        by_day[day] = by_day.get(day, 0.0) + revenue
        name = sale['product_name']
        bucket = by_product.setdefault(name, {'name': name, 'revenue': 0.0, 'profit': 0.0, 'units': 0.0, 'tickets': 0})
        bucket['revenue'] += revenue
        bucket['profit'] += profit
        bucket['units'] += units
        bucket['tickets'] += 1
        if day == today:
            track['today_revenue'] += revenue
            track['today_profit'] += profit
            track['today_tickets'] += 1
            track['today_units'] += units
        if day == yesterday:
            track['yesterday_revenue'] += revenue
            track['yesterday_profit'] += profit
        if day >= week_from:
            track['week_revenue'] += revenue
            track['week_profit'] += profit
        if day >= month_from:
            track['month_revenue'] += revenue
            track['month_profit'] += profit
        if last_start <= day <= last_end:
            track['last_month_revenue'] += revenue
            track['last_month_profit'] += profit
        if day in track['trend_7']:
            track['trend_7'][day] += revenue
        if day in track['trend_30']:
            track['trend_30'][day] += revenue

    if track['all_tickets']:
        track['avg_ticket'] = money_round(track['all_revenue'] / track['all_tickets'])
    if track['all_revenue']:
        track['avg_margin_pct'] = pct(track['all_profit'], track['all_revenue'])
    track['day_vs_day_pct'] = delta_pct(track['today_revenue'], track['yesterday_revenue'])
    track['month_vs_month_pct'] = delta_pct(track['month_revenue'], track['last_month_revenue'])
    if by_day:
        best = max(by_day.items(), key=lambda item: item[1])
        track['best_day'] = best[0]
        track['best_day_revenue'] = money_round(best[1])
    track['top_products'] = sorted(by_product.values(), key=lambda item: item['revenue'], reverse=True)[:6]
    for key in (
        'today_revenue', 'today_profit', 'yesterday_revenue', 'yesterday_profit',
        'week_revenue', 'week_profit', 'month_revenue', 'month_profit',
        'last_month_revenue', 'last_month_profit', 'all_revenue', 'all_profit',
    ):
        track[key] = money_round(track[key])
    return track


def build_books_trackers(income_rows, expense_rows):
    today = today_iso()
    month_from = month_start_iso(today)
    track = {
        'income_total': 0.0,
        'expense_total': 0.0,
        'income_month': 0.0,
        'expense_month': 0.0,
        'income_today': 0.0,
        'expense_today': 0.0,
        'income_rows': income_rows,
        'expense_rows': expense_rows,
        'income_by_date': {},
        'expense_by_date': {},
        'expense_by_category': {},
    }
    for row in income_rows:
        amount = row['amount']
        day = row['date']
        track['income_total'] += amount
        track['income_by_date'][day] = track['income_by_date'].get(day, 0.0) + amount
        if day >= month_from:
            track['income_month'] += amount
        if day == today:
            track['income_today'] += amount
    for row in expense_rows:
        amount = row['amount']
        day = row['date']
        cat = row['category']
        track['expense_total'] += amount
        track['expense_by_date'][day] = track['expense_by_date'].get(day, 0.0) + amount
        track['expense_by_category'][cat] = track['expense_by_category'].get(cat, 0.0) + amount
        if day >= month_from:
            track['expense_month'] += amount
        if day == today:
            track['expense_today'] += amount
    for key in ('income_total', 'expense_total', 'income_month', 'expense_month', 'income_today', 'expense_today'):
        track[key] = money_round(track[key])
    return track


def build_cash_trackers(rows):
    today = today_iso()
    track = {'in_total': 0.0, 'out_total': 0.0, 'net': 0.0, 'today_in': 0.0, 'today_out': 0.0}
    for row in rows:
        if row['entry_type'] == 'in':
            track['in_total'] += row['amount']
            if row['date'] == today:
                track['today_in'] += row['amount']
        else:
            track['out_total'] += row['amount']
            if row['date'] == today:
                track['today_out'] += row['amount']
    track['net'] = money_round(track['in_total'] - track['out_total'])
    track['in_total'] = money_round(track['in_total'])
    track['out_total'] = money_round(track['out_total'])
    track['today_in'] = money_round(track['today_in'])
    track['today_out'] = money_round(track['today_out'])
    return track


def build_stock_trackers(rows, threshold):
    track = {
        'skus': len(rows),
        'units': 0.0,
        'value_cost': 0.0,
        'value_sell': 0.0,
        'low': [],
        'out': [],
    }
    for row in rows:
        qty = row['quantity']
        track['units'] += qty
        track['value_cost'] += qty * row['cost_price']
        track['value_sell'] += qty * row['selling_price']
        if qty <= 0:
            track['out'].append(row)
        elif qty < threshold:
            track['low'].append(row)
    track['units'] = money_round(track['units'])
    track['value_cost'] = money_round(track['value_cost'])
    track['value_sell'] = money_round(track['value_sell'])
    return track


def build_profit_loss(sales, books, cash):
    revenue = as_float(sales.get('all_revenue'))
    profit = as_float(sales.get('all_profit'))
    cost = money_round(revenue - profit)
    other = as_float(books.get('income_total'))
    expenses = as_float(books.get('expense_total'))
    operating = money_round(profit + other - expenses)
    cash_net = as_float(cash.get('net'))
    combined = money_round(operating + cash_net)
    if operating > 0.004:
        status, label = 'profit', 'Profit'
    elif operating < -0.004:
        status, label = 'loss', 'Loss'
    else:
        status, label = 'even', 'Break even'
    return {
        'sales_revenue': money_round(revenue),
        'sales_cost': cost,
        'sales_profit': money_round(profit),
        'other_income': money_round(other),
        'expenses': money_round(expenses),
        'operating': operating,
        'cash_net': money_round(cash_net),
        'combined': combined,
        'status': status,
        'label': label,
    }


def push_alert(alerts, level, title, detail):
    alerts.append({'level': level, 'title': title, 'detail': detail})


def build_indicators(snap):
    sales = snap['sales']
    books = snap['books']
    stock = snap['stock']
    pl = snap['pl']
    items = [
        {'key': 'today_sales', 'label': "Today's sales", 'value': sales['today_revenue'], 'hint': '{} tickets'.format(sales['today_tickets'])},
        {'key': 'today_margin', 'label': "Today's sale profit", 'value': sales['today_profit'], 'hint': 'vs yesterday {}'.format(sales['day_vs_day_pct']) + '%'},
        {'key': 'month_sales', 'label': 'This month sales', 'value': sales['month_revenue'], 'hint': 'vs last month {}'.format(sales['month_vs_month_pct']) + '%'},
        {'key': 'avg_ticket', 'label': 'Average ticket', 'value': sales['avg_ticket'], 'hint': '{}% margin'.format(sales['avg_margin_pct'])},
        {'key': 'other_income', 'label': 'Other income', 'value': books['income_total'], 'hint': 'not from the till'},
        {'key': 'expenses', 'label': 'Expenses', 'value': books['expense_total'], 'hint': 'all recorded costs'},
        {'key': 'stock_value', 'label': 'Stock at cost', 'value': stock['value_cost'], 'hint': '{} SKUs'.format(stock['skus'])},
        {'key': 'operating', 'label': 'Operating P/L', 'value': pl['operating'], 'hint': pl['label']},
    ]
    return items


# ---------------------------------------------------------------------------
# Mode pipelines — only one of these runs
# ---------------------------------------------------------------------------

def _mark(snap, ran, skipped):
    snap['ran'] = list(ran)
    snap['skipped'] = list(skipped)
    return snap


def pipeline_till(cur, user_id, snap, bits):
    """Shop floor: sales + stock + cash drawer. Books stay dormant."""
    sales_rows = fetch_sales(cur, user_id)
    stock_rows, _ = fetch_stock(cur, user_id, bits['threshold'])
    cash_rows = fetch_cash(cur, user_id)
    snap['sales'] = build_sales_trackers(sales_rows)
    snap['stock'] = build_stock_trackers(stock_rows, bits['threshold'])
    snap['cash'] = build_cash_trackers(cash_rows)
    snap['pl'] = build_profit_loss(snap['sales'], snap['books'], snap['cash'])
    if snap['stock']['out']:
        push_alert(snap['alerts'], 'danger', 'Out of stock', '{} product(s) cannot be sold.'.format(len(snap['stock']['out'])))
    if snap['stock']['low']:
        push_alert(snap['alerts'], 'warn', 'Low stock', '{} product(s) are below the threshold.'.format(len(snap['stock']['low'])))
    if snap['sales']['today_tickets'] == 0:
        push_alert(snap['alerts'], 'info', 'No sales yet today', 'Open Counter or Sales to ring the first ticket.')
    elif snap['sales']['day_vs_day_pct'] < -20:
        push_alert(snap['alerts'], 'warn', 'Quiet versus yesterday', 'Today is {}% behind yesterday.'.format(snap['sales']['day_vs_day_pct']))
    snap['indicators'] = build_indicators(snap)
    return _mark(snap, ['sales', 'stock', 'cash', 'pl'], ['books', 'office'])


def pipeline_books(cur, user_id, snap, bits):
    """Ledgers: income, expenses, cash, sales totals for P/L. Till UI stays dormant."""
    sales_rows = fetch_sales(cur, user_id)
    income_rows = fetch_income(cur, user_id)
    expense_rows = fetch_expenses(cur, user_id)
    cash_rows = fetch_cash(cur, user_id)
    snap['sales'] = build_sales_trackers(sales_rows)
    snap['books'] = build_books_trackers(income_rows, expense_rows)
    snap['cash'] = build_cash_trackers(cash_rows)
    snap['pl'] = build_profit_loss(snap['sales'], snap['books'], snap['cash'])
    if snap['pl']['operating'] < 0:
        push_alert(snap['alerts'], 'danger', 'Operating loss', 'Expenses and costs are ahead of income and sale profit.')
    if snap['books']['expense_month'] > snap['books']['income_month'] + snap['sales']['month_profit']:
        push_alert(snap['alerts'], 'warn', 'This month is underwater', 'Month expenses are larger than month income plus sale profit.')
    snap['indicators'] = build_indicators(snap)
    return _mark(snap, ['sales_totals', 'books', 'cash', 'pl'], ['stock_alerts', 'office'])


def pipeline_office(cur, user_id, snap, bits):
    """Planning desk: tasks and reminders. Selling stays dormant."""
    snap['office']['open_tasks'] = fetch_open_tasks(cur, user_id)
    snap['office']['upcoming_recurring'] = fetch_upcoming_recurring(cur, user_id)
    today = today_iso()
    overdue = [t for t in snap['office']['open_tasks'] if t.get('due_date') and t['due_date'] < today]
    snap['office']['overdue_tasks'] = len(overdue)
    if overdue:
        push_alert(snap['alerts'], 'warn', 'Overdue tasks', '{} task(s) passed their due date.'.format(len(overdue)))
    if snap['office']['upcoming_recurring']:
        push_alert(snap['alerts'], 'info', 'Coming up', '{} recurring item(s) in the next two weeks.'.format(len(snap['office']['upcoming_recurring'])))
    snap['pl'] = build_profit_loss(snap['sales'], snap['books'], snap['cash'])
    snap['indicators'] = build_indicators(snap)
    return _mark(snap, ['office', 'pl'], ['sales_live', 'stock', 'books'])


def pipeline_quiet(cur, user_id, snap, bits):
    """Dashboard only — compute P/L quietly so the footer is honest, skip live desks."""
    sales_rows = fetch_sales(cur, user_id)
    income_rows = fetch_income(cur, user_id)
    expense_rows = fetch_expenses(cur, user_id)
    snap['sales'] = build_sales_trackers(sales_rows)
    snap['books'] = build_books_trackers(income_rows, expense_rows)
    snap['pl'] = build_profit_loss(snap['sales'], snap['books'], snap['cash'])
    push_alert(snap['alerts'], 'info', 'Quiet mode', 'Desks are asleep. Switch mode in Settings to wake a module.')
    snap['indicators'] = build_indicators(snap)
    return _mark(snap, ['pl'], ['sales_desk', 'stock', 'office', 'cash'])


def pipeline_full(cur, user_id, snap, bits):
    """Every optional pipeline runs."""
    sales_rows = fetch_sales(cur, user_id)
    income_rows = fetch_income(cur, user_id)
    expense_rows = fetch_expenses(cur, user_id)
    cash_rows = fetch_cash(cur, user_id)
    stock_rows, _ = fetch_stock(cur, user_id, bits['threshold'])
    snap['sales'] = build_sales_trackers(sales_rows)
    snap['books'] = build_books_trackers(income_rows, expense_rows)
    snap['cash'] = build_cash_trackers(cash_rows)
    snap['stock'] = build_stock_trackers(stock_rows, bits['threshold'])
    snap['office']['open_tasks'] = fetch_open_tasks(cur, user_id)
    snap['office']['upcoming_recurring'] = fetch_upcoming_recurring(cur, user_id)
    today = today_iso()
    snap['office']['overdue_tasks'] = len(
        [t for t in snap['office']['open_tasks'] if t.get('due_date') and t['due_date'] < today]
    )
    snap['pl'] = build_profit_loss(snap['sales'], snap['books'], snap['cash'])
    if snap['stock']['low'] or snap['stock']['out']:
        push_alert(
            snap['alerts'],
            'warn',
            'Stock watch',
            '{} low, {} out.'.format(len(snap['stock']['low']), len(snap['stock']['out'])),
        )
    if snap['pl']['operating'] < 0:
        push_alert(snap['alerts'], 'danger', 'Operating loss', 'See the P/L bar for the full split.')
    if bits['monthly_goal'] and snap['sales']['month_revenue'] < bits['monthly_goal']:
        left = money_round(bits['monthly_goal'] - snap['sales']['month_revenue'])
        push_alert(snap['alerts'], 'info', 'Goal gap', '{} left to hit this month’s sales goal.'.format(left))
    snap['indicators'] = build_indicators(snap)
    return _mark(
        snap,
        ['sales', 'books', 'cash', 'stock', 'office', 'pl'],
        [],
    )


def pipeline_custom(cur, user_id, snap, bits, live_modules):
    """Wake only the modules the owner ticked."""
    ran, skipped = [], []
    live = set(live_modules or [])
    if 'sales' in live or 'counter' in live:
        snap['sales'] = build_sales_trackers(fetch_sales(cur, user_id))
        ran.append('sales')
    else:
        skipped.append('sales')
    if 'bookkeeping' in live or 'accounts' in live:
        snap['books'] = build_books_trackers(fetch_income(cur, user_id), fetch_expenses(cur, user_id))
        ran.append('books')
    else:
        skipped.append('books')
    if 'bookkeeping' in live:
        snap['cash'] = build_cash_trackers(fetch_cash(cur, user_id))
        ran.append('cash')
    else:
        skipped.append('cash')
    if 'stock' in live:
        rows, _ = fetch_stock(cur, user_id, bits['threshold'])
        snap['stock'] = build_stock_trackers(rows, bits['threshold'])
        ran.append('stock')
    else:
        skipped.append('stock')
    if 'workspace' in live or 'operations' in live:
        snap['office']['open_tasks'] = fetch_open_tasks(cur, user_id)
        snap['office']['upcoming_recurring'] = fetch_upcoming_recurring(cur, user_id)
        ran.append('office')
    else:
        skipped.append('office')
    snap['pl'] = build_profit_loss(snap['sales'], snap['books'], snap['cash'])
    ran.append('pl')
    snap['indicators'] = build_indicators(snap)
    return _mark(snap, ran, skipped)


PIPELINES = {
    'till': pipeline_till,
    'books': pipeline_books,
    'office': pipeline_office,
    'quiet': pipeline_quiet,
    'full': pipeline_full,
    'custom': pipeline_custom,
}


def run_selected_mode(cur, user_id, mode, live_modules=None):
    """
    Entry point. Runs one pipeline. The other five stay dormant.
    """
    mode = (mode or 'full').strip() or 'full'
    snap = empty_snapshot(mode)
    bits = fetch_settings_bits(cur, user_id)
    snap['monthly_goal'] = bits['monthly_goal']
    snap['tutorial_completed'] = bits['tutorial_completed']
    snap['goal_progress_pct'] = 0.0
    runner = PIPELINES.get(mode, pipeline_full)
    if mode == 'custom':
        runner(cur, user_id, snap, bits, live_modules or [])
    else:
        runner(cur, user_id, snap, bits)
    # Goal uses live sales month figure after the pipeline
    if bits['monthly_goal']:
        snap['goal_progress_pct'] = min(100.0, pct(snap['sales']['month_revenue'], bits['monthly_goal']))
    else:
        snap['goal_progress_pct'] = 0.0
    return snap


def activities_feed(cur, user_id, limit=10):
    try:
        cur.execute(
            '''
            SELECT username, action, details, created_at
            FROM activities
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT %s
            ''',
            (user_id, limit),
        )
        return [dict(row) for row in (cur.fetchall() or [])]
    except Exception:
        return []
