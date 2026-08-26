import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { A as getPlan, M as getSettings, Y as savePlan } from "./server-BeIiaNi3.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { s as printHtml } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Textarea } from "./textarea-B7g5K7Zm.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/plan-C_y-Yic9.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var SECTIONS = [
	{
		key: "mission",
		label: "Mission",
		hint: "Why the business exists."
	},
	{
		key: "products_services",
		label: "Products / services",
		hint: "What you sell, and why it is different."
	},
	{
		key: "target_market",
		label: "Target market",
		hint: "Who the ideal buyer is."
	},
	{
		key: "marketing_strategy",
		label: "Marketing",
		hint: "How people find you."
	},
	{
		key: "operations_plan",
		label: "Operations",
		hint: "How the day actually runs."
	},
	{
		key: "financial_plan",
		label: "Financial plan",
		hint: "Costs, pricing, funding."
	},
	{
		key: "goals",
		label: "Goals",
		hint: "What success looks like in 6 months, a year, three years."
	}
];
function PlanPage() {
	const [plan, setPlan] = (0, import_react.useState)(void 0);
	const [biz, setBiz] = (0, import_react.useState)("");
	(0, import_react.useEffect)(() => {
		(async () => {
			const [p, s] = await Promise.all([getPlan(), getSettings()]);
			setPlan(p);
			setBiz(s.business_name);
		})();
	}, []);
	if (plan === void 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "Business plan",
				description: "A living document. Save whenever the strategy shifts.",
				actions: plan ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					onClick: () => printHtml("Business plan", `<h1>${plan.business_name || biz || "Business plan"}</h1>
                   <p class="muted">Updated ${plan.updated_date ?? "—"}</p>
                   ${SECTIONS.map((s) => `<h3>${s.label}</h3><pre>${String(plan[s.key] ?? "")}</pre>`).join("")}`),
					children: "Print"
				}) : null
			}),
			plan?.updated_date ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "text-xs text-subtle",
				children: ["Last updated ", plan.updated_date]
			}) : null,
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "space-y-5",
				onSubmit: async (e) => {
					e.preventDefault();
					const fd = new FormData(e.currentTarget);
					const payload = {
						business_name: String(fd.get("business_name") ?? ""),
						mission: String(fd.get("mission") ?? ""),
						products_services: String(fd.get("products_services") ?? ""),
						target_market: String(fd.get("target_market") ?? ""),
						marketing_strategy: String(fd.get("marketing_strategy") ?? ""),
						operations_plan: String(fd.get("operations_plan") ?? ""),
						financial_plan: String(fd.get("financial_plan") ?? ""),
						goals: String(fd.get("goals") ?? "")
					};
					await savePlan({ data: payload });
					toast.success("Plan saved");
					setPlan({
						...payload,
						updated_date: (/* @__PURE__ */ new Date()).toISOString().slice(0, 10)
					});
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Business name",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "business_name",
							defaultValue: plan?.business_name || biz,
							className: "max-w-md"
						})
					}),
					SECTIONS.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Field, {
						label: s.label,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-xs text-subtle",
							children: s.hint
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
							name: s.key,
							rows: 3,
							defaultValue: String(plan?.[s.key] ?? "")
						})]
					}, s.key)),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						type: "submit",
						children: "Save plan"
					})
				]
			})
		]
	});
}
//#endregion
export { PlanPage as component };
