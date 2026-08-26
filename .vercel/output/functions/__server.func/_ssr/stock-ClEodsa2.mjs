import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { C as deleteStock, H as listStock, M as getSettings, l as addStock, nt as updateStock } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Card } from "./card-CyLphHyC.mjs";
import { r as downloadCsv } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { i as DialogTitle, n as DialogContent, r as DialogHeader, t as Dialog } from "./dialog-gZJ4g5it.mjs";
import { a as XAxis, c as CartesianGrid, d as Tooltip, i as YAxis, l as Bar, r as BarChart, u as ResponsiveContainer } from "../_libs/recharts+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/stock-ClEodsa2.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function StockPage() {
	const [items, setItems] = (0, import_react.useState)(null);
	const [settings, setSettings] = (0, import_react.useState)(null);
	const [edit, setEdit] = (0, import_react.useState)(null);
	async function load() {
		const [s, rows] = await Promise.all([getSettings(), listStock()]);
		setSettings(s);
		setItems(rows);
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!items || !settings) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	const symbol = settings.currency_symbol;
	const chart = items.map((i) => ({
		name: i.product_name,
		value: i.quantity * i.cost_price
	}));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Stock",
				description: "Quantity, cost, and selling price. Sales reduce quantity automatically.",
				actions: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					onClick: () => downloadCsv("stock.csv", [
						"Product",
						"Qty",
						"Unit",
						"Cost",
						"Selling"
					], items.map((i) => [
						i.product_name,
						String(i.quantity),
						i.unit,
						String(i.cost_price),
						String(i.selling_price)
					])),
					children: "Export CSV"
				})
			}),
			chart.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, {
				className: "h-64 p-4",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
					width: "100%",
					height: "100%",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(BarChart, {
						data: chart,
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CartesianGrid, {
								stroke: "var(--kaze-border)",
								vertical: false
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
								dataKey: "name",
								tick: {
									fill: "var(--kaze-muted)",
									fontSize: 11
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
								dataKey: "value",
								fill: "var(--kaze-brand)",
								radius: [
									4,
									4,
									0,
									0
								]
							})
						]
					})
				})
			}) : null,
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-6",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					await addStock({ data: {
						product_name: String(fd.get("product_name") ?? ""),
						quantity: Number(fd.get("quantity")),
						cost_price: Number(fd.get("cost_price")),
						selling_price: Number(fd.get("selling_price")),
						unit: String(fd.get("unit") ?? "pcs")
					} });
					form.reset();
					toast.success("Stock added");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Product",
						className: "sm:col-span-2 space-y-1.5",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "product_name",
							required: true,
							placeholder: "Rice 25kg"
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
						label: "Cost",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "cost_price",
							type: "number",
							step: "0.01",
							required: true
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Selling",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "selling_price",
							type: "number",
							step: "0.01",
							required: true
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Unit",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "unit",
							placeholder: "pcs"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex items-end sm:col-span-6",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							size: "sm",
							children: "Add stock"
						})
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Product",
					"Qty",
					"Unit",
					"Cost",
					"Selling",
					"Value",
					""
				],
				empty: items.length === 0,
				children: items.map((i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: i.product_name }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: i.quantity < settings.low_stock_threshold ? "text-out" : "",
						children: i.quantity
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: i.unit }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: i.cost_price,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: i.selling_price,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: i.quantity * i.cost_price,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: () => setEdit(i),
							children: "Edit"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								if (!confirm("Delete this product?")) return;
								await deleteStock({ data: { id: i.id } });
								toast.success("Deleted");
								await load();
							},
							children: "Delete"
						})]
					}) })
				] }, i.id))
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
				open: !!edit,
				onOpenChange: (o) => !o && setEdit(null),
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Edit stock" }) }), edit ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
					className: "space-y-3",
					onSubmit: async (e) => {
						e.preventDefault();
						const fd = new FormData(e.currentTarget);
						await updateStock({ data: {
							id: edit.id,
							product_name: String(fd.get("product_name") ?? ""),
							quantity: Number(fd.get("quantity")),
							cost_price: Number(fd.get("cost_price")),
							selling_price: Number(fd.get("selling_price")),
							unit: String(fd.get("unit") ?? "pcs")
						} });
						setEdit(null);
						toast.success("Saved");
						await load();
					},
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Product",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "product_name",
								defaultValue: edit.product_name,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Quantity",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "quantity",
								type: "number",
								step: "any",
								defaultValue: edit.quantity,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Cost",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "cost_price",
								type: "number",
								step: "0.01",
								defaultValue: edit.cost_price,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Selling",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "selling_price",
								type: "number",
								step: "0.01",
								defaultValue: edit.selling_price,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Unit",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "unit",
								defaultValue: edit.unit
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							children: "Save changes"
						})
					]
				}) : null] })
			})
		]
	});
}
//#endregion
export { StockPage as component };
