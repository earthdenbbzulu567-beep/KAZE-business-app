import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { R as listNotifications, p as clearNotifications } from "./server-BeIiaNi3.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Badge } from "./badge-TfmHgfhb.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/notifications-CfWY9pue.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function NotificationsPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	async function load() {
		setRows(await listNotifications());
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!rows) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: "Alerts",
			description: "Low stock, recurring items, purchase orders, and other notices.",
			actions: rows.length ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				variant: "secondary",
				size: "sm",
				onClick: async () => {
					await clearNotifications();
					toast.success("Cleared");
					await load();
				},
				children: "Clear all"
			}) : null
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
			headers: [
				"Message",
				"Category",
				"When"
			],
			empty: rows.length === 0,
			children: rows.map((n) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: n.message }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, { children: n.category }) }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
					className: "text-muted",
					children: n.created_date
				})
			] }, n.id))
		})]
	});
}
//#endregion
export { NotificationsPage as component };
