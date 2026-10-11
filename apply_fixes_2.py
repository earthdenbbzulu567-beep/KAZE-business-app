"""
apply_fixes_2.py — v4.0.0 update for KAZE.

Patches app.py (prices, trial, version, nav, small bugs) and rewrites the
LICENCE and TERMS_OF_SERVICE files with the new v4.0.0 content.

Run from the folder containing app.py:
    python apply_fixes_2.py
"""

import os
import shutil
import subprocess
import sys
from datetime import datetime

STAMP = datetime.now().strftime('%Y%m%d_%H%M%S')
FAILED, SKIPPED, APPLIED = [], [], []


def backup(path):
    if os.path.isfile(path):
        b = f"{path}.bak.{STAMP}"
        if not os.path.isfile(b):
            shutil.copy2(path, b)
        return b
    return None


def patch(path, label, old, new, required=True):
    if not os.path.isfile(path):
        print(f"  [SKIP] {label} — {path} missing")
        if required:
            FAILED.append(label)
        return
    with open(path, 'r', encoding='utf-8') as fh:
        src = fh.read()
    if old not in src:
        if new in src:
            print(f"  [SKIP] {label} — already updated")
            SKIPPED.append(label)
        else:
            print(f"  [FAIL] {label} — pattern not found")
            if required:
                FAILED.append(label)
        return
    backup(path)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(src.replace(old, new))
    print(f"  [OK]   {label}")
    APPLIED.append(label)


# ═════════════════════════════════════════════════════════════════════════
# app.py — package prices
# ═════════════════════════════════════════════════════════════════════════
print("[1/9] app.py — package prices")
patch('app.py', 'Entrepreneur price 50 -> 75',
    "        'tagline': 'Till plus a cash ledger for a growing stall.',\n        'price': 50,",
    "        'tagline': 'Till plus a cash ledger for a growing stall.',\n        'price': 75,")
patch('app.py', 'Entrepreneur + price 75 -> 150',
    "        'tagline': 'Suppliers, purchase orders, and extra papers.',\n        'price': 75,",
    "        'tagline': 'Suppliers, purchase orders, and extra papers.',\n        'price': 150,")
patch('app.py', 'Businessman price 100 -> 300',
    "        'tagline': 'Shop floor, books, reports, and tax estimate.',\n        'price': 100,",
    "        'tagline': 'Shop floor, books, reports, and tax estimate.',\n        'price': 300,")
patch('app.py', 'Businessman pro price 150 -> 350',
    "        'tagline': 'Statistics and higher desk limits for a busy shop.',\n        'price': 150,",
    "        'tagline': 'Statistics and higher desk limits for a busy shop.',\n        'price': 350,")
patch('app.py', 'CEO price 300 -> 550',
    "        'tagline': 'Every module, including account tracking.',\n        'price': 300,",
    "        'tagline': 'Every module, including account tracking.',\n        'price': 550,")
patch('app.py', "Founder price 500 -> 1100",
    "        'tagline': 'The full house with no practical desk limits.',\n        'price': 500,",
    "        'tagline': 'The full house with no practical desk limits.',\n        'price': 1100,")


# ═════════════════════════════════════════════════════════════════════════
# app.py — trial range 7..12
# ═════════════════════════════════════════════════════════════════════════
print("\n[2/9] app.py — trial days 7..12")
patch('app.py', 'trial days range 7..12',
    "        trial_day_choices=list(range(7, 18)),",
    "        trial_day_choices=list(range(7, 13)),")
patch('app.py', 'trial days clamp 17 -> 12',
    "    days = min(17, max(7, days))",
    "    days = min(12, max(7, days))")


# ═════════════════════════════════════════════════════════════════════════
# app.py — legal version
# ═════════════════════════════════════════════════════════════════════════
print("\n[3/9] app.py — legal version 4.0.0")
patch('app.py', 'LEGAL_VERSION 3.3.5 -> 4.0.0',
    "LEGAL_VERSION = '3.3.5'",
    "LEGAL_VERSION = '4.0.0'")


