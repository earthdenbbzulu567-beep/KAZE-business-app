import { t as cn } from "./utils-C_uf36nf.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/badge-TfmHgfhb.js
var import_jsx_runtime = require_jsx_runtime();
function Badge({ className, tone = "neutral", ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
		className: cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium tracking-wide", {
			neutral: "bg-surface-2 text-muted",
			in: "bg-in/15 text-in",
			out: "bg-out/15 text-out",
			warn: "bg-warn/15 text-warn",
			brand: "bg-brand/15 text-brand"
		}[tone], className),
		...props
	});
}
//#endregion
export { Badge as t };
