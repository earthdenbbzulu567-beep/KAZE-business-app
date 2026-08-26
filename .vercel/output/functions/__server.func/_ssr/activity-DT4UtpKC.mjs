import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { N as listActivity } from "./server-BeIiaNi3.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { n as CardTitle, t as Card } from "./card-CyLphHyC.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/activity-DT4UtpKC.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function ActivityPage() {
	const [data, setData] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		listActivity().then(setData);
	}, []);
	if (!data) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Login activity",
				description: "Recent sign-ins on this account."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "max-w-xs",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, { children: "Logins today" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-3 font-display text-3xl tabular",
					children: data.todayCount
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: ["Name", "Time"],
				empty: data.logs.length === 0,
				children: data.logs.map((l) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: l.username }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
					className: "text-muted",
					children: l.login_time
				})] }, l.id))
			})
		]
	});
}
//#endregion
export { ActivityPage as component };