# ═════════════════════════════════════════════════════════════════════════
# app.py — nav highlight for sub-routes
# ═════════════════════════════════════════════════════════════════════════
print("\n[4/9] app.py — nav sub-routes")
patch('app.py', 'nav Counter endpoints',
    "        ('Counter', 'counter', 'monitor-smartphone', 'counter', ('counter', 'counter_sale')),",
    "        ('Counter', 'counter', 'monitor-smartphone', 'counter', ('counter', 'counter_sale', 'counter_checkout')),")
patch('app.py', 'nav Sales endpoints',
    "        ('Sales', 'sales', 'receipt', 'sales', ('sales', 'aged_sales')),",
    "        ('Sales', 'sales', 'receipt', 'sales', ('sales', 'aged_sales', 'auto_sale', 'repeat_sale', 'sale_to_invoice', 'sale_receipt')),")
patch('app.py', 'nav Stock endpoints',
    "        ('Stock', 'stock', 'package', 'stock', ('stock', 'edit_stock')),",
    "        ('Stock', 'stock', 'package', 'stock', ('stock', 'edit_stock', 'add_stock', 'update_stock', 'stock_bulk', 'check_low_stock', 'reorder_low_stock', 'price_list', 'stock_valuation_pdf')),")
patch('app.py', 'nav Customers endpoints',
    "        ('Customers', 'customers', 'users', 'customers', ('customers', 'edit_customer')),",
    "        ('Customers', 'customers', 'users', 'customers', ('customers', 'edit_customer', 'add_customer', 'customers_bulk', 'customer_statement')),")


# ═════════════════════════════════════════════════════════════════════════
# app.py — small bug fixes
# ═════════════════════════════════════════════════════════════════════════
print("\n[5/9] app.py — bug fixes")
patch('app.py', 'oauth provider session cleanup',
    "    session.pop('oauth_state', None)\n    session.pop('oauth_verifier', None)\n    if err or not token:",
    "    session.pop('oauth_state', None)\n    session.pop('oauth_verifier', None)\n    session.pop('oauth_provider', None)\n    if err or not token:")
patch('app.py', 'send_daily_summary closes conn',
    "    settings = cur.fetchone() or {}\n    cur.close()\n\n    if not sales_today:",
    "    settings = cur.fetchone() or {}\n    cur.close()\n    conn.close()\n\n    if not sales_today:")
patch('app.py', 'pay_plan compares stored_key',
    "    current = plan_info(settings)\n    if PLAN_RANK[wanted] <= PLAN_RANK[current['key']]:",
    "    current = plan_info(settings)\n    # Compare against the paid plan, not the trial-inflated one, so a\n    # shop on trial CEO can still buy Entrepreneur for when the trial ends.\n    if PLAN_RANK[wanted] <= PLAN_RANK[current['stored_key']]:")


# ═════════════════════════════════════════════════════════════════════════
# stripe_payments.py — remove managed_payments
# ═════════════════════════════════════════════════════════════════════════
print("\n[6/9] stripe_payments.py — remove managed_payments")
patch('stripe_payments.py', 'stripe managed_payments removed',
    "            'metadata': {str(k): str(v)[:500] for k, v in (metadata or {}).items()},\n            'managed_payments': {'enabled': False},\n        }",
    "            'metadata': {str(k): str(v)[:500] for k, v in (metadata or {}).items()},\n        }")


# ═════════════════════════════════════════════════════════════════════════
# templates — small fixes
# ═════════════════════════════════════════════════════════════════════════
print("\n[7/9] templates — small fixes")

