import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as LogoMark, t as Logo } from "./logo-OSLEArSG.mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { v as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { n as useCurrentUserState } from "./use-current-user-DG6UNzh9.mjs";
import { n as SignedIn, r as SignedOut } from "./gates-Di-qsd7U.mjs";
import { S as ArrowRight, c as ShoppingCart, f as Package, h as FileText, n as Wallet, y as ChartLine } from "../_libs/lucide-react.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-CQ_E_qSA.js
var import_jsx_runtime = require_jsx_runtime();
var FEATURES = [
	{
		icon: Wallet,
		title: "Income and expenses",
		body: "Log every dollar in and out, see profit at a glance, and watch the trend over time."
	},
	{
		icon: Package,
		title: "Stock and inventory",
		body: "Track quantity, cost, and selling price. Low-stock alerts fire before you run dry."
	},
	{
		icon: ShoppingCart,
		title: "Sales and customers",
		body: "Record sales against inventory, attach them to customers, and see lifetime spend."
	},
	{
		icon: FileText,
		title: "Invoices and receipts",
		body: "Create invoices, contracts, and reports. Print a clean copy whenever you need one."
	},
	{
		icon: Wallet,
		title: "Cash book",
		body: "Keep till cash separate from the income statement — categorized and dated."
	},
	{
		icon: ChartLine,
		title: "Reports and plans",
		body: "Six-month profit trend, top products, SWOT, and a living business plan."
	}
];
function Home() {
	const { isPending } = useCurrentUserState();
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "min-h-screen bg-bg text-fg",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
				className: "mx-auto flex max-w-6xl items-center justify-between px-5 py-5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Logo, {}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "flex items-center gap-2",
					children: isPending ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "h-11 w-24 animate-pulse rounded-sm bg-surface-2" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SignedOut, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/login",
							children: "Log in"
						})
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/login",
							children: "Get started"
						})
					})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SignedIn, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Link, {
							to: "/dashboard",
							children: ["Open dashboard", /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowRight, { className: "size-4" })]
						})
					}) })] })
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "relative mx-auto max-w-3xl overflow-hidden px-5 pt-16 pb-12 text-center sm:pt-24",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						"aria-hidden": true,
						className: "pointer-events-none absolute top-1/2 left-1/2 size-[28rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand/20"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						"aria-hidden": true,
						className: "pointer-events-none absolute top-1/2 left-1/2 size-[22rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand/10"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "relative kaze-enter",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LogoMark, { className: "mx-auto mb-6 size-16" }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mb-3 text-[11px] font-medium tracking-[0.22em] text-brand uppercase",
								children: "Business manager"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h1", {
								className: "font-display text-4xl leading-[1.1] font-medium tracking-tight sm:text-5xl",
								children: [
									"Run the whole business",
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("br", {}),
									"from one desk."
								]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mx-auto mt-5 max-w-lg text-base text-muted",
								children: "Stock, sales, cash, invoices, budgets, and a plan — kept together so a small trading house can see the day clearly."
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "mt-8 flex flex-wrap justify-center gap-3",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SignedOut, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
									size: "lg",
									asChild: true,
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
										to: "/login",
										children: "Create an account"
									})
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
									size: "lg",
									variant: "secondary",
									asChild: true,
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
										to: "/login",
										children: "Log in"
									})
								})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SignedIn, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
									size: "lg",
									asChild: true,
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
										to: "/dashboard",
										children: "Go to dashboard"
									})
								}) })]
							})
						]
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "mx-auto max-w-6xl px-5 pb-20",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "mb-6 font-display text-2xl tracking-tight",
					children: "Everything a trading desk needs"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "grid gap-3 sm:grid-cols-2 lg:grid-cols-3",
					children: FEATURES.map((f, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("article", {
						className: "kaze-enter rounded-xl bg-surface p-6 shadow-[var(--kaze-shadow)] transition-[box-shadow,transform] duration-[var(--motion-fast)] hover:shadow-[var(--kaze-shadow-hover)]",
						style: { animationDelay: `${i * 40}ms` },
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(f.icon, {
								className: "mb-4 size-5 text-brand",
								strokeWidth: 1.75
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
								className: "font-medium text-fg",
								children: f.title
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "mt-1.5 text-sm text-muted",
								children: f.body
							})
						]
					}, f.title))
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("section", {
				className: "mx-auto mb-20 max-w-6xl px-5",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "rounded-2xl bg-surface px-6 py-12 text-center shadow-[var(--kaze-shadow)] sm:px-12",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
							className: "font-display text-3xl tracking-tight",
							children: "Ready to get organized?"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-2 text-muted",
							children: "Set up the books in a couple of minutes."
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "mt-6",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								asChild: true,
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Link, {
									to: "/login",
									children: ["Open KAZE Traders", /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowRight, { className: "size-4" })]
								})
							})
						})
					]
				})
			})
		]
	});
}
//#endregion
export { Home as component };
