import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { J as saveBudget, M as getSettings, P as listBudgets, m as deleteBudget } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Card } from "./card-CyLphHyC.mjs";
import { t as EXPENSE_CATEGORIES } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/budgets-CBo5vJoV.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function BudgetsPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	const [symbol, setSymbol] = (0, import_react.useState)("$");
	async function load() {
		const [s, list] = await Promise.all([getSettings(), listBudgets()]);
		setSymbol(s.currency_symbol);
		setRows(list);
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!rows) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Budgets",
				description: "Monthly spending limits per expense category, tracked against this month."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "flex flex-wrap items-end gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]",
				onSubmit: async (e) => {
					e.preventDefault();
					const fd = new FormData(e.currentTarget);
					await saveBudget({ data: {
						category: String(fd.get("category") ?? "Other"),
						monthly_limit: Number(fd.get("monthly_limit"))
					} });
					toast.success("Budget saved");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Category",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Select, {
							name: "category",
							defaultValue: "Other",
							children: EXPENSE_CATEGORIES.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", { children: c }, c))
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Monthly limit",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "monthly_limit",
							type: "number",
							step: "0.01",
							required: true
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						type: "submit",
						size: "sm",
						children: "Save budget"
					})
				]
			}),
			rows.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-muted",
				children: "No budgets yet."
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "space-y-3",
				children: rows.map((b) => {
					const pct = b.monthly_limit ? b.spent / b.monthly_limit * 100 : 0;
					const over = b.spent > b.monthly_limit;
					return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "mb-2 flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
								className: "font-medium",
								children: b.category
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								variant: "ghost",
								size: "sm",
								onClick: async () => {
									await deleteBudget({ data: { id: b.id } });
									toast.success("Removed");
									await load();
								},
								children: "Remove"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "mb-2 flex justify-between text-sm text-muted",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
									amount: b.spent,
									symbol
								}),
								" of",
								" ",
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
									amount: b.monthly_limit,
									symbol
								})
							] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
								className: over ? "font-medium text-out" : "tabular",
								children: [
									Math.round(pct),
									"%",
									over ? " — over budget" : ""
								]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "h-2.5 overflow-hidden rounded-full bg-surface-2",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: `h-full rounded-full ${over ? "bg-out" : "bg-brand"}`,
								style: { width: `${Math.min(pct, 100)}%` }
							})
						})
					] }, b.id);
				})
			})
		]
	});
}
//#endregion
export { BudgetsPage as component };
