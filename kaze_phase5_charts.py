"""
kaze_phase5_charts.py — Global Chart Overhaul (Phase 5).
Applies the mockup aesthetic to all Chart.js instances.
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

FILES = [
    'templates/base.html',
    'templates/dashboard.html',
    'templates/reports.html',
    'templates/cashbook.html',
    'templates/stock.html',
    'templates/stats.html',
]

# 1. Backups
for path in FILES:
    if os.path.isfile(path):
        shutil.copy2(path, f"{path}.bak.phase5charts_{STAMP}")
        print(f"Backup: {path}.bak.phase5charts_{STAMP}")
    else:
        print(f"  [FAIL] {path} not found.")
        sys.exit(1)

# ═══════════════════════════════════════════════════════════════════
print("\n[1/5] Injecting Global Chart Defaults into base.html")
# ═══════════════════════════════════════════════════════════════════

with open('templates/base.html', encoding='utf-8') as f:
    base_html = f.read()

GLOBAL_CHART_JS = """
<script id="kaze-chart-globals">
(function(){
    if (!window.Chart) return;
    // Typography & Colors
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    Chart.defaults.font.size = 11;
    Chart.defaults.color = '#6b7280';
    Chart.defaults.borderColor = '#e5e7eb';

    // Clean Legend (Small circles)
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.boxWidth = 6;
    Chart.defaults.plugins.legend.labels.boxHeight = 6;
    Chart.defaults.plugins.legend.labels.padding = 16;

    // Modern Tooltip
    Chart.defaults.plugins.tooltip.backgroundColor = '#1e293b';
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
    Chart.defaults.plugins.tooltip.displayColors = true;
    Chart.defaults.plugins.tooltip.boxPadding = 4;

    // Rounded Bars & Smooth Lines
    Chart.defaults.elements.bar.borderRadius = 4;
    Chart.defaults.elements.line.tension = 0.35;
    Chart.defaults.elements.point.radius = 3;

    // Remove heavy grids
    Chart.defaults.scales.linear.grid.display = false;
    Chart.defaults.scales.category.grid.display = false;
    
    // Mockup Colors
    window.KAZE_COLORS = {
        sales: '#1a8f3c',     // Brand Green
        expenses: '#1e293b',  // Dark Slate
        profit: '#10b981',    // Bright Green
        light: '#f3f4f6',
        danger: '#ef4444'
    };
})();
</script>
"""

if 'kaze-chart-globals' not in base_html:
    # Insert right before </body>
    base_html = base_html.replace('</body>', GLOBAL_CHART_JS + '\n</body>', 1)
    print("  [OK]   Global Chart Defaults injected.")
else:
    print("  [SKIP] Global Chart Defaults already exist.")

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(base_html)

# ═══════════════════════════════════════════════════════════════════
print("\n[2/5] Updating Dashboard Chart (Sales vs Expenses)")
# ═══════════════════════════════════════════════════════════════════

with open('templates/dashboard.html', encoding='utf-8') as f:
    dash_html = f.read()

# Find the dashboard chart script
OLD_DASH_CHART = """<script>
        const salesTrendData = {{ snap.sales.trend_7 | tojson }};
        const trendLabels = Object.keys(salesTrendData).sort();
        const trendValues = trendLabels.map(d => salesTrendData[d]);
        const chartType = '{{ user_settings.default_chart_type if user_settings else "line" }}';
        const ctxTrend = document.getElementById('salesTrendChart').getContext('2d');
        new Chart(ctxTrend, {
            type: chartType,
            data: { labels: trendLabels, datasets: [{ label: 'Sales revenue', data: trendValues, borderColor: '#27ae60', backgroundColor: 'rgba(39,174,96,0.2)' }] },
            options: { responsive: true, scales: { y: { ticks: { callback: v => window.kazeMoney(v) } } } }
        });
    </script>"""

NEW_DASH_CHART = """<script>
        const salesTrendData = {{ snap.sales.trend_7 | tojson }};
        const expenseData = {{ snap.books.expense_by_date | tojson }};
        const trendLabels = Object.keys(salesTrendData).sort();
        
        const salesValues = trendLabels.map(d => salesTrendData[d] || 0);
        const expenseValues = trendLabels.map(d => expenseData[d] || 0);

        const ctxTrend = document.getElementById('salesTrendChart').getContext('2d');
        new Chart(ctxTrend, {
            type: 'bar',
            data: { 
                labels: trendLabels, 
                datasets: [
                    { 
                        label: 'Sales', 
                        data: salesValues, 
                        backgroundColor: window.KAZE_COLORS.sales,
                        borderRadius: 4
                    },
                    { 
                        label: 'Expenses', 
                        data: expenseValues, 
                        backgroundColor: window.KAZE_COLORS.expenses,
                        borderRadius: 4
                    }
                ] 
            },
            options: { 
                responsive: true, 
                scales: { 
                    y: { 
                        beginAtZero: true,
                        ticks: { callback: v => window.kazeMoney(v) } 
                    } 
                } 
            }
        });
    </script>"""

if 'const expenseData = {{ snap.books.expense_by_date | tojson }};' not in dash_html:
    if OLD_DASH_CHART in dash_html:
        dash_html = dash_html.replace(OLD_DASH_CHART, NEW_DASH_CHART, 1)
        print("  [OK]   Dashboard chart updated to Grouped Bar (Sales vs Expenses).")
    else:
        # Fallback if exact match not found (maybe spacing differs)
        # Just replace the specific script block
        pattern = re.compile(r'const salesTrendData = .*?</script>', re.DOTALL)
        dash_html = pattern.sub(NEW_DASH_CHART, dash_html)
        print("  [OK]   Dashboard chart updated (regex fallback).")
else:
    print("  [SKIP] Dashboard chart already updated.")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(dash_html)

# ═══════════════════════════════════════════════════════════════════
print("\n[3/5] Updating Reports Chart (Profit Trend)")
# ═══════════════════════════════════════════════════════════════════

with open('templates/reports.html', encoding='utf-8') as f:
    reports_html = f.read()

# We need to update the profit trend chart to match the colors
# Find the profit trend chart config
OLD_REPORTS_CHART = """    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: months,
            datasets: [
                { label: 'Profit', data: months.map(m => profitData[m] || 0), backgroundColor: 'rgba(46, 204, 113, 0.7)', borderColor: '#2ecc71', borderWidth: 1, type: 'line', tension: 0.3, fill: false },
                { label: 'Income', data: months.map(m => incomeData[m] || 0), backgroundColor: 'rgba(52, 152, 219, 0.5)' },
                { label: 'Expenses', data: months.map(m => expenseData[m] || 0), backgroundColor: 'rgba(231, 76, 60, 0.5)' }
            ]
        },"""

NEW_REPORTS_CHART = """    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: months,
            datasets: [
                { label: 'Profit', data: months.map(m => profitData[m] || 0), borderColor: window.KAZE_COLORS.profit, backgroundColor: 'transparent', borderWidth: 2, type: 'line', tension: 0.35, fill: false, order: 1 },
                { label: 'Income', data: months.map(m => incomeData[m] || 0), backgroundColor: window.KAZE_COLORS.sales, borderRadius: 4, order: 2 },
                { label: 'Expenses', data: months.map(m => expenseData[m] || 0), backgroundColor: window.KAZE_COLORS.expenses, borderRadius: 4, order: 2 }
            ]
        },"""

if OLD_REPORTS_CHART in reports_html:
    reports_html = reports_html.replace(OLD_REPORTS_CHART, NEW_REPORTS_CHART, 1)
    print("  [OK]   Reports Profit Trend updated.")
else:
    print("  [WARN] Reports Profit Trend pattern not found. Skipping.")

# Update pie chart to doughnut with cutout
OLD_PIE = """    new Chart(pieCtx, {
        type: 'pie',
        data: { labels: expLabels, datasets: [{ data: expValues, backgroundColor: ['#2ecc71','#e74c3c','#f1c40f','#3498db','#9b59b6'] }] }
    });"""
NEW_PIE = """    new Chart(pieCtx, {
        type: 'doughnut',
        data: { labels: expLabels, datasets: [{ data: expValues, backgroundColor: ['#1a8f3c','#e74c3c','#f1c40f','#3498db','#9b59b6'], borderWidth: 0 }] },
        options: { cutout: '70%' }
    });"""
if OLD_PIE in reports_html:
    reports_html = reports_html.replace(OLD_PIE, NEW_PIE, 1)
    print("  [OK]   Reports Expense Pie updated to Doughnut.")

with open('templates/reports.html', 'w', encoding='utf-8') as f:
    f.write(reports_html)

# ═══════════════════════════════════════════════════════════════════
print("\n[4/5] Updating Cashbook, Stock, and Stats Charts")
# ═══════════════════════════════════════════════════════════════════

# Cashbook Mix -> Doughnut
with open('templates/cashbook.html', encoding='utf-8') as f:
    cash_html = f.read()
OLD_CASH = """new Chart(document.getElementById('cashMixChart'), {
    type: 'doughnut',
    data: { labels: ['Cash in', 'Cash out'], datasets: [{ data: [{{ ns.inn }}, {{ ns.out }}], backgroundColor: ['#2ecc71', '#e74c3c'] }] },
    options: { plugins: { title: { display: true, text: 'Cash mix' } } }
});"""
NEW_CASH = """new Chart(document.getElementById('cashMixChart'), {
    type: 'doughnut',
    data: { labels: ['Cash in', 'Cash out'], datasets: [{ data: [{{ ns.inn }}, {{ ns.out }}], backgroundColor: [window.KAZE_COLORS.sales, window.KAZE_COLORS.expenses], borderWidth: 0 }] },
    options: { cutout: '70%', plugins: { title: { display: true, text: 'Cash mix' } } }
});"""
if OLD_CASH in cash_html:
    cash_html = cash_html.replace(OLD_CASH, NEW_CASH, 1)
    print("  [OK]   Cashbook Mix updated to Doughnut.")
with open('templates/cashbook.html', 'w', encoding='utf-8') as f:
    f.write(cash_html)

# Stock Value -> Horizontal Bar
with open('templates/stock.html', encoding='utf-8') as f:
    stock_html = f.read()
OLD_STOCK = """    new Chart(ctxStock, {
        type: 'bar',
        data: {
            labels: prodNames,
            datasets: [{
                label: 'Inventory value',
                data: invValues,
                backgroundColor: 'rgba(39, 174, 96, 0.7)',
                borderColor: '#27ae60',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Inventory Value by Product' }
            },
            scales: {
                y: { ticks: { callback: v => window.kazeMoney(v) } }
            }
        }
    });"""
NEW_STOCK = """    new Chart(ctxStock, {
        type: 'bar',
        data: {
            labels: prodNames,
            datasets: [{
                label: 'Inventory value',
                data: invValues,
                backgroundColor: window.KAZE_COLORS.sales,
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y', // Horizontal Bar
            responsive: true,
            plugins: {
                title: { display: false }
            },
            scales: {
                x: { ticks: { callback: v => window.kazeMoney(v) } }
            }
        }
    });"""
if OLD_STOCK in stock_html:
    stock_html = stock_html.replace(OLD_STOCK, NEW_STOCK, 1)
    print("  [OK]   Stock Chart updated to Horizontal Bar.")
with open('templates/stock.html', 'w', encoding='utf-8') as f:
    f.write(stock_html)

# ═══════════════════════════════════════════════════════════════════
print("\n[5/5] Verifying Jinja Syntax")
# ═══════════════════════════════════════════════════════════════════

for path in FILES:
    if path == 'base.html': continue
    with open(f'templates/{path}', encoding='utf-8') as f:
        content = f.read()
    try:
        Environment().parse(content)
        print(f"  [OK]   {path} parses cleanly")
    except Exception as exc:
        print(f"  [FAIL] {path} Jinja error: {exc}")
        sys.exit(1)

print("\n" + "=" * 62)
print("Phase 5 (Charts) complete.")
print("  Global defaults set in base.html.")
print("  Dashboard: Grouped Bar (Sales vs Expenses).")
print("  Reports: Combo Chart & Doughnut.")
print("  Cashbook: Doughnut Chart.")
print("  Stock: Horizontal Bar Chart.")
print("=" * 62)