//#region node_modules/.nitro/vite/services/ssr/assets/format-DhlBBqua.js
function num(v) {
	if (typeof v === "number" && Number.isFinite(v)) return v;
	if (typeof v === "string") {
		const n = Number(v);
		return Number.isFinite(n) ? n : 0;
	}
	return 0;
}
function todayISO() {
	const d = /* @__PURE__ */ new Date();
	return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function money(amount, symbol = "$", opts) {
	const formatted = Math.abs(amount).toLocaleString("en-US", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});
	if (opts?.signed) {
		if (amount < 0) return `-${symbol}${formatted}`;
		if (amount > 0) return `+${symbol}${formatted}`;
	}
	if (amount < 0) return `-${symbol}${formatted}`;
	return `${symbol}${formatted}`;
}
function monthKey(date) {
	return date.slice(0, 7);
}
function addMonths(dateStr, months) {
	const [y, m, d] = dateStr.split("-").map(Number);
	const dt = new Date(Date.UTC(y, m - 1, d));
	const day = dt.getUTCDate();
	dt.setUTCDate(1);
	dt.setUTCMonth(dt.getUTCMonth() + months);
	const last = new Date(Date.UTC(dt.getUTCFullYear(), dt.getUTCMonth() + 1, 0)).getUTCDate();
	dt.setUTCDate(Math.min(day, last));
	return dt.toISOString().slice(0, 10);
}
var EXPENSE_CATEGORIES = [
	"Food",
	"Rent",
	"Supplies",
	"Marketing",
	"Utilities",
	"Transport",
	"Wages",
	"Other"
];
function downloadCsv(filename, headers, rows) {
	const esc = (v) => `"${v.replaceAll("\"", "\"\"")}"`;
	const csv = [headers.map(esc).join(","), ...rows.map((r) => r.map(esc).join(","))].join("\n");
	const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
	const url = URL.createObjectURL(blob);
	const a = document.createElement("a");
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}
function printHtml(title, body) {
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
//#endregion
export { monthKey as a, todayISO as c, money as i, addMonths as n, num as o, downloadCsv as r, printHtml as s, EXPENSE_CATEGORIES as t };
