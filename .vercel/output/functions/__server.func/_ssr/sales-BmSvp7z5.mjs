import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { H as listStock, I as listCustomers, M as getSettings, S as deleteSale, V as listSales, c as addSale } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Card } from "./card-CyLphHyC.mjs";
import { c as todayISO, i as money, r as downloadCsv, s as printHtml } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { a as XAxis, c as CartesianGrid, d as Tooltip, i as YAxis, n as AreaChart, o as Area, u as ResponsiveContainer } from "../_libs/recharts+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/sales-BmSvp7z5.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function SalesPage() {
	const [sales, setSales] = (0, import_react.useState)(null);
	const [stock, setStock] = (0, import_react.useState)([]);
	const [customers, setCustomers] = (0, import_react.useState)([]);
	const [settings, setSettings] = (0, import_react.useState)(null);
	async function load() {
		const [s, rows, st, cu] = await Promise.all([
			getSettings(),
			listSales(),
			listStock(),
			listCustomers()
		]);
		setSettings(s);
		setSales(rows);
		setStock(st);
		setCustomers(cu);
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!sales || !settings) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	const symbol = settings.currency_symbol;
	const byDate = {};
	for (const s of sales) byDate[s.sale_date] = (byDate[s.sale_date] ?? 0) + s.total_amount;
	const chart = Object.keys(byDate).sort().map((d) => ({
		date: d.slice(5),
		total: byDate[d]
	}));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Sales",
				description: "Record a sale against stock. Profit is calculated and inventory drops.",
				actions: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					onClick: () => downloadCsv("sales.csv", [
						"Product",
						"Qty",
						"Price",
						"Total",
						"Profit",
						"Date",
						"Customer"
					], sales.map((s) => [
						s.product_name,
						String(s.quantity_sold),
						String(s.selling_price_at_time),
						String(s.total_amount),
						String(s.profit),
						s.sale_date,
						s.customer_name
					])),
					children: "Export CSV"
				})
			}),
			chart.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, {
				className: "h-64 p-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
					width: "100%",
					height: "100%",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AreaChart, {
						data: chart,
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CartesianGrid, {
								stroke: "var(--kaze-border)",
								vertical: false
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
								dataKey: "date",
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
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Area, {
								type: "monotone",
								dataKey: "total",
								stroke: "var(--kaze-in)",
								fill: "var(--kaze-in)",
								fillOpacity: .15
							})
						]
					})
				})
			}) : null,
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					const cid = String(fd.get("customer_id") ?? "");
					try {
						await addSale({ data: {
							stock_id: Number(fd.get("stock_id")),
							quantity: Number(fd.get("quantity")),
							customer_id: cid ? Number(cid) : null,
							customer_name: String(fd.get("customer_name") ?? ""),
							customer_email: String(fd.get("customer_email") ?? ""),
							date: String(fd.get("date") || todayISO())
						} });
						form.reset();
						toast.success("Sale recorded");
						await load();
					} catch (err) {
						toast.error(err instanceof Error ? err.message : "Could not record sale");
					}
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Product",
						className: "sm:col-span-2 space-y-1.5",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							name: "stock_id",
							required: true,
							defaultValue: "",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "",
								disabled: true,
								children: "Select product"
							}), stock.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("option", {
								value: s.id,
								children: [
									s.product_name,
									" (stock ",
									s.quantity,
									", ",
									money(s.selling_price, symbol),
									")"
								]
							}, s.id))]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Quantity",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "quantity",
							type: "number",
							step: "any",
							required: true
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Saved customer",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							name: "customer_id",
							defaultValue: "",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "",
								children: "Walk-in / new"
							}), customers.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: c.id,
								children: c.name
							}, c.id))]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Name if new",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "customer_name",
							placeholder: "Optional"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Email if new",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "customer_email",
							type: "email",
							placeholder: "Optional"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Date",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "date",
							type: "date",
							defaultValue: todayISO()
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "sm:col-span-3",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							size: "sm",
							children: "Record sale"
						})
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Product",
					"Qty",
					"Price",
					"Total",
					"Profit",
					"Date",
					"Customer",
					""
				],
				empty: sales.length === 0,
				children: sales.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: s.product_name }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "tabular",
						children: s.quantity_sold
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: s.selling_price_at_time,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: s.total_amount,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: s.profit,
						symbol,
						tone: "in"
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: s.sale_date
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: s.customer_name || "Walk-in" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: () => {
								const tax = s.total_amount * (settings.tax_rate || 0) / 100;
								printHtml("Receipt", `<h1>${settings.business_name || "KAZE Traders"}</h1>
                       <p class="muted">Sales receipt · ${s.sale_date}</p>
                       <table>
                         <tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr>
                         <tr><td>${s.product_name}</td><td>${s.quantity_sold}</td><td>${money(s.selling_price_at_time, symbol)}</td><td>${money(s.total_amount, symbol)}</td></tr>
                       </table>
                       <p>Customer: ${s.customer_name || "Walk-in"}</p>
                       ${settings.tax_rate ? `<p>Tax (${settings.tax_rate}%): ${money(tax, symbol)}</p>` : ""}
                       <p class="total">Total ${money(s.total_amount + tax, symbol)}</p>`);
							},
							children: "Receipt"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								if (!confirm("Delete this sale and restore stock?")) return;
								await deleteSale({ data: { id: s.id } });
								toast.success("Sale deleted");
								await load();
							},
							children: "Delete"
						})]
					}) })
				] }, s.id))
			})
		]
	});
}
//#endregion
export { SalesPage as component };
