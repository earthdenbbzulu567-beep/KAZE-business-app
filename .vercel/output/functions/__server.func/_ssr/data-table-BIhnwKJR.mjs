import { t as cn } from "./utils-C_uf36nf.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/data-table-BIhnwKJR.js
var import_jsx_runtime = require_jsx_runtime();
function DataTable({ headers, children, empty, colSpan }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "overflow-x-auto rounded-xl bg-surface shadow-[var(--kaze-shadow)]",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
			className: "w-full min-w-[36rem] text-left text-sm",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tr", {
				className: "border-b border-border",
				children: headers.map((h) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
					className: "px-4 py-3 text-[11px] font-medium tracking-[0.12em] text-subtle uppercase",
					children: h
				}, h))
			}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", {
				className: "[&_tr:last-child_td]:border-b-0",
				children: empty ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tr", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
					colSpan: colSpan ?? headers.length,
					className: "px-4 py-10 text-center text-sm text-muted",
					children: "Nothing here yet."
				}) }) : children
			})]
		})
	});
}
function Td({ className, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
		className: cn("border-b border-border px-4 py-3 text-fg", className),
		children
	});
}
function Tr({ children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tr", {
		className: "transition-colors duration-[var(--motion-quick)] hover:bg-surface-2/60",
		children
	});
}
//#endregion
export { Td as n, Tr as r, DataTable as t };
