import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { M as getSettings, j as getReports } from "./server-BeIiaNi3.mjs";
import { n as Money, r as SectionLabel } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Card } from "./card-CyLphHyC.mjs";
import { a as XAxis, c as CartesianGrid, d as Tooltip, i as YAxis, l as Bar, s as Line, t as ComposedChart, u as ResponsiveContainer } from "../_libs/recharts+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/reports-CxNvTcAb.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function ReportsPage() {
	const [data, setData] = (0, import_react.useState)(null);
	const [symbol, setSymbol] = (0, import_react.useState)("$");
	(0, import_react.useEffect)(() => {
		(async () => {
			const [s, r] = await Promise.all([getSettings(), getReports()]);
			setSymbol(s.currency_symbol);
			setData(r);
		})();
	}, []);
	if (!data) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	const chart = data.months.map((m) => ({
		month: m,
		income: data.monthlyIncome[m] ?? 0,
		expenses: data.monthlyExpenses[m] ?? 0,
		profit: data.monthlyProfit[m] ?? 0
	}));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Reports",
				description: "Six-month profit trend and your best products and customers."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, {
				className: "h-72 p-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
					width: "100%",
					height: "100%",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(ComposedChart, {
						data: chart,
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CartesianGrid, {
								stroke: "var(--kaze-border)",
								vertical: false
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
								dataKey: "month",
								tick: {
									fill: "var(--kaze-muted)",
									fontSize: 12
								}
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(YAxis, { tick: {
								fill: "var(--kaze-muted)",
								fontSize: 12
							} }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Tooltip, { contentStyle: {
								background: "var(--kaze-surface)",
								border: "1px solid var(--kaze-border)",
								borderRadius: 12
							} }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Bar, {
								dataKey: "income",
								fill: "var(--kaze-in)",
								fillOpacity: .45
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Bar, {
								dataKey: "expenses",
								fill: "var(--kaze-out)",
								fillOpacity: .45
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Line, {
								type: "monotone",
								dataKey: "profit",
								stroke: "var(--kaze-brand)",
								strokeWidth: 2
							})
						]
					})
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-6 lg:grid-cols-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Top products" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
					headers: [
						"Product",
						"Units",
						"Revenue",
						"Profit"
					],
					empty: data.topProducts.length === 0,
					children: data.topProducts.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: p.product_name }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
							className: "tabular",
							children: p.units
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
							amount: p.revenue,
							symbol
						}) }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
							amount: p.profit,
							symbol,
							tone: "in"
						}) })
					] }, p.product_name))
				})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Top customers" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
					headers: [
						"Customer",
						"Orders",
						"Spent"
					],
					empty: data.topCustomers.length === 0,
					children: data.topCustomers.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: c.customer_name }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
							className: "tabular",
							children: c.orders
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
							amount: c.spent,
							symbol
						}) })
					] }, c.customer_name))
				})] })]
			})
		]
	});
}
//#endregion
export { ReportsPage as component };