if os.path.isfile('templates/base.html'):
    patch('templates/base.html', 'base anon bell hidden',
        "                <a href=\"{{ url_for('notifications') }}\" class=\"bell-link\" title=\"Notifications\">",
        "                {% if current_user.is_authenticated %}\n                <a href=\"{{ url_for('notifications') }}\" class=\"bell-link\" title=\"Notifications\">")
    patch('templates/base.html', 'base anon bell hidden end',
        "                </a>\n                <div class=\"user-menu\">",
        "                </a>\n                {% endif %}\n                {% if current_user.is_authenticated %}\n                <div class=\"user-menu\">")
    patch('templates/base.html', 'base anon user menu end',
        "                        <a href=\"{{ url_for('logout') }}\">Logout</a>\n                    </div>\n                </div>\n            </div>\n        </header>",
        "                        <a href=\"{{ url_for('logout') }}\">Logout</a>\n                    </div>\n                </div>\n                {% endif %}\n            </div>\n        </header>")

patch('templates/tasks.html', 'tasks dead checkbox removed',
    "<th>Notes</th><th><input type=\"checkbox\" onclick=\"kazeToggleAll(this)\"></th></tr></thead>",
    "<th>Notes</th><th></th></tr></thead>")

patch('templates/counter.html', 'counter clears discount',
    "        basket.splice(0, basket.length);\n        tiles.forEach(t => t.classList.remove('is-picked'));\n        render();\n    });",
    "        basket.splice(0, basket.length);\n        tiles.forEach(t => t.classList.remove('is-picked'));\n        discount.value = 0;\n        render();\n    });")

patch('templates/stock.html', 'stock dead jinja guard removed',
    "{% block content %}\n{% if ns is not defined %}{% endif %}\n<div class=\"page-header\">",
    "{% block content %}\n<div class=\"page-header\">")

patch('templates/legal_accept.html', 'legal_accept dup intro removed',
    "    <h1>Accept the licence</h1> <p style=\"color:var(--text2);\">Version {{ legal_version }}. The desk stays locked until you accept. Ephraim Zulu and KAZE Traders will sue, charge, and prosecute where the law allows — anyone who violates these terms.</p>\n        <p style=\"color:var(--text2);\">Version {{ legal_version }}. The desk stays locked until you accept both documents below.</p>",
    "    <h1>Accept the licence</h1>\n    <p style=\"color:var(--text2);\">Version {{ legal_version }} — beta. The desk stays locked until you accept both documents below. Ephraim Zulu and KAZE Traders will sue, charge, and prosecute where the law allows anyone who violates these terms.</p>")


# ═════════════════════════════════════════════════════════════════════════
# LICENCE — full v4.0.0 (beta) rewrite
# ═════════════════════════════════════════════════════════════════════════
print("\n[8/9] LICENCE — writing v4.0.0")

