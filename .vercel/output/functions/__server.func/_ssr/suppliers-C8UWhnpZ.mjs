import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { v as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { U as listSuppliers, u as addSupplier, w as deleteSupplier } from "./server-BeIiaNi3.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { n as toast } from "../_libs/sonner.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/suppliers-C8UWhnpZ.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function SuppliersPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	async function load() {
		setRows(await listSuppliers());
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!rows) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Suppliers",
				description: "Vendors you buy stock from.",
				actions: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					asChild: true,
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
						to: "/orders",
						children: "Purchase orders"
					})
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-2",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					await addSupplier({ data: {
						name: String(fd.get("name") ?? ""),
						email: String(fd.get("email") ?? ""),
						phone: String(fd.get("phone") ?? ""),
						address: String(fd.get("address") ?? ""),
						notes: ""
					} });
					form.reset();
					toast.success("Supplier saved");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Name",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "name",
							required: true
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
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						type: "submit",
						size: "sm",
						children: "Save supplier"
					}) })
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Name",
					"Email",
					"Phone",
					"Address",
					""
				],
				empty: rows.length === 0,
				children: rows.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: s.name }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: s.email || "—"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: s.phone || "—" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: s.address || "—" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						size: "sm",
						onClick: async () => {
							await deleteSupplier({ data: { id: s.id } });
							toast.success("Deleted");
							await load();
						},
						children: "Delete"
					}) })
				] }, s.id))
			})
		]
	});
}
//#endregion
export { SuppliersPage as component };
