import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { t as useCurrentUser } from "./use-current-user-DG6UNzh9.mjs";
import { E as deleteTeam, G as listTeam, f as addTeam } from "./server-BeIiaNi3.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { n as toast } from "../_libs/sonner.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/team-BFpnEb7-.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function TeamPage() {
	const user = useCurrentUser();
	const [rows, setRows] = (0, import_react.useState)(null);
	async function load() {
		setRows(await listTeam());
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!rows) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Team",
				description: "A roster of people who work this desk. Each person still signs in with their own account."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					await addTeam({ data: {
						name: String(fd.get("name") ?? ""),
						email: String(fd.get("email") ?? ""),
						role: String(fd.get("role") ?? "Staff")
					} });
					form.reset();
					toast.success("Added to team");
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
						label: "Role",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "role",
							placeholder: "Staff"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						type: "submit",
						size: "sm",
						children: "Add member"
					}) })
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DataTable, {
				headers: [
					"Name",
					"Email",
					"Role",
					""
				],
				empty: false,
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: user?.displayName ?? "You" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: user?.primaryEmail ?? "—"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: "Owner" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: "—" })
				] }), rows.map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: m.name }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: m.email || "—"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: m.role }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						size: "sm",
						onClick: async () => {
							await deleteTeam({ data: { id: m.id } });
							toast.success("Removed");
							await load();
						},
						children: "Remove"
					}) })
				] }, m.id))]
			})
		]
	});
}
//#endregion
export { TeamPage as component };
