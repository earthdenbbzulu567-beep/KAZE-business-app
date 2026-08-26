import { o as __toESM } from "../_runtime.mjs";
import { n as require_jsx_runtime } from "../_libs/radix-ui__react-context+react.mjs";
import { n as require_react } from "../_libs/@radix-ui/react-compose-refs+[...].mjs";
import { t as Button } from "./button-Dv40PwMJ.mjs";
import { t as Skeleton } from "./skeleton-BKKGM19s.mjs";
import { v as Link } from "../_libs/@tanstack/react-router+[...].mjs";
import { t as useCurrentUser } from "./use-current-user-DG6UNzh9.mjs";
import { D as dismissTutorial, Z as seedSample, a as addIncome, i as addExpense, k as getDashboard, v as deleteExpense, y as deleteIncome } from "./server-BeIiaNi3.mjs";
import { n as Money, r as SectionLabel } from "./app-shell-Bsq3zwaD.mjs";
import { n as Td, r as Tr, t as DataTable } from "./data-table-BIhnwKJR.mjs";
import { n as Field, r as PageHeader, t as EmptyState } from "./page-header-DtL_JkzF.mjs";
import { n as CardTitle, t as Card } from "./card-CyLphHyC.mjs";
import { c as todayISO, r as downloadCsv, t as EXPENSE_CATEGORIES } from "./format-DhlBBqua.mjs";
import { t as Input } from "./input-Cb96lfug.mjs";
import { t as Select } from "./select-BNz9F6zf.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { a as XAxis, c as CartesianGrid, d as Tooltip, i as YAxis, n as AreaChart, o as Area, u as ResponsiveContainer } from "../_libs/recharts+[...].mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/dashboard-BIKbe84m.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function DashboardPage() {
	const user = useCurrentUser();
	const [data, setData] = (0, import_react.useState)(null);
	const [error, setError] = (0, import_react.useState)(null);
	const [busy, setBusy] = (0, import_react.useState)(false);
	async function load() {
		try {
			setData(await getDashboard());
			setError(null);
		} catch (e) {
			setError(e instanceof Error ? e.message : "Could not load dashboard");
		}
	}
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	if (error) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: "Could not load",
		description: error,
		action: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
			variant: "secondary",
			onClick: () => void load(),
			children: "Try again"
		})
	});
	if (!data) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-10 w-64" }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-3 sm:grid-cols-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-28" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-28" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-28" })
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Skeleton, { className: "h-64" })
		]
	});
	const symbol = data.settings.currency_symbol || "$";
	const chartData = [.../* @__PURE__ */ new Set([...Object.keys(data.incomeByDate), ...Object.keys(data.expenseByDate)])].sort().map((d) => ({
		date: d.slice(5),
		income: data.incomeByDate[d] ?? 0,
		expenses: data.expenseByDate[d] ?? 0
	}));
	async function onSeed() {
		setBusy(true);
		try {
			const r = await seedSample();
			toast.success(r.seeded ? "Sample data loaded" : "You already have stock — sample skipped");
			await load();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Could not load sample");
		} finally {
			setBusy(false);
		}
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "kaze-enter space-y-8",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
				title: `${user?.displayName?.split(" ")[0] ?? "Your"} desk`,
				description: "Income, expenses, and the pulse of the last few days.",
				actions: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					onClick: () => downloadCsv("income.csv", [
						"Source",
						"Amount",
						"Date"
					], data.income.map((i) => [
						i.source,
						String(i.amount),
						i.date
					])),
					children: "Income CSV"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "secondary",
					size: "sm",
					onClick: () => downloadCsv("expenses.csv", [
						"Name",
						"Amount",
						"Category",
						"Date"
					], data.expenses.map((e) => [
						e.name,
						String(e.amount),
						e.category,
						e.date
					])),
					children: "Expenses CSV"
				})] })
			}),
			!data.settings.tutorial_completed ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "flex flex-wrap items-center justify-between gap-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-medium",
					children: "New here?"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm text-muted",
					children: "A short tour of where everything lives."
				})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						asChild: true,
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/help",
							children: "Take the tour"
						})
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "secondary",
						onClick: () => {
							dismissTutorial();
							setData({
								...data,
								settings: {
									...data.settings,
									tutorial_completed: true
								}
							});
						},
						children: "Dismiss"
					})]
				})]
			}) : null,
			data.income.length === 0 && data.expenses.length === 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "flex flex-wrap items-center justify-between gap-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-medium",
					children: "Start with a sample shop"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm text-muted",
					children: "Loads stock, customers, sales, and a couple of ledger lines so you can click around."
				})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					onClick: () => void onSeed(),
					disabled: busy,
					children: busy ? "Loading…" : "Load sample data"
				})]
			}) : null,
			data.settings.monthly_revenue_goal > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, { children: "Monthly revenue goal" }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-3 flex justify-between text-sm text-muted",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
							amount: data.monthRevenue,
							symbol
						}),
						" of",
						" ",
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
							amount: data.settings.monthly_revenue_goal,
							symbol
						})
					] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "tabular",
						children: [data.goalProgressPct, "%"]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-2 h-2.5 overflow-hidden rounded-full bg-surface-2",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "h-full rounded-full bg-brand transition-[width] duration-[var(--motion-slow)]",
						style: { width: `${data.goalProgressPct}%` }
					})
				})
			] }) : null,
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-3 sm:grid-cols-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, { children: "Total income" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-3 font-display text-3xl tracking-tight text-in",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
							amount: data.totalIncome,
							symbol,
							tone: "in"
						})
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, { children: "Total expenses" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-3 font-display text-3xl tracking-tight text-out",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
							amount: data.totalExpenses,
							symbol,
							tone: "out"
						})
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, { children: "Profit / loss" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: `mt-3 font-display text-3xl tracking-tight ${data.profit >= 0 ? "text-in" : "text-out"}`,
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
								amount: data.profit,
								symbol
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "mt-1 text-xs text-subtle",
							children: [
								"Includes sales profit ",
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
									amount: data.salesProfit,
									symbol
								}),
								" and cash net",
								" ",
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
									amount: data.cashNet,
									symbol
								})
							]
						})
					] })
				]
			}),
			chartData.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
				className: "p-5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, { children: "Income vs expenses" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-4 h-64",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
						width: "100%",
						height: "100%",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AreaChart, {
							data: chartData,
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CartesianGrid, {
									stroke: "var(--kaze-border)",
									vertical: false
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
									dataKey: "date",
									tick: {
										fill: "var(--kaze-muted)",
										fontSize: 12
									}
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(YAxis, { tick: {
									fill: "var(--kaze-muted)",
									fontSize: 12
								} }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Tooltip, { contentStyle: {
									background: "var(--kaze-surface)",
									border: "1px solid var(--kaze-border)",
									borderRadius: 12,
									color: "var(--kaze-fg)"
								} }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Area, {
									type: "monotone",
									dataKey: "income",
									stroke: "var(--kaze-in)",
									fill: "var(--kaze-in)",
									fillOpacity: .15
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Area, {
									type: "monotone",
									dataKey: "expenses",
									stroke: "var(--kaze-out)",
									fill: "var(--kaze-out)",
									fillOpacity: .12
								})
							]
						})
					})
				})]
			}) : null,
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-4 lg:grid-cols-2",
				children: [data.settings.show_low_stock_widget ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Low stock" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
					headers: [
						"Product",
						"Qty",
						"Unit"
					],
					empty: data.lowStock.length === 0,
					colSpan: 3,
					children: data.lowStock.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: s.product_name }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
							className: "tabular text-out",
							children: s.quantity
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: s.unit })
					] }, s.product_name))
				})] }) : null, data.settings.show_sales_trend ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Sales, last 7 days" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Card, {
					className: "h-[220px] p-4",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResponsiveContainer, {
						width: "100%",
						height: "100%",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AreaChart, {
							data: data.salesTrend.map((d) => ({
								...d,
								date: d.date.slice(5)
							})),
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CartesianGrid, {
									stroke: "var(--kaze-border)",
									vertical: false
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(XAxis, {
									dataKey: "date",
									tick: {
										fill: "var(--kaze-muted)",
										fontSize: 12
									}
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(YAxis, { tick: {
									fill: "var(--kaze-muted)",
									fontSize: 12
								} }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Tooltip, { contentStyle: {
									background: "var(--kaze-surface)",
									border: "1px solid var(--kaze-border)",
									borderRadius: 12
								} }),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Area, {
									type: "monotone",
									dataKey: "total",
									stroke: "var(--kaze-brand)",
									fill: "var(--kaze-brand)",
									fillOpacity: .18
								})
							]
						})
					})
				})] }) : null]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "grid gap-4 lg:grid-cols-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
					className: "rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]",
					onSubmit: async (e) => {
						e.preventDefault();
						const form = e.currentTarget;
						const fd = new FormData(form);
						await addIncome({ data: {
							source: String(fd.get("source") ?? ""),
							amount: Number(fd.get("amount")),
							date: String(fd.get("date") || todayISO())
						} });
						form.reset();
						toast.success("Income added");
						await load();
					},
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Add income" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid gap-3 sm:grid-cols-3",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Source",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										name: "source",
										required: true,
										placeholder: "Client A"
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Amount",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										name: "amount",
										type: "number",
										step: "0.01",
										required: true
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Date",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										name: "date",
										type: "date",
										defaultValue: todayISO()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							className: "mt-4",
							size: "sm",
							children: "Add income"
						})
					]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("form", {
					className: "rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]",
					onSubmit: async (e) => {
						e.preventDefault();
						const form = e.currentTarget;
						const fd = new FormData(form);
						await addExpense({ data: {
							name: String(fd.get("name") ?? ""),
							amount: Number(fd.get("amount")),
							category: String(fd.get("category") ?? "Other"),
							date: String(fd.get("date") || todayISO())
						} });
						form.reset();
						toast.success("Expense added");
						await load();
					},
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Add expense" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid gap-3 sm:grid-cols-2",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Name",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										name: "name",
										required: true,
										placeholder: "Rent"
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Amount",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										name: "amount",
										type: "number",
										step: "0.01",
										required: true
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Category",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Select, {
										name: "category",
										defaultValue: "Other",
										children: EXPENSE_CATEGORIES.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", { children: c }, c))
									})
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Field, {
									label: "Date",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										name: "date",
										type: "date",
										defaultValue: todayISO()
									})
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							type: "submit",
							className: "mt-4",
							size: "sm",
							children: "Add expense"
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Income history" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Source",
					"Amount",
					"Date",
					""
				],
				empty: data.income.length === 0,
				children: data.income.map((i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: i.source }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: i.amount,
						symbol,
						tone: "in"
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: i.date
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						size: "sm",
						onClick: async () => {
							await deleteIncome({ data: { id: i.id } });
							toast.success("Deleted");
							await load();
						},
						children: "Delete"
					}) })
				] }, i.id))
			})] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SectionLabel, { children: "Expense history" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DataTable, {
				headers: [
					"Name",
					"Amount",
					"Category",
					"Date",
					""
				],
				empty: data.expenses.length === 0,
				children: data.expenses.map((e) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tr, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: e.name }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Money, {
						amount: e.amount,
						symbol,
						tone: "out"
					}) }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: e.category }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, {
						className: "text-muted",
						children: e.date
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Td, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						size: "sm",
						onClick: async () => {
							await deleteExpense({ data: { id: e.id } });
							toast.success("Deleted");
							await load();
						},
						children: "Delete"
					}) })
				] }, e.id))
			})] })
		]
	});
}
//#endregion
export { DashboardPage as component };
