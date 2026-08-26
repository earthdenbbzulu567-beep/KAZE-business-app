import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { I as listCustomers, M as getSettings, g as deleteCustomer, n as addCustomer, tt as updateCustomer } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { r as downloadCsv } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { i as DialogTitle, n as DialogContent, r as DialogHeader, t as Dialog } from "./dialog-gZJ4g5it.mjs";
import { t as Textarea } from "./textarea-B7g5K7Zm.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/customers-BvgyT5D6.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function CustomersPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	const [symbol, setSymbol] = (0, import_react.useState)("$");
	const [edit, setEdit] = (0, import_react.useState)(null);
	async function load() {
		const [s, list] = await Promise.all([getSettings(), listCustomers()]);
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
				title: "Customers",
				description: "Contacts and lifetime spend from recorded sales.",
				actions: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					onClick: () => downloadCsv("customers.csv", [
						"Name",
						"Email",
						"Phone",
						"Address",
						"Orders",
						"Spent"
					], rows.map((c) => [
						c.name,
						c.email,
						c.phone,
						c.address,
						String(c.order_count),
						String(c.total_spent)
					])),
					children: "Export CSV"
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-2",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					await addCustomer({ data: {
						name: String(fd.get("name") ?? ""),
						email: String(fd.get("email") ?? ""),
						phone: String(fd.get("phone") ?? ""),
						address: String(fd.get("address") ?? ""),
						notes: String(fd.get("notes") ?? "")
					} });
					form.reset();
					toast.success("Customer saved");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Name",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "name",
							required: true,
							placeholder: "Customer name"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Email",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "email",
							type: "email"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Phone",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, { name: "phone" })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Address",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, { name: "address" })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Notes",
						className: "sm:col-span-2 space-y-1.5",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
							name: "notes",
							rows: 2
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						type: "submit",
						size: "sm",
						children: "Save customer"
					}) })
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Name",
					"Email",
					"Phone",
					"Orders",
					"Spent",
					""
				],
				empty: rows.length === 0,
				children: rows.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: c.name }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: c.email || "—"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: c.phone || "—" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "tabular",
						children: c.order_count
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: c.total_spent,
						symbol
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: () => setEdit(c),
							children: "Edit"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								if (!confirm("Delete this customer?")) return;
								await deleteCustomer({ data: { id: c.id } });
								toast.success("Deleted");
								await load();
							},
							children: "Delete"
						})]
					}) })
				] }, c.id))
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
				open: !!edit,
				onOpenChange: (o) => !o && setEdit(null),
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Edit customer" }) }), edit ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
					className: "space-y-3",
					onSubmit: async (e) => {
						e.preventDefault();
						const fd = new FormData(e.currentTarget);
						await updateCustomer({ data: {
							id: edit.id,
							name: String(fd.get("name") ?? ""),
							email: String(fd.get("email") ?? ""),
							phone: String(fd.get("phone") ?? ""),
							address: String(fd.get("address") ?? ""),
							notes: String(fd.get("notes") ?? "")
						} });
						setEdit(null);
						toast.success("Saved");
						await load();
					},
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Name",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "name",
								defaultValue: edit.name,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Email",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "email",
								type: "email",
								defaultValue: edit.email
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Phone",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "phone",
								defaultValue: edit.phone
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Address",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "address",
								defaultValue: edit.address
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Notes",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
								name: "notes",
								defaultValue: edit.notes,
								rows: 3
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
export { CustomersPage as component };
