import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { v as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { H as listStock, K as receiveOrder, M as getSettings, U as listSuppliers, b as deleteOrder, o as addOrder, z as listOrders } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Badge } from "./badge-TfmHgfhb.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/orders-DWi4XQBg.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function OrdersPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	const [suppliers, setSuppliers] = (0, import_react.useState)([]);
	const [stock, setStock] = (0, import_react.useState)([]);
	const [symbol, setSymbol] = (0, import_react.useState)("$");
	async function load() {
		const [s, list, sup, st] = await Promise.all([
			getSettings(),
			listOrders(),
			listSuppliers(),
			listStock()
		]);
		setSymbol(s.currency_symbol);
		setRows(list);
		setSuppliers(sup);
		setStock(st);
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!rows) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Purchase orders",
				description: "Order stock from suppliers. Receiving an order can add quantity to inventory.",
				actions: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					asChild: true,
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
						to: "/suppliers",
						children: "Suppliers"
					})
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					const sid = String(fd.get("supplier_id") ?? "");
					const stid = String(fd.get("stock_id") ?? "");
					await addOrder({ data: {
						supplier_id: sid ? Number(sid) : null,
						item_description: String(fd.get("item_description") ?? ""),
						quantity: Number(fd.get("quantity")),
						unit_cost: Number(fd.get("unit_cost")),
						expected_date: String(fd.get("expected_date") ?? ""),
						stock_id: stid ? Number(stid) : null
					} });
					form.reset();
					toast.success("Order created");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Supplier",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							name: "supplier_id",
							defaultValue: "",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "",
								children: "No supplier"
							}), suppliers.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: s.id,
								children: s.name
							}, s.id))]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Item",
						className: "sm:col-span-2 space-y-1.5",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "item_description",
							required: true,
							placeholder: "What are you ordering?"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Link to stock",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							name: "stock_id",
							defaultValue: "",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "",
								children: "Not linked"
							}), stock.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: s.id,
								children: s.product_name
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
						label: "Unit cost",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "unit_cost",
							type: "number",
							step: "0.01",
							required: true
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Expected",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "expected_date",
							type: "date"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex items-end",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							size: "sm",
							children: "Create order"
						})
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Item",
					"Supplier",
					"Qty",
					"Unit cost",
					"Total",
					"Status",
					"Expected",
					""
				],
				empty: rows.length === 0,
				children: rows.map((po) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: po.item_description }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: po.supplier_name || "—" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "tabular",
						children: po.quantity
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: po.unit_cost,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: po.total_cost,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: po.status === "received" ? "in" : "warn",
						children: po.status === "received" ? "Received" : "Pending"
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: po.expected_date || "—"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [po.status !== "received" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								await receiveOrder({ data: { id: po.id } });
								toast.success("Received");
								await load();
							},
							children: "Receive"
						}) : null, /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								await deleteOrder({ data: { id: po.id } });
								toast.success("Deleted");
								await load();
							},
							children: "Delete"
						})]
					}) })
				] }, po.id))
			})
		]
	});
}
//#endregion
export { OrdersPage as component };
