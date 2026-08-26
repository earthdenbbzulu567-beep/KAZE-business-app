import { o as __toESM } from "../_runtime.mjs";
import { t as cn } from "./utils-C_uf36nf.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { L as listDocuments, M as getSettings, O as generateDocumentCopy, _ as deleteDocument, r as addDocument } from "./server-BeIiaNi3.mjs";
import { n as Money } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { c as todayISO, i as money, s as printHtml } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Badge } from "./badge-TfmHgfhb.mjs";
import { t as Textarea } from "./textarea-B7g5K7Zm.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/documents-pH5882PY.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function DocumentsPage() {
	const [docs, setDocs] = (0, import_react.useState)(null);
	const [settings, setSettings] = (0, import_react.useState)(null);
	const [filter, setFilter] = (0, import_react.useState)("all");
	const [ai, setAi] = (0, import_react.useState)(null);
	const [aiBusy, setAiBusy] = (0, import_react.useState)(false);
	async function load() {
		const [s, list] = await Promise.all([getSettings(), listDocuments()]);
		setSettings(s);
		setDocs(list);
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!docs || !settings) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	const symbol = settings.currency_symbol;
	const shown = filter === "all" ? docs : docs.filter((d) => d.doc_type === filter);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Documents",
				description: "Invoices, contracts, and reports — print a clean copy any time."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "flex flex-wrap gap-2",
				children: [
					"all",
					"invoice",
					"contract",
					"report"
				].map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					size: "sm",
					variant: filter === t ? "default" : "secondary",
					onClick: () => setFilter(t),
					className: cn("capitalize"),
					children: t === "all" ? "All" : t
				}, t))
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "space-y-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					const amountRaw = String(fd.get("amount") ?? "");
					await addDocument({ data: {
						doc_type: String(fd.get("doc_type") ?? "invoice"),
						title: String(fd.get("title") ?? ""),
						client: String(fd.get("client") ?? ""),
						amount: amountRaw ? Number(amountRaw) : null,
						date: String(fd.get("date") || todayISO()),
						notes: String(fd.get("notes") ?? "")
					} });
					form.reset();
					toast.success("Document saved");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-3 sm:grid-cols-2",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Type",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									name: "doc_type",
									defaultValue: "invoice",
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "invoice",
											children: "Invoice"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "contract",
											children: "Contract"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "report",
											children: "Report"
										})
									]
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
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Title",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									name: "title",
									required: true,
									placeholder: "Invoice 1042 — Acme"
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Client",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									name: "client",
									required: true
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Amount (optional)",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									name: "amount",
									type: "number",
									step: "0.01"
								})
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Notes",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
							name: "notes",
							rows: 3,
							placeholder: "Scope, terms, details…"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex flex-wrap gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							size: "sm",
							children: "Save document"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "button",
							variant: "secondary",
							size: "sm",
							disabled: aiBusy,
							onClick: async (e) => {
								const form = e.currentTarget.form;
								if (!form) return;
								const fd = new FormData(form);
								setAiBusy(true);
								setAi("Generating…");
								try {
									const amountRaw = String(fd.get("amount") ?? "");
									const r = await generateDocumentCopy({ data: {
										doc_type: String(fd.get("doc_type") ?? "invoice"),
										title: String(fd.get("title") ?? ""),
										client: String(fd.get("client") ?? ""),
										amount: amountRaw ? Number(amountRaw) : null,
										notes: String(fd.get("notes") ?? ""),
										business_name: settings.business_name
									} });
									if (!r.ok) {
										setAi(r.error);
										toast.error(r.error);
									} else {
										setAi(r.text);
										const notes = form.elements.namedItem("notes");
										if (notes && r.text) notes.value = r.text;
									}
								} finally {
									setAiBusy(false);
								}
							},
							children: aiBusy ? "Generating…" : "Draft with AI"
						})]
					}),
					ai ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("pre", {
						className: "max-h-48 overflow-auto rounded-md bg-surface-2 p-3 text-xs whitespace-pre-wrap text-muted",
						children: ai
					}) : null
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Type",
					"Title",
					"Client",
					"Amount",
					"Date",
					""
				],
				empty: shown.length === 0,
				children: shown.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
						tone: d.doc_type === "invoice" ? "in" : d.doc_type === "contract" ? "brand" : "neutral",
						children: d.doc_type
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "font-medium",
						children: d.title
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: d.client }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: d.amount != null ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: d.amount,
						symbol
					}) : "—" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: d.date
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: () => {
								const tax = d.amount != null && settings.tax_rate ? d.amount * settings.tax_rate / 100 : 0;
								printHtml(d.title, `<h1>${settings.business_name || "KAZE Traders"}</h1>
                       <p class="muted">${d.doc_type.toUpperCase()} · ${d.date}</p>
                       <h2>${d.title}</h2>
                       <p>Client: ${d.client}</p>
                       ${d.amount != null ? `<p>Amount: ${money(d.amount, symbol)}</p>` : ""}
                       ${tax ? `<p>Tax (${settings.tax_rate}%): ${money(tax, symbol)}</p><p class="total">Total ${money(d.amount + tax, symbol)}</p>` : ""}
                       <pre>${d.notes || ""}</pre>`);
							},
							children: "Print"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								if (!confirm("Delete this document?")) return;
								await deleteDocument({ data: { id: d.id } });
								toast.success("Deleted");
								await load();
							},
							children: "Delete"
						})]
					}) })
				] }, d.id))
			})
		]
	});
}
//#endregion
export { DocumentsPage as component };
