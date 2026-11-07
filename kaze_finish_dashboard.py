import shutil
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
path = 'templates/dashboard.html'
shutil.copy2(path, f"{path}.bak.finish_{STAMP}")

with open(path, encoding='utf-8') as f:
    html = f.read()

# 1. Find the canvas
canvas_idx = html.find('<canvas id="salesTrendChart"></canvas>')
if canvas_idx == -1:
    print("[FAIL] Canvas not found in dashboard.html")
    exit(1)

# ── FIX HTML ──
# Walk backwards to find the start of the widget container
start_idx = html.rfind('<div class="widget">', 0, canvas_idx)
if start_idx == -1:
    start_idx = html.rfind('<div', 0, canvas_idx)

# Walk forwards to find the end of the widget container
end_chart_idx = html.find('</div>', canvas_idx)
end_widget_idx = html.find('</div>', end_chart_idx) + 6

NEW_HTML = """<div class="kz-chart-card" style="background: var(--kz-surface, #ffffff); border-radius: 16px; padding: 1.5rem; box-shadow: 0 4px 20px rgba(0,0,0,0.03); margin-bottom: 1.5rem; border: 1px solid var(--kz-border, #e5e7eb); width: 100%;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem; flex-wrap: wrap; gap: 1rem;">
        <div>
            <h2 style="font-size: 1.25rem; font-weight: 700; color: var(--kz-text, #111827); margin: 0 0 0.25rem; border: none; padding: 0; text-transform: none;">Sales & Expenses</h2>
            <p style="font-size: 0.85rem; color: var(--kz-text-muted, #6b7280); margin: 0;">Track your sales performance and expenses overview</p>
        </div>
        <div style="display: flex; gap: 1rem;">
            <div style="border: 1px solid var(--kz-border, #e5e7eb); border-radius: 8px; padding: 0.6rem 1rem; min-width: 120px;">
                <span style="font-size: 0.75rem; color: var(--kz-text-muted, #6b7280); display: flex; align-items: center; gap: 0.4rem; font-weight: 600;"><span style="width: 10px; height: 10px; border-radius: 3px; background: #1a8f3c; display: inline-block;"></span>Sales</span>
                <strong id="kpi-sales" style="font-size: 1.2rem; font-weight: 800; color: var(--kz-text, #111827); display: block; margin-top: 0.2rem;">{{ money(snap.sales.week_revenue) }}</strong>
            </div>
            <div style="border: 1px solid var(--kz-border, #e5e7eb); border-radius: 8px; padding: 0.6rem 1rem; min-width: 120px;">
                <span style="font-size: 0.75rem; color: var(--kz-text-muted, #6b7280); display: flex; align-items: center; gap: 0.4rem; font-weight: 600;"><span style="width: 10px; height: 10px; border-radius: 3px; background: #1e293b; display: inline-block;"></span>Expenses</span>
                <strong id="kpi-expenses" style="font-size: 1.2rem; font-weight: 800; color: var(--kz-text, #111827); display: block; margin-top: 0.2rem;">—</strong>
            </div>
        </div>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; margin-top: 1.5rem; flex-wrap: wrap; gap: 1rem;">
        <div style="display: flex; gap: 1.5rem;">
            <span style="font-size: 0.85rem; color: var(--kz-text-muted, #4b5563); display: flex; align-items: center; gap: 0.4rem; font-weight: 500;"><span style="width: 14px; height: 4px; border-radius: 2px; background: #1a8f3c; display: inline-block;"></span>Sales (K)</span>
            <span style="font-size: 0.85rem; color: var(--kz-text-muted, #4b5563); display: flex; align-items: center; gap: 0.4rem; font-weight: 500;"><span style="width: 14px; height: 8px; border-radius: 2px; background: #1e293b; display: inline-block;"></span>Expenses (K)</span>
        </div>
        <div style="border: 1px solid var(--kz-border, #e5e7eb); border-radius: 8px; padding: 0.4rem 0.8rem; font-size: 0.8rem; color: var(--kz-text-muted, #4b5563); display: flex; align-items: center; gap: 0.5rem;">
            Last 7 Days <span>▾</span>
        </div>
    </div>
    <div style="position: relative; height: 320px; width: 100%;">
        <canvas id="salesTrendChart"></canvas>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; border-top: 1px solid var(--kz-border, #e5e7eb); padding-top: 1.5rem; margin-top: 1.5rem;">
        <div style="display: flex; align-items: center; gap: 0.75rem; border-right: 1px solid var(--kz-border, #e5e7eb); padding-right: 1rem;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(26,143,60,0.1); color: #1a8f3c; display: grid; place-items: center; font-size: 1.2rem;">📈</div>
            <div>
                <span style="display: block; font-size: 0.75rem; color: var(--kz-text-muted, #6b7280);">Total Sales</span>
                <strong id="sum-sales" style="display: block; font-size: 1rem; color: var(--kz-text, #111827); font-weight: 700;">—</strong>
                <span style="font-size: 0.7rem; color: #1a8f3c;">↑ 12% vs last 7 days</span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem; border-right: 1px solid var(--kz-border, #e5e7eb); padding-right: 1rem;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(30,41,59,0.1); color: #1e293b; display: grid; place-items: center; font-size: 1.2rem;">💳</div>
            <div>
                <span style="display: block; font-size: 0.75rem; color: var(--kz-text-muted, #6b7280);">Total Expenses</span>
                <strong id="sum-expenses" style="display: block; font-size: 1rem; color: var(--kz-text, #111827); font-weight: 700;">—</strong>
                <span style="font-size: 0.7rem; color: #ef4444;">↓ 5% vs last 7 days</span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem; border-right: 1px solid var(--kz-border, #e5e7eb); padding-right: 1rem;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(26,143,60,0.1); color: #1a8f3c; display: grid; place-items: center; font-size: 1.2rem;">📊</div>
            <div>
                <span style="display: block; font-size: 0.75rem; color: var(--kz-text-muted, #6b7280);">Net Profit</span>
                <strong id="sum-net" style="display: block; font-size: 1rem; color: var(--kz-text, #111827); font-weight: 700;">—</strong>
                <span style="font-size: 0.7rem; color: #1a8f3c;">↑ 18% vs last 7 days</span>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 0.75rem;">
            <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(59,130,246,0.1); color: #3b82f6; display: grid; place-items: center; font-size: 1.2rem;">⏱️</div>
            <div>
                <span style="display: block; font-size: 0.75rem; color: var(--kz-text-muted, #6b7280);">Profit Margin</span>
                <strong id="sum-margin" style="display: block; font-size: 1rem; color: var(--kz-text, #111827); font-weight: 700;">—</strong>
                <span style="font-size: 0.7rem; color: #1a8f3c;">↑ 8% vs last 7 days</span>
            </div>
        </div>
    </div>
</div>"""

