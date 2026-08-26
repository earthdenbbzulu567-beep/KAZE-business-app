import { o as __toESM } from "../_runtime.mjs";
import { t as cn } from "./utils-C_uf36nf.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/select-BNz9F6zf.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var Select = (0, import_react.forwardRef)(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
	ref,
	className: cn("flex h-11 w-full appearance-none rounded-md bg-surface-2 bg-[length:12px] bg-[right_12px_center] bg-no-repeat px-3 pr-9 text-sm text-fg shadow-[var(--kaze-shadow)] transition-[box-shadow] duration-[var(--motion-quick)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/70 disabled:cursor-not-allowed disabled:opacity-50", className),
	style: { backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' fill='none'><path d='M1 1.5 6 6.5 11 1.5' stroke='%238b928b' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/></svg>")` },
	...props,
	children
}));
Select.displayName = "Select";
//#endregion
export { Select as t };
