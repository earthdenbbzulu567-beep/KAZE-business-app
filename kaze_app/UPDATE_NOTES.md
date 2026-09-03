# KAZE 2.6 update — Counter mode + Practical guide

Drop these files over your existing Render deploy (keep your current `DATABASE_URL` and env vars).

## New feature: Counter mode
- Route: `/counter`
- Sidebar: Core → Counter
- Also in the + quick-add menu and Ctrl+K
- Tap a product, set quantity, optional customer/discount, ring up
- Updates stock and today’s take immediately
- Sale note is stored as `counter` so you can tell till sales from desk sales

## Practical guide
- Page: `/tutorial` (stepper with progress, remembers last step in the browser)
- PDF: `/guide.pdf` (also saved as `KAZE_Practical_Guide.pdf`)
- Help modal still works and now points at the full guide
- Dashboard banner sends new users to the guide and Counter

## Polish
- Focus rings, press feedback, staggered stat chips
- `prefers-reduced-motion` turns animations off
- Landing page lists Counter mode

## Files touched
- `app.py` — `_guide_steps`, `tutorial`, `counter`, `counter_sale`, `guide_pdf`
- `templates/base.html` — nav, fab, command palette, motion
- `templates/counter.html` — new
- `templates/tutorial.html` — rebuilt as a guide
- `templates/_tutorial_content.html`
- `templates/dashboard.html`, `index.html`, `shortcuts.html`