LICENCE_TEXT = r"""==============================================================================
KAZE TRADERS BUSINESS MANAGER
COPYRIGHT NOTICE, END USER LICENCE AGREEMENT, TERMS OF SERVICE,
FEATURE CONDITIONS, BREACH PENALTIES, AND TERMINATION
==============================================================================

Product:              KAZE Traders Business Manager ("KAZE", "the App")
Legal version:        4.0.0 (beta)
Brand:                KAZE Traders
Rightful owner:       Ephraim Zulu
Licensor:             Ephraim Zulu, rightful owner of KAZE Traders ("we")
Year:                 2026
Effective date:       2026-10-11
Controlling file:     LICENCE

COPYRIGHT (C) 2026 EPHRAIM ZULU AND KAZE TRADERS. ALL RIGHTS RESERVED.

By creating an account, ticking acceptance, signing in, hosting, paying,
starting a trial, or using any feature, you agree to this document.
The App records that acceptance (version and time) against your login.

Version 4.0.0 is a beta release. Features, prices, and clauses may change
before the stable release. A new legal version can require a fresh tick.

This is not personal legal, tax, or investment advice.

==============================================================================
PART A -- COPYRIGHT, LICENCE, SHARES
==============================================================================

A1. Ephraim Zulu owns KAZE Traders and the Software (source, templates,
    design, KAZE sounds, docs, this file, names, package names).
    Third-party libraries keep their own licences. Your typed shop
    data remains yours.

A2. You receive a limited, personal, non-exclusive, non-transferable,
    revocable permission to use unlocked features for your own shop
    records. You do not buy the Software, copyright, or shares.

A3. You may not sell, rent, white-label, or relicense the App; remove
    notices; claim authorship; scrape or attack a hosted copy; bypass
    package, trial, mode, or payment locks; use a payment method you
    have no right to use; or present KAZE as certified accounting,
    tax, or legal software.

A4. Shares: Ephraim Zulu may grant a percentage of KAZE Traders shares
    to whoever he chooses, only if he judges it benefits the company.
    He alone decides whether it is worth it. A grant needs a separate
    signed writing. Using or paying for the App is not a share purchase.

==============================================================================
PART B -- ACCOUNTS, TEAM, DATA
==============================================================================

B1. Keep login details accurate and passwords secret. You are
    responsible for Staff you invite.

B2. Modes only hide modules. Settings, currency, and keys are your
    operational choices.

B3. Keep your own backups. Clear data cannot be undone in-app.

B4. The App will refuse use of the desk until you accept this legal
    version. A later version may require acceptance again.

==============================================================================
PART C -- FEATURES (CONDITIONS)
==============================================================================

All shipped features are covered: dashboard; income and expenses;
stock (including bulk, import, low-stock, valuation, price list);
sales (including auto-sale, aged sales, invoice, receipt); counter /
till; customers and statements; services and sessions; book-keeping
papers (quotation through payslip and later paper types); account
tracking books (cash book through cash-flow statement and later
books); standalone cash book; banking; investments; shop listings
and orders; market value; purchase orders; suppliers; recurring
items; budgets; reports; statistics and CSV / Excel / PDF export;
tax estimate; SWOT; business plan; tasks; notes; snippets; calendar;
reminders; calculator; day close; documents; shortcuts; tutorial;
payments history; packages; team; search; notifications; activity;
backup export / import; theme and sound cues; health and job URLs.

Conditions for every feature:
  - lawful shop records only;
  - locked modules stay locked without payment or an active trial;
  - papers and totals are working records, not certified filings
    unless you confirm the law of your country;
  - wrong entries make wrong reports -- that is your responsibility.

Markdown: notes, snippets, and legal pages may use simple markdown.
Raw HTML is escaped. You are responsible for the words you save.

==============================================================================
PART D -- PACKAGES AND TRIAL
==============================================================================

One-time prices in Zambian Kwacha (hardcoded):

    New user              K 0.00       (free forever)
    New user +            K 25.00
    Entrepreneur          K 75.00
    Entrepreneur +        K 150.00
    Businessman           K 300.00
    Businessman pro       K 350.00
    Chief Executive
    Officer (CEO)         K 550.00
    Founder's premium     K 1,100.00

A paid package unlocks only after Stripe, PayPal, or Flutterwave
confirms, or a bank transfer is marked paid. One trial per shop
(7 to 12 days, default 12). Unused trial days are not paid out.

==============================================================================
PART E -- PAYMENT
==============================================================================

Only the Account Owner may pay. Opening checkout is not payment.
Provider and bank fees are yours. Refunds are not routine after a
successful unlock. Change of mind is not a refund ground. Chargebacks
after use may relock the package and count as breach.

==============================================================================
PART F -- SPECIFIC BREACH PENALTIES
==============================================================================

These penalties apply in addition to any remedy the law allows.
They are intended as a clear price for breach, not as a permission
to breach if you "pay the fine".

F1. Schedule

    Breach                              Automated / immediate result     Further penalty we will pursue
    ----------------------------------  -------------------------------  --------------------------------
    Using the App without accepting     Access blocked until you         Account may be closed if you
    this legal version                  accept                           refuse
    ----------------------------------  -------------------------------  --------------------------------
    Setting or forcing a paid package   Action refused; attempt logged   Liquidated sum equal to that
    without completed payment           as a licence breach              package price (see Part D)
    ----------------------------------  -------------------------------  --------------------------------
    Chargeback after using unlocked     Package relocked; login may      Package price + provider fees
    modules                             be suspended                     as a debt
    ----------------------------------  -------------------------------  --------------------------------
    Copying, reselling, white-labelling Immediate termination            Damages not less than K 1,100
    or relicensing the Software                                          (Founder's premium) plus all
                                                                         proven extra loss and legal costs
    ----------------------------------  -------------------------------  --------------------------------
    Removing copyright or owner names   Termination and takedown         Same floor as copying, plus
                                                                         correction of public copies
    ----------------------------------  -------------------------------  --------------------------------
    Attacking the host, scraping other  Immediate ban; keys revoked      Report to the host and, where
    shops, or breaking into data                                         the law allows, the police
    ----------------------------------  -------------------------------  --------------------------------
    Using a card or wallet without      Unlock reversed; login banned    Report as fraud; recovery of
    authority                                                            the taken amount
    ----------------------------------  -------------------------------  --------------------------------
    Sharing an Owner login as a public  Warning, then suspension         Termination if it continues
    password
    ----------------------------------  -------------------------------  --------------------------------
    False papers or tax filings made    Feature may be limited           You bear the fine from any
    from App figures                                                     authority; we are not your filer
    ----------------------------------  -------------------------------  --------------------------------
    Vulgar, offensive, or insulting     Warning, then suspension         Heavy fine as set out in F4
    language about the App or owner                                      below
    ----------------------------------  -------------------------------  --------------------------------
    Plagiarism, piracy, or unauthorised Termination and takedown;       USD 10,000 to USD 100,000 as
    distribution of the Software        keys revoked                     a liquidated sum, plus legal costs
                                                                         and further charges

F2. Liquidated amounts
    Where the table names a Kwacha or US Dollar floor, you agree that
    amount is a reasonable pre-estimate of harm to Ephraim Zulu and
    KAZE Traders for that class of breach (lost control of the product,
    support time, and enforcement). A court may award more if actual
    loss is higher.

F3. No set-off
    Paying a penalty does not buy you the right to keep breaching
    and does not transfer copyright or shares.

F4. Language and reputation
    Constructive criticism is welcome and will never be penalised.
    However, anyone who uses vulgar, offensive, or insulting language
    when discussing the App, its features, or the company -- whether
    in public posts, reviews, support tickets, social media, or private
    messages to the owner or staff -- will be heavily fined. The fine
    is at the owner's reasonable discretion, taking into account the
    severity and reach of the statement, and may be enforced as a debt
    where the law allows.

F5. Plagiarism, piracy, and unauthorised distribution
    Plagiarism, unauthorised distribution, and piracy of the Software
    will not be tolerated. Anyone caught will pay not less than
    USD 10,000 (ten thousand United States dollars) and up to
    USD 100,000 (one hundred thousand United States dollars) as a
    liquidated sum. Additional charges may apply, including but not
    limited to legal costs, provider fees, and any statutory damages
    available under copyright law.

==============================================================================
PART G -- TERMINATION
==============================================================================

G1. You may end your use at any time. Export your shop data first.
    Ending use does not create a refund or a share right.

G2. Automatic termination
    This licence ends at once, without extra notice, if you:
      (a) copy, sell, or relicense the Software without a signed grant;
      (b) bypass payment, trial, or mode locks after a recorded warning
          or logged breach;
      (c) attack the service or another shop;
      (d) refuse this legal version after it is shown to you;
      (e) use a payment method without authority;
      (f) engage in plagiarism, piracy, or unauthorised distribution of
          the Software, as described in F5.

G3. Termination on notice
    We may end or suspend the licence if you seriously or repeatedly
    break any other clause, including unpaid chargebacks or repeated
    vulgar or insulting language as described in F4.

G4. After termination
      (a) permission to use the Software ends;
      (b) paid modules relock;
      (c) you must stop using the Software and, after a written demand
          following a copyright breach, delete copies you control;
      (d) you may keep exports of your own shop data;
      (e) Parts A, F, G, H, and the liability limits still apply;
      (f) money already validly paid is not refunded because of your
          breach.

G5. Survival
    Copyright, share policy, payment debts, penalty schedule,
    termination effects, and liability limits survive termination.

==============================================================================
PART H -- ENFORCEMENT: SUE, CHARGE, PROSECUTE
==============================================================================

H1. Notice
    Ephraim Zulu and KAZE Traders will sue, charge, and -- where the
    criminal law of the relevant country allows -- prosecute anyone
    who violates this licence or the Terms of Service.

H2. What that includes
      (a) civil claims for injunctions (orders to stop and to take
          copies down);
      (b) civil claims for damages, liquidated amounts in Part F,
          provider fees, and legal costs;
      (c) reports to payment providers, hosts, app stores, and
          repositories;
      (d) criminal complaints for fraud, unauthorised access, or
          copyright offences where those offences exist.

H3. No waiver
    A delay in suing is not permission to continue. A settlement with
    one person does not bind Ephraim Zulu as to anyone else.

H4. Who may enforce
    Only Ephraim Zulu and KAZE Traders (or a lawyer they appoint)
    enforce this file. A shop user cannot use this file to sue another
    shop user except about that user's own shop data.

==============================================================================
PART I -- LIABILITY, PRIVACY, CHANGES
==============================================================================

I1. THE APP IS PROVIDED "AS IS". No warranty of uptime or correct totals.

I2. To the fullest extent the law allows, Ephraim Zulu and KAZE Traders
    are not liable for lost profits, lost data, or wrong filings.
    Where a cap must apply, it is the package fees you paid in the
    three months before the claim, or zero if you paid none -- except
    that this cap does not limit our claim against you for your breach.

I3. Passwords are hashed. Full card numbers are not stored in KAZE.

I4. This file may be updated with the App. A new legal version can
    require a fresh tick. Continued use after a reasonable chance to
    read it means you accept it.

I5. If one clause fails, the rest stands.

==============================================================================
PART J -- CONTACT LINE
==============================================================================

Product:          KAZE Traders Business Manager
Brand:            KAZE Traders
Rightful owner:   Ephraim Zulu
Copyright:        (C) 2026 Ephraim Zulu and KAZE Traders. All rights reserved.
Legal version:    4.0.0 (beta)
Effective date:   2026-10-11
Companion file:   TERMS_OF_SERVICE (this LICENCE controls if they differ)

By ticking acceptance or using the App you confirm you have read
Parts A to J, including the penalty table and the termination clauses.
"""

