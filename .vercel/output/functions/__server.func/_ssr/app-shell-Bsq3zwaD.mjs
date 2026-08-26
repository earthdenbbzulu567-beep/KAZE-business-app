import { o as __toESM } from "../_runtime.mjs";
import { t as cn } from "./utils-C_uf36nf.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { t as Logo } from "./logo-OSLEArSG.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { a as DialogPortal, i as DialogOverlay, n as DialogClose, r as DialogContent, t as Dialog } from "../_libs/@radix-ui/react-dialog+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { d as useRouterState, m as Outlet, v as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { n as useCurrentUserState, t as useCurrentUser } from "./use-current-user-DG6UNzh9.mjs";
import { i as UserButton, t as RedirectToSignIn } from "./gates-Di-qsd7U.mjs";
import { $ as unreadCount, M as getSettings, q as recordActivity } from "./server-BeIiaNi3.mjs";
import { _ as Clock, a as Truck, b as BookOpen, c as ShoppingCart, d as Repeat, f as Package, g as Compass, h as FileText, i as UserRound, l as Settings, m as LayoutDashboard, n as Wallet, p as Menu, r as Users, s as Target, t as X, u as ScrollText, v as ClipboardList, x as Bell, y as ChartLine } from "../_libs/lucide-react.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/app-shell-Bsq3zwaD.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var Sheet = Dialog;
function SheetContent({ className, children, side = "left", ...props }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogPortal, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogOverlay, { className: "fixed inset-0 z-50 bg-bg/70" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
		className: cn("fixed z-50 flex h-full w-[min(20rem,88vw)] flex-col bg-bg-elevated p-4 shadow-[var(--kaze-shadow-hover)] focus:outline-none", side === "left" ? "inset-y-0 left-0" : "inset-y-0 right-0", className),
		...props,
		children: [children, /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogClose, {
			className: "absolute top-3 right-3 rounded-sm p-1 text-muted hover:text-fg",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "size-4" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
				className: "sr-only",
				children: "Close"
			})]
		})]
	})] });
}
var GROUPS = [
	{
		label: "Overview",
		items: [{
			to: "/dashboard",
			label: "Dashboard",
			icon: LayoutDashboard
		}, {
			to: "/reports",
			label: "Reports",
			icon: ChartLine
		}]
	},
	{
		label: "Trade",
		items: [
			{
				to: "/stock",
				label: "Stock",
				icon: Package
			},
			{
				to: "/sales",
				label: "Sales",
				icon: ShoppingCart
			},
			{
				to: "/customers",
				label: "Customers",
				icon: Users
			}
		]
	},
	{
		label: "Money",
		items: [
			{
				to: "/cashbook",
				label: "Cash book",
				icon: Wallet
			},
			{
				to: "/budgets",
				label: "Budgets",
				icon: Target
			},
			{
				to: "/recurring",
				label: "Recurring",
				icon: Repeat
			}
		]
	},
	{
		label: "Operations",
		items: [
			{
				to: "/documents",
				label: "Documents",
				icon: FileText
			},
			{
				to: "/suppliers",
				label: "Suppliers",
				icon: Truck
			},
			{
				to: "/orders",
				label: "Purchase orders",
				icon: ClipboardList
			}
		]
	},
	{
		label: "Strategy",
		items: [{
			to: "/swot",
			label: "SWOT",
			icon: Compass
		}, {
			to: "/plan",
			label: "Business plan",
			icon: ScrollText
		}]
	}
];
var ACCOUNT = [
	{
		to: "/notifications",
		label: "Alerts",
		icon: Bell
	},
	{
		to: "/team",
		label: "Team",
		icon: UserRound
	},
	{
		to: "/activity",
		label: "Activity",
		icon: Clock
	},
	{
		to: "/help",
		label: "Guide",
		icon: BookOpen
	},
	{
		to: "/settings",
		label: "Settings",
		icon: Settings
	}
];
function NavLink({ item, active, onClick, badge }) {
	const Icon = item.icon;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Link, {
		to: item.to,
		onClick,
		className: cn("flex h-10 items-center gap-2.5 rounded-md px-2.5 text-sm transition-colors duration-[var(--motion-quick)]", active ? "bg-surface-2 text-fg" : "text-muted hover:bg-surface/80 hover:text-fg"),
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Icon, {
				className: "size-4 shrink-0",
				strokeWidth: 1.75
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
				className: "flex-1 truncate",
				children: item.label
			}),
			badge ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
				className: "grid min-w-5 place-items-center rounded-full bg-out/20 px-1.5 text-[10px] font-medium text-out",
				children: badge
			}) : null
		]
	});
}
function SideNav({ pathname, unread, onNavigate }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex h-full flex-col",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
				to: "/dashboard",
				onClick: onNavigate,
				className: "mb-6 flex items-center px-1 pt-1",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Logo, {})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("nav", {
				className: "flex-1 space-y-5 overflow-y-auto pr-1",
				children: [GROUPS.map((g) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mb-1.5 px-2.5 text-[10px] font-medium tracking-[0.16em] text-subtle uppercase",
					children: g.label
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "space-y-0.5",
					children: g.items.map((item) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NavLink, {
						item,
						active: pathname === item.to,
						onClick: onNavigate
					}, item.to))
				})] }, g.label)), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mb-1.5 px-2.5 text-[10px] font-medium tracking-[0.16em] text-subtle uppercase",
					children: "Account"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "space-y-0.5",
					children: ACCOUNT.map((item) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NavLink, {
						item,
						active: pathname === item.to,
						onClick: onNavigate,
						badge: item.to === "/notifications" ? unread : void 0
					}, item.to))
				})] })]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-4 border-t border-border pt-3",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(UserButton, {})
			})
		]
	});
}
function AppShell() {
	const { user, isPending } = useCurrentUserState();
	const current = useCurrentUser();
	const pathname = useRouterState({ select: (s) => s.location.pathname });
	const [settings, setSettings] = (0, import_react.useState)(null);
	const [unread, setUnread] = (0, import_react.useState)(0);
	const [open, setOpen] = (0, import_react.useState)(false);
	(0, import_react.useEffect)(() => {
		if (!user) return;
		let cancelled = false;
		(async () => {
			try {
				const [s, n] = await Promise.all([getSettings(), unreadCount()]);
				if (!cancelled) {
					setSettings(s);
					setUnread(n);
				}
			} catch {}
		})();
		return () => {
			cancelled = true;
		};
	}, [user, pathname]);
	(0, import_react.useEffect)(() => {
		if (!user) return;
		const key = `kaze-login-${user.id}`;
		if (sessionStorage.getItem(key)) return;
		sessionStorage.setItem(key, "1");
		recordActivity({ data: { username: user.displayName ?? user.primaryEmail ?? "User" } }).catch(() => {});
	}, [user]);
	(0, import_react.useEffect)(() => {
		if (!settings) return;
		document.documentElement.dataset.theme = settings.theme === "light" ? "light" : "dark";
		document.documentElement.dataset.density = settings.font_size || "medium";
		if (!settings.animations_enabled) document.documentElement.dataset.motion = "off";
		else delete document.documentElement.dataset.motion;
	}, [settings]);
	if (isPending) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex min-h-screen bg-bg",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("aside", {
			className: "hidden w-60 shrink-0 border-r border-border p-4 md:block",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "mb-6 h-8 w-28" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "space-y-2",
				children: Array.from({ length: 8 }).map((_, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-10 w-full" }, i))
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex-1 p-8",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "mb-4 h-8 w-48" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-40 w-full" })]
		})]
	});
	if (!user) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RedirectToSignIn, {});
	const title = settings?.business_name?.trim() || current?.displayName || "KAZE Traders";
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex min-h-screen bg-bg text-fg",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("aside", {
			className: "sticky top-0 hidden h-screen w-60 shrink-0 border-r border-border bg-bg-elevated p-4 md:block",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SideNav, {
				pathname,
				unread
			})
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex min-w-0 flex-1 flex-col",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
					className: "sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-bg/90 px-4 backdrop-blur-sm md:hidden",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "icon",
							onClick: () => setOpen(true),
							"aria-label": "Open menu",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Menu, { className: "size-5" })
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Logo, {}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "ml-auto truncate text-xs text-muted",
							children: title
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Sheet, {
					open,
					onOpenChange: setOpen,
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SheetContent, {
						side: "left",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SideNav, {
							pathname,
							unread,
							onNavigate: () => setOpen(false)
						})
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("main", {
					className: "mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:px-8",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Outlet, {})
				})
			]
		})]
	});
}
function Money({ amount, symbol = "$", tone }) {
	const abs = Math.abs(amount).toLocaleString("en-US", {
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	});
	const text = amount < 0 ? `-${symbol}${abs}` : `${symbol}${abs}`;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
		className: cn("tabular font-medium", tone === "in" ? "text-in" : tone === "out" ? "text-out" : amount < 0 ? "text-out" : "text-fg"),
		children: text
	});
}
function SectionLabel({ children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h2", {
		className: "mb-3 flex items-center gap-2 text-xs font-medium tracking-[0.14em] text-subtle uppercase",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "inline-block h-3 w-0.5 rounded-full bg-brand" }), children]
	});
}
//#endregion
export { Money as n, SectionLabel as r, AppShell as t };
