"""
kaze_phase4g_tablefix.py — Fix table overflow on analytics pages.
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime
from jinja2 import Environment

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')

FILES = [
    'templates/sales_analytics.html',
    'templates/customers_analytics.html',
    'templates/stock_analytics.html',
    'templates/accounts_health.html',
    'templates/analytics_decisions.html',
    'templates/analytics_patterns.html',
    'templates/team_health.html',
    'templates/workflow_signals.html',
    'templates/services_analytics.html',
    'templates/settings_audit.html',
]

for path in FILES:
    if not os.path.isfile(path):
        print(f"ERROR: {path} not found.")
        sys.exit(1)

FIX_CSS = """
/* --- Table Overflow Fix --- */
.page-content .table-wrapper {
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch;
}
.page-content table {
    width: 100% !important;
    table-layout: auto !important;
}
.page-content th, 
.page-content td {
    white-space: nowrap !important; /* Prevents numbers from breaking mid-digit */
    padding: 12px 16px !important;
}
.page-content td {
    font-variant-numeric: tabular-nums !important; /* Aligns all numbers perfectly */
}
"""

for path in FILES:
    with open(path, encoding='utf-8') as f:
        html = f.read()

    if '/* --- Table Overflow Fix --- */' in html:
        print(f"  [SKIP] {path} — fix already applied")
        continue

    # Inject right before the closing </style> tag
    if '</style>' in html:
        html = html.replace('</style>', FIX_CSS + '\n</style>', 1)
    else:
        print(f"  [FAIL] {path} — no </style> tag found")
        continue

    try:
        Environment().parse(html)
        print(f"  [OK]   {path} parsed")
    except Exception as exc:
        print(f"  [FAIL] {path} Jinja error: {exc}")
        continue

    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)

print("\nTable overflow fix applied. Hard refresh (Ctrl+Shift+R) your browser.")