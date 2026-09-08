# KAZE 2.6.7 — PDF fix + restored static logos

Every PDF route uses `_brand_logo_image()`. That helper now checks `static/logo_icon.png` exists before loading it. If the file is missing, it draws a green K badge so invoices, receipts, SWOT, business plan, price list, stock valuation, P&L, statements, and the guide still export.

`static/` is restored:
- logo_icon.png
- logo_full.png
- favicon-32.png / favicon-64.png
- apple-touch-icon.png

Sale receipts use LEFT JOIN so a deleted product does not break the PDF.
Unused variables removed from `mode_runtime.py`.

Dashboard still has Sales as the first tab and a bottom P/L strip.
Modes still gate which pipeline runs.

Restart the Render service after upload. Keep `DATABASE_URL`.
