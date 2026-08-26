import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { v as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { D as dismissTutorial } from "./server-BeIiaNi3.mjs";
import { r as PageHeader } from "./page-header-DtL_JkzF.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/help-C-3umuYu.js
var import_jsx_runtime = require_jsx_runtime();
var STEPS = [
	{
		n: "01",
		title: "Dashboard",
		body: "Home base. Income, expenses, and profit at a glance, plus charts and a monthly goal if you set one."
	},
	{
		n: "02",
		title: "Stock",
		body: "Add products with cost and selling price. Sales reduce quantity. Rows below the threshold light up."
	},
	{
		n: "03",
		title: "Sales",
		body: "Record a sale against stock. Profit is calculated, inventory drops, and you can print a receipt."
	},
	{
		n: "04",
		title: "Customers",
		body: "A contact list with lifetime order count and spend, pulled from sales history."
	},
	{
		n: "05",
		title: "Documents",
		body: "Invoices, contracts, and reports. Print a clean copy with tax applied from Settings."
	},
	{
		n: "06",
		title: "Cash book",
		body: "Till cash in and out — separate from the income statement, useful for end-of-day reconciliation."
	},
	{
		n: "07",
		title: "SWOT and plan",
		body: "Think strategically, then keep a living business plan you can print for a partner or a bank."
	},
	{
		n: "08",
		title: "Operations",
		body: "Recurring invoices and expenses, suppliers, purchase orders that restock inventory, and category budgets."
	},
	{
		n: "09",
		title: "Settings",
		body: "Business name, currency, tax rate, monthly goal, theme, and which dashboard widgets to show."
	}
];
function HelpPage() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Getting started",
				description: "A short tour of the desk."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("ol", {
				className: "space-y-6",
				children: STEPS.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
					className: "flex gap-4",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "grid size-9 shrink-0 place-items-center rounded-full bg-brand text-xs font-medium text-bg",
						children: s.n
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
						className: "font-medium",
						children: s.title
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-1 max-w-xl text-sm text-muted",
						children: s.body
					})] })]
				}, s.n))
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "rounded-xl bg-surface px-6 py-8 text-center shadow-[var(--kaze-shadow)]",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-display text-xl",
					children: "Ready to work"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-4",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						asChild: true,
						onClick: () => {
							dismissTutorial();
						},
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/dashboard",
							children: "Go to dashboard"
						})
					})
				})]
			})
		]
	});
}
//#endregion
export { HelpPage as component };
