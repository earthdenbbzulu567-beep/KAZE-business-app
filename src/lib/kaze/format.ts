export function num(v: unknown): number {
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  }
  return 0;
}

export function todayISO(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function money(
  amount: number,
  symbol = "$",
  opts?: { signed?: boolean },
) {
  const abs = Math.abs(amount);
  const formatted = abs.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  if (opts?.signed) {
    if (amount < 0) return `-${symbol}${formatted}`;
    if (amount > 0) return `+${symbol}${formatted}`;
  }
  if (amount < 0) return `-${symbol}${formatted}`;
  return `${symbol}${formatted}`;
}

export function monthKey(date: string): string {
  return date.slice(0, 7);
}

export function addMonths(dateStr: string, months: number): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  const day = dt.getUTCDate();
  dt.setUTCDate(1);
  dt.setUTCMonth(dt.getUTCMonth() + months);
  const last = new Date(
    Date.UTC(dt.getUTCFullYear(), dt.getUTCMonth() + 1, 0),
  ).getUTCDate();
  dt.setUTCDate(Math.min(day, last));
  return dt.toISOString().slice(0, 10);
}

export function advanceDate(dateStr: string, frequency: string): string {
  if (frequency === "weekly") return addMonths(dateStr, 0).replace(
    /(\d{4})-(\d{2})-(\d{2})/,
    (_, y, m, d) => {
      const dt = new Date(Date.UTC(Number(y), Number(m) - 1, Number(d) + 7));
      return dt.toISOString().slice(0, 10);
    },
  );
  if (frequency === "monthly") return addMonths(dateStr, 1);
  if (frequency === "quarterly") return addMonths(dateStr, 3);
  if (frequency === "yearly") return addMonths(dateStr, 12);
  return dateStr;
}

export const EXPENSE_CATEGORIES = [
  "Food",
  "Rent",
  "Supplies",
  "Marketing",
  "Utilities",
  "Transport",
  "Wages",
  "Other",
] as const;

export const DOC_TYPES = ["invoice", "contract", "report"] as const;

export function downloadCsv(filename: string, headers: string[], rows: string[][]) {
  const esc = (v: string) => `"${v.replaceAll('"', '""')}"`;
  const csv = [headers.map(esc).join(","), ...rows.map((r) => r.map(esc).join(","))].join(
    "\n",
  );
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function printHtml(title: string, body: string) {
  const frame = document.createElement("iframe");
  frame.style.position = "fixed";
  frame.style.right = "0";
  frame.style.bottom = "0";
  frame.style.width = "0";
  frame.style.height = "0";
  frame.style.border = "0";
  document.body.appendChild(frame);
  const doc = frame.contentDocument;
  if (!doc) return;
  doc.open();
  doc.write(`<!doctype html><html><head><title>${title}</title>
    <style>
      body { font-family: Georgia, serif; color: #111; padding: 32px; }
      h1 { font-size: 22px; margin: 0 0 4px; }
      .muted { color: #555; font-size: 13px; }
      table { width: 100%; border-collapse: collapse; margin-top: 20px; }
      th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #ddd; font-size: 13px; }
      th { text-transform: uppercase; letter-spacing: .06em; font-size: 11px; color: #666; }
      .total { font-weight: 700; }
      pre { white-space: pre-wrap; font-family: Georgia, serif; }
    </style></head><body>${body}</body></html>`);
  doc.close();
  frame.onload = () => {
    frame.contentWindow?.focus();
    frame.contentWindow?.print();
    setTimeout(() => frame.remove(), 500);
  };
}