for candidate in ('LICENCE', 'LICENCE.txt', 'LICENCE - Copy.txt'):
    if os.path.isfile(candidate):
        backup(candidate)
        with open(candidate, 'w', encoding='utf-8') as fh:
            fh.write(LICENCE_TEXT)
        print(f"  [OK]   wrote {candidate} ({len(LICENCE_TEXT):,} bytes)")
        APPLIED.append(f'LICENCE -> {candidate}')
        break
else:
    # create the canonical name
    with open('LICENCE', 'w', encoding='utf-8') as fh:
        fh.write(LICENCE_TEXT)
    print(f"  [OK]   created LICENCE ({len(LICENCE_TEXT):,} bytes)")
    APPLIED.append('LICENCE created')


# ═════════════════════════════════════════════════════════════════════════
# TERMS_OF_SERVICE — full v4.0.0 (beta) rewrite
# ═════════════════════════════════════════════════════════════════════════
print("\n[9/9] TERMS_OF_SERVICE — writing v4.0.0")

TERMS_TEXT = r"""==============================================================================
KAZE TRADERS BUSINESS MANAGER -- TERMS OF SERVICE
==============================================================================

Companion to LICENCE version 4.0.0 (beta). If they differ, LICENCE controls.

Brand:           KAZE Traders
Rightful owner:  Ephraim Zulu
Copyright:       (C) 2026 Ephraim Zulu and KAZE Traders. All rights reserved.
Effective date:  2026-10-11

1. You accept these terms by ticking the box, signing in, paying,
   starting a trial, or using any feature. The App stores the legal
   version and the time you accepted.

2. Ephraim Zulu owns KAZE Traders and the Software. You own the shop
   data you type.

3. Locked features stay locked until payment or an active trial.
   Wrong entries make wrong reports. Notes may use simple markdown.
   Raw HTML is escaped.

4. Prices (Kwacha, one-time):
       New user              K 0       (free forever)
       New user +            K 25
       Entrepreneur          K 75
       Entrepreneur +        K 150
       Businessman           K 300
       Businessman pro       K 350
       Chief Executive
       Officer (CEO)         K 550
       Founder's premium     K 1,100

   Free trial: 7 to 12 days. One trial per shop. Unused days are not
   paid out.

5. Breach penalties (summary)
   - No acceptance: desk blocked.
   - Unpaid package force: refused, logged, debt equal to that price.
   - Chargeback after use: relock + price + provider fees.
   - Copy / resell / strip copyright: termination + damages not less
     than K 1,100 plus extra proven loss and costs.
   - Attack or fraud: ban and report to host and authorities.
   - Vulgar, offensive, or insulting language about the App or the
     owner: warning, then suspension, then a heavy fine at the owner's
     reasonable discretion. Constructive criticism is always welcome
     and is not covered by this clause.
   - Plagiarism, piracy, or unauthorised distribution of the Software:
     termination and takedown, plus a liquidated sum of not less than
     USD 10,000 and up to USD 100,000, plus legal costs and any other
     charges that apply.

6. Termination
   The licence ends at once if you copy the Software, bypass locks
   after a logged breach, attack the service, refuse this version,
   pay with a method you have no right to use, or engage in plagiarism
   or unauthorised distribution. After that you must stop using the
   Software. Shop-data exports remain yours. Breach does not create a
   refund.

7. Enforcement
   Ephraim Zulu and KAZE Traders will sue, charge, and -- where the
   law allows -- prosecute anyone who violates the licence or these
   terms.

8. Shares stay in Ephraim Zulu's discretion. Using the App is not
   buying shares.

Full text: LICENCE.
"""

for candidate in ('TERMS_OF_SERVICE', 'TERMS_OF_SERVICE.txt', 'TERMS_OF_SERVICE - Copy.txt'):
    if os.path.isfile(candidate):
        backup(candidate)
        with open(candidate, 'w', encoding='utf-8') as fh:
            fh.write(TERMS_TEXT)
        print(f"  [OK]   wrote {candidate} ({len(TERMS_TEXT):,} bytes)")
        APPLIED.append(f'TERMS -> {candidate}')
        break
else:
    with open('TERMS_OF_SERVICE', 'w', encoding='utf-8') as fh:
        fh.write(TERMS_TEXT)
    print(f"  [OK]   created TERMS_OF_SERVICE ({len(TERMS_TEXT):,} bytes)")
    APPLIED.append('TERMS_OF_SERVICE created')


# ═════════════════════════════════════════════════════════════════════════
# Verify app.py compiles
# ═════════════════════════════════════════════════════════════════════════
print("\nVerifying app.py compiles...")
if os.path.isfile('app.py'):
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
    print("\nFailed (pattern not found — usually already edited by hand):")
    for f in FAILED:
        print(f"  - {f}")
print("=" * 60)