import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { M as getSettings, X as saveSettings } from "./server-BeIiaNi3.mjs";
import { n as Field, r as PageHeader } from "./page-header-DtL_JkzF.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { t as Textarea } from "./textarea-B7g5K7Zm.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/settings-B_25fQr1.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function SettingsPage() {
	const [s, setS] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		getSettings().then(setS);
	}, []);
	if (!s) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: "Settings",
			description: "Business details, appearance, and dashboard widgets."
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
			className: "max-w-xl space-y-6",
			onSubmit: async (e) => {
				e.preventDefault();
				const fd = new FormData(e.currentTarget);
				const next = await saveSettings({ data: {
					business_name: String(fd.get("business_name") ?? ""),
					currency_code: String(fd.get("currency_code") ?? "USD"),
					currency_symbol: String(fd.get("currency_symbol") ?? "$"),
					tax_rate: Number(fd.get("tax_rate") || 0),
					monthly_revenue_goal: Number(fd.get("monthly_revenue_goal") || 0),
					low_stock_threshold: Number(fd.get("low_stock_threshold") || 10),
					theme: String(fd.get("theme") ?? "dark"),
					font_size: String(fd.get("font_size") ?? "medium"),
					default_chart_type: String(fd.get("default_chart_type") ?? "line"),
					animations_enabled: fd.get("animations_enabled") === "on",
					show_low_stock_widget: fd.get("show_low_stock_widget") === "on",
					show_sales_trend: fd.get("show_sales_trend") === "on",
					about_text: String(fd.get("about_text") ?? "")
				} });
				setS(next);
				document.documentElement.dataset.theme = next.theme === "light" ? "light" : "dark";
				document.documentElement.dataset.density = next.font_size;
				toast.success("Settings saved");
			},
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
					className: "space-y-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
							className: "text-xs font-medium tracking-[0.14em] text-subtle uppercase",
							children: "Business"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Business name (on receipts)",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "business_name",
								defaultValue: s.business_name
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-2 gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Currency",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									name: "currency_code",
									defaultValue: s.currency_code,
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "USD",
											children: "USD"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "ZMW",
											children: "ZMW"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "EUR",
											children: "EUR"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "GBP",
											children: "GBP"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "ZAR",
											children: "ZAR"
										})
									]
								})
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
								label: "Symbol",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									name: "currency_symbol",
									defaultValue: s.currency_symbol,
									maxLength: 4
								})
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Tax / VAT rate (%)",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "tax_rate",
								type: "number",
								step: "0.01",
								defaultValue: s.tax_rate
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Monthly revenue goal",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "monthly_revenue_goal",
								type: "number",
								step: "0.01",
								defaultValue: s.monthly_revenue_goal
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Low stock threshold",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
								name: "low_stock_threshold",
								type: "number",
								step: "1",
								defaultValue: s.low_stock_threshold
							})
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
					className: "space-y-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
							className: "text-xs font-medium tracking-[0.14em] text-subtle uppercase",
							children: "Appearance"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Theme",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
								name: "theme",
								defaultValue: s.theme,
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "dark",
									children: "Dark"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "light",
									children: "Light"
								})]
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Text size",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
								name: "font_size",
								defaultValue: s.font_size,
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
										value: "small",
										children: "Small"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
										value: "medium",
										children: "Medium"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
										value: "large",
										children: "Large"
									})
								]
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "Default chart",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
								name: "default_chart_type",
								defaultValue: s.default_chart_type,
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "line",
									children: "Line"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
									value: "bar",
									children: "Bar"
								})]
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
							className: "flex h-11 items-center gap-2 text-sm",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "checkbox",
								name: "animations_enabled",
								defaultChecked: s.animations_enabled,
								className: "size-4 accent-brand"
							}), "Motion"]
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
					className: "space-y-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
							className: "text-xs font-medium tracking-[0.14em] text-subtle uppercase",
							children: "Dashboard"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
							className: "flex h-11 items-center gap-2 text-sm",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "checkbox",
								name: "show_low_stock_widget",
								defaultChecked: s.show_low_stock_widget,
								className: "size-4 accent-brand"
							}), "Show low stock"]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
							className: "flex h-11 items-center gap-2 text-sm",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "checkbox",
								name: "show_sales_trend",
								defaultChecked: s.show_sales_trend,
								className: "size-4 accent-brand"
							}), "Show sales trend"]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
							label: "About",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
								name: "about_text",
								rows: 3,
								defaultValue: s.about_text
							})
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					type: "submit",
					children: "Save settings"
				})
			]
		})]
	});
}
//#endregion
export { SettingsPage as component };
