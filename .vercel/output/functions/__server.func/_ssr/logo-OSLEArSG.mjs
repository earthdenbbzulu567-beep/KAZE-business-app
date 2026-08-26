import { t as cn } from "./utils-C_uf36nf.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/logo-OSLEArSG.js
var import_jsx_runtime = require_jsx_runtime();
function LogoMark({ className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("svg", {
		viewBox: "0 0 32 32",
		className: cn("size-8 shrink-0", className),
		"aria-hidden": "true",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
				width: "32",
				height: "32",
				rx: "8",
				className: "fill-surface-2"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
				x: "1",
				y: "1",
				width: "30",
				height: "30",
				rx: "7",
				className: "stroke-brand",
				fill: "none",
				strokeWidth: "1.5"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("path", {
				d: "M10 8.5V23.5H13.1V17.2L18.6 23.5H22.4L15.7 15.7L21.9 8.5H18.1L13.1 14.4V8.5H10Z",
				className: "fill-fg"
			})
		]
	});
}
function Logo({ className }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
		className: cn("flex items-center gap-2.5", className),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LogoMark, {}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-display text-[15px] font-medium tracking-[0.14em] uppercase",
			children: "KAZE"
		})]
	});
}
//#endregion
export { LogoMark as n, Logo as t };
