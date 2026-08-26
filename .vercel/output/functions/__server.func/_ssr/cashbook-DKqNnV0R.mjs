import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { F as listCash, M as getSettings, et as updateCash, h as deleteCash, t as addCash } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { c as todayISO, r as downloadCsv } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Badge } from "./badge-TfmHgfhb.mjs";
import { i as DialogTitle, n as DialogContent, r as DialogHeader, t as Dialog } from "./dialog-gZJ4g5it.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/cashbook-DKqNnV0R.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function CashPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	const [symbol, setSymbol] = (0, import_react.useState)("$");
	const [edit, setEdit] = (0, import_react.useState)(null);
	async function load() {
		const [s, list] = await Promise.all([getSettings(), listCash()]);
		setSymbol(s.currency_symbol);
		setRows(list);
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!rows) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	const inn = rows.filter((r) => r.entry_type === "in").reduce((s, r) => s + r.amount, 0);
	const out = rows.filter((r) => r.entry_type === "out").reduce((s, r) => s + r.amount, 0);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Cash book",
				description: "Till cash in and out, separate from the income statement.",
				actions: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					onClick: () => downloadCsv("cashbook.csv", [
						"Type",
						"Category",
						"Description",
						"Amount",
						"Date"
					], rows.map((r) => [
						r.entry_type,
						r.category,
						r.description,
						String(r.amount),
						r.date
					])),
					children: "Export CSV"
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "text-sm text-muted",
				children: [
					"In ",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: inn,
						symbol,
						tone: "in"
					}),
					" · Out",
					" ",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: out,
						symbol,
						tone: "out"
					}),
					" · Net",
					" ",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: inn - out,
						symbol
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-5",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					await addCash({ data: {
						entry_type: String(fd.get("entry_type") ?? "in"),
						category: String(fd.get("category") ?? ""),
						description: String(fd.get("description") ?? ""),
						amount: Number(fd.get("amount")),
						date: String(fd.get("date") || todayISO())
					} });
					form.reset();
					toast.success("Entry added");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Type",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
							name: "entry_type",
							defaultValue: "in",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "in",
								children: "Cash in"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "out",
								children: "Cash out"
							})]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Category",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "category",
							required: true,
							placeholder: "Rent, Sales…"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Description",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, { name: "description" })
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
						label: "Date",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "date",
							type: "date",
							defaultValue: todayISO()
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "sm:col-span-5",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							size: "sm",
							children: "Add entry"
						})
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Type",
					"Category",
					"Description",
					"Amount",
					"Date",
					""
				],
				empty: rows.length === 0,
				children: rows.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: r.entry_type === "in" ? "in" : "out",
						children: r.entry_type === "in" ? "In" : "Out"
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: r.category }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: r.description || "—"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: r.amount,
						symbol,
						tone: r.entry_type === "in" ? "in" : "out"
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: r.date
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: () => setEdit(r),
							children: "Edit"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								await deleteCash({ data: { id: r.id } });
								toast.success("Deleted");
								await load();
							},
							children: "Delete"
						})]
					}) })
				] }, r.id))
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
				open: !!edit,
				onOpenChange: (o) => !o && setEdit(null),
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Edit cash entry" }) }), edit ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
					className: "space-y-3",
					onSubmit: async (e) => {
						e.preventDefault();
						const fd = new FormData(e.currentTarget);
						await updateCash({ data: {
							id: edit.id,
							entry_type: String(fd.get("entry_type") ?? "in"),
							category: String(fd.get("category") ?? ""),
							description: String(fd.get("description") ?? ""),
							amount: Number(fd.get("amount")),
							date: String(fd.get("date") || todayISO())
						} });
						setEdit(null);
						toast.success("Saved");
						await load();
					},
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Type",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
								name: "entry_type",
								defaultValue: edit.entry_type,
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "in",
									children: "Cash in"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "out",
									children: "Cash out"
								})]
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Category",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "category",
								defaultValue: edit.category,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Description",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "description",
								defaultValue: edit.description
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Amount",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "amount",
								type: "number",
								step: "0.01",
								defaultValue: edit.amount,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Date",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "date",
								type: "date",
								defaultValue: edit.date,
								required: true
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							children: "Save"
						})
					]
				}) : null] })
			})
		]
	});
}
//#endregion
export { CashPage as component };
