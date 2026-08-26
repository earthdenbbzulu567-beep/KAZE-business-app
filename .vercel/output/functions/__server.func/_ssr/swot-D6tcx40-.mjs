import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { T as deleteSwot, W as listSwot, d as addSwot } from "./server-BeIiaNi3.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Card } from "./card-CyLphHyC.mjs";
import { s as printHtml } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Textarea } from "./textarea-B7g5K7Zm.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/swot-D6tcx40-.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function SwotPage() {
	const [rows, setRows] = (0, import_react.useState)(null);
	async function load() {
		setRows(await listSwot());
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (!rows) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: "SWOT analysis",
				description: "Strengths, weaknesses, opportunities, and threats — saved over time."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
				className: "space-y-4 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]",
				onSubmit: async (e) => {
					e.preventDefault();
					const form = e.currentTarget;
					const fd = new FormData(form);
					await addSwot({ data: {
						title: String(fd.get("title") ?? ""),
						strengths: String(fd.get("strengths") ?? ""),
						weaknesses: String(fd.get("weaknesses") ?? ""),
						opportunities: String(fd.get("opportunities") ?? ""),
						threats: String(fd.get("threats") ?? "")
					} });
					form.reset();
					toast.success("Analysis saved");
					await load();
				},
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
						label: "Title",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
							name: "title",
							placeholder: "Q3 strategy review",
							className: "max-w-md"
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid gap-3 sm:grid-cols-2",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "rounded-lg bg-in/10 p-4",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Strengths",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
										name: "strengths",
										rows: 5,
										placeholder: "What you do well"
									})
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "rounded-lg bg-warn/10 p-4",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Weaknesses",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
										name: "weaknesses",
										rows: 5,
										placeholder: "Where you could improve"
									})
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "rounded-lg bg-brand/10 p-4",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Opportunities",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
										name: "opportunities",
										rows: 5,
										placeholder: "Trends or gaps"
									})
								})
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "rounded-lg bg-out/10 p-4",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Threats",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
										name: "threats",
										rows: 5,
										placeholder: "What could hurt the business"
									})
								})
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						type: "submit",
						size: "sm",
						children: "Save analysis"
					})
				]
			}),
			rows.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-sm text-muted",
				children: "No analyses yet."
			}) : rows.map((a) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "space-y-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex flex-wrap items-center justify-between gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
						className: "font-display text-lg",
						children: a.title
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-xs text-subtle",
						children: a.created_date
					})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex gap-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: () => printHtml(a.title, `<h1>${a.title}</h1><p class="muted">${a.created_date}</p>
                       <h3>Strengths</h3><pre>${a.strengths}</pre>
                       <h3>Weaknesses</h3><pre>${a.weaknesses}</pre>
                       <h3>Opportunities</h3><pre>${a.opportunities}</pre>
                       <h3>Threats</h3><pre>${a.threats}</pre>`),
							children: "Print"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: async () => {
								await deleteSwot({ data: { id: a.id } });
								toast.success("Deleted");
								await load();
							},
							children: "Delete"
						})]
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "grid gap-3 sm:grid-cols-2",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md bg-in/10 p-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs font-medium text-in",
								children: "Strengths"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1 whitespace-pre-wrap text-sm",
								children: a.strengths || "—"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md bg-warn/10 p-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs font-medium text-warn",
								children: "Weaknesses"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1 whitespace-pre-wrap text-sm",
								children: a.weaknesses || "—"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md bg-brand/10 p-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs font-medium text-brand",
								children: "Opportunities"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1 whitespace-pre-wrap text-sm",
								children: a.opportunities || "—"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md bg-out/10 p-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs font-medium text-out",
								children: "Threats"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1 whitespace-pre-wrap text-sm",
								children: a.threats || "—"
							})]
						})
					]
				})]
			}, a.id))
		]
	});
}
//#endregion
export { SwotPage as component };