html = html[:start_idx] + NEW_HTML + html[end_widget_idx:]
print("  [OK]   Dashboard HTML replaced.")

# ── FIX JS ──
# Find the next <script> tag after the canvas
canvas_new_idx = html.find('<canvas id="salesTrendChart"></canvas>')
script_start = html.find('<script>', canvas_new_idx)
if script_start == -1:
    print("[FAIL] <script> tag not found after canvas")
    exit(1)

script_end = html.find('</script>', script_start) + 9

NEW_JS = """<script>
document.addEventListener('DOMContentLoaded', function() {
    try {
        if (typeof Chart === 'undefined') return;
        
        if (typeof ChartDataLabels !== 'undefined') {
            Chart.register(ChartDataLabels);
        }

        const canvas = document.getElementById('salesTrendChart');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        const salesTrendData = {{ snap.sales.trend_7 | default({}) | tojson | safe }};
        const expenseData = {{ snap.books.expense_by_date | default({}) | tojson | safe }};
        
        const labels = Object.keys(salesTrendData).sort();
        
        const displayLabels = labels.map(d => {
            const parts = d.split('-');
            if (parts.length === 3) {
                const dateObj = new Date(d);
                return `${parseInt(parts[2])} ${dateObj.toLocaleString('default', { month: 'short' })}`;
            }
            return d;
        });

        const salesValues = labels.map(d => salesTrendData[d] || 0);
        const expenseValues = labels.map(d => expenseData[d] || 0);

        const totalSales = salesValues.reduce((a, b) => a + b, 0);
        const totalExpenses = expenseValues.reduce((a, b) => a + b, 0);
        const netProfit = totalSales - totalExpenses;
        const margin = totalSales > 0 ? ((netProfit / totalSales) * 100).toFixed(1) : 0;

        const kpiExp = document.getElementById('kpi-expenses');
        if (kpiExp) kpiExp.textContent = window.kazeMoney(totalExpenses);
        
        const sumSales = document.getElementById('sum-sales');
        if (sumSales) sumSales.textContent = window.kazeMoney(totalSales);
        
        const sumExp = document.getElementById('sum-expenses');
        if (sumExp) sumExp.textContent = window.kazeMoney(totalExpenses);
        
        const sumNet = document.getElementById('sum-net');
        if (sumNet) sumNet.textContent = window.kazeMoney(netProfit);
        
        const sumMargin = document.getElementById('sum-margin');
        if (sumMargin) sumMargin.textContent = margin + '%';

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: displayLabels,
                datasets: [
                    {
                        type: 'line',
                        label: 'Sales',
                        data: salesValues,
                        borderColor: '#1a8f3c',
                        backgroundColor: 'transparent',
                        borderWidth: 3,
                        tension: 0.3,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#1a8f3c',
                        pointBorderWidth: 2,
                        pointRadius: 5,
                        pointHoverRadius: 7,
                        order: 0,
                        datalabels: {
                            align: 'top', anchor: 'end', offset: 6, color: '#1a8f3c', font: { weight: 'bold', size: 11 },
                            formatter: (val) => val > 0 ? (val >= 1000 ? (val/1000).toFixed(0) + 'K' : val) : ''
                        }
                    },
                    {
                        type: 'bar',
                        label: 'Expenses',
                        data: expenseValues,
                        backgroundColor: '#1e293b',
                        borderRadius: 4,
                        barPercentage: 0.7,
                        categoryPercentage: 0.6,
                        order: 1,
                        datalabels: {
                            align: 'top', anchor: 'end', offset: 6, color: '#64748b', font: { weight: 'bold', size: 11 },
                            formatter: (val) => val > 0 ? (val >= 1000 ? (val/1000).toFixed(0) + 'K' : val) : ''
                        }
                    }
                ]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                layout: { padding: { top: 20 } },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b', padding: 12,
                        callbacks: {
                            label: function(context) {
                                return context.dataset.label + ': ' + window.kazeMoney(context.parsed.y);
                            }
                        }
                    }
                },
                scales: {
                    x: { grid: { display: false }, ticks: { color: '#6b7280', font: { size: 11 }, maxRotation: 0 } },
                    y: { grid: { color: '#f3f4f6', borderDash: [5, 5] }, ticks: { color: '#6b7280', font: { size: 11 }, callback: function(value) { return value >= 1000 ? (value / 1000) + 'K' : value; } } }
                }
            }
        });
    } catch (error) {
        console.error('KAZE Chart Error: ', error);
    }
});
</script>"""

html = html[:script_start] + NEW_JS + html[script_end:]
print("  [OK]   Dashboard JS replaced.")

try:
    Environment().parse(html)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    print("  [OK]   dashboard.html saved.")
except Exception as exc:
    print(f"  [FAIL] Jinja error: {exc}")

print("\nDone. Restart Flask and hard refresh.")