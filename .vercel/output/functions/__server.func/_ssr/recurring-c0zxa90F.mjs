import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { B as listRecurring, M as getSettings, Q as toggleRecurring, s as addRecurring, x as deleteRecurring } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { c as todayISO } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Badge } from "./badge-TfmHgfhb.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/recurring-c0zxa90F.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function RecurringPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	const [symbol, setSymbol] = (0, import_react.useState)("$");
	async function load() {
		const [s, list] = await Promise.all([getSettings(), listRecurring()]);
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
				title: "Recurring items",
				description: "Expenses or invoices that generate automatically when their date arrives."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					await addRecurring({ data: {
						item_type: String(fd.get("item_type") ?? "expense"),
						name: String(fd.get("name") ?? ""),
						amount: Number(fd.get("amount")),
						category: String(fd.get("category") ?? ""),
						client: String(fd.get("client") ?? ""),
						frequency: String(fd.get("frequency") ?? "monthly"),
						start_date: String(fd.get("start_date") || todayISO())
					} });
					form.reset();
					toast.success("Scheduled");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Type",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							name: "item_type",
							defaultValue: "expense",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "expense",
								children: "Expense"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "invoice",
								children: "Invoice"
							})]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Name",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "name",
							required: true,
							placeholder: "Rent, retainer…"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Amount",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "amount",
							type: "number",
							step: "0.01",
							required: true
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Category (expenses)",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, { name: "category" })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Client (invoices)",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, { name: "client" })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Frequency",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							name: "frequency",
							defaultValue: "monthly",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "weekly",
									children: "Weekly"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "monthly",
									children: "Monthly"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "quarterly",
									children: "Quarterly"
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "yearly",
									children: "Yearly"
								})
							]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "First run",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "start_date",
							type: "date",
							defaultValue: todayISO()
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex items-end",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							size: "sm",
							children: "Schedule"
						})
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Type",
					"Name",
					"Amount",
					"Frequency",
					"Next run",
					"Status",
					""
				],
				empty: rows.length === 0,
				children: rows.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "capitalize",
						children: r.item_type
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: r.name }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: r.amount,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "capitalize",
						children: r.frequency
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: r.next_run_date }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: r.active ? "in" : "neutral",
						children: r.active ? "Active" : "Paused"
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								await toggleRecurring({ data: { id: r.id } });
								await load();
							},
							children: r.active ? "Pause" : "Resume"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								await deleteRecurring({ data: { id: r.id } });
								toast.success("Deleted");
								await load();
							},
							children: "Delete"
						})]
					}) })
				] }, r.id))
			})
		]
	});
}
//#endregion
export { RecurringPage as component };
