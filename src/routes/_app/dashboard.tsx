import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { toast } from "sonner";
import { Money, SectionLabel } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { EmptyState, Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentUser } from "@/lib/auth/use-current-user";
import { EXPENSE_CATEGORIES, downloadCsv, todayISO } from "@/lib/kaze/format";
import {
  addExpense,
  addIncome,
  deleteExpense,
  deleteIncome,
  dismissTutorial,
  getDashboard,
  seedSample,
} from "@/lib/kaze/server";
import type { DashboardData } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/dashboard")({ component: DashboardPage });

function DashboardPage() {
  const user = useCurrentUser();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    try {
      setData(await getDashboard());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load dashboard");
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (error) {
    return (
      <EmptyState
        title="Could not load"
        description={error}
        action={
          <Button variant="secondary" onClick={() => void load()}>
            Try again
          </Button>
        }
      />
    );
  }

  if (!data) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <div className="grid gap-3 sm:grid-cols-3">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const symbol = data.settings.currency_symbol || "$";
  const chartDates = [
    ...new Set([...Object.keys(data.incomeByDate), ...Object.keys(data.expenseByDate)]),
  ].sort();
  const chartData = chartDates.map((d) => ({
    date: d.slice(5),
    income: data.incomeByDate[d] ?? 0,
    expenses: data.expenseByDate[d] ?? 0,
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

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title={`${user?.displayName?.split(" ")[0] ?? "Your"} desk`}
        description="Income, expenses, and the pulse of the last few days."
        actions={
          <>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                downloadCsv(
                  "income.csv",
                  ["Source", "Amount", "Date"],
                  data.income.map((i) => [i.source, String(i.amount), i.date]),
                )
              }
            >
              Income CSV
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                downloadCsv(
                  "expenses.csv",
                  ["Name", "Amount", "Category", "Date"],
                  data.expenses.map((e) => [e.name, String(e.amount), e.category, e.date]),
                )
              }
            >
              Expenses CSV
            </Button>
          </>
        }
      />

      {!data.settings.tutorial_completed ? (
        <Card className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="font-medium">New here?</p>
            <p className="text-sm text-muted">A short tour of where everything lives.</p>
          </div>
          <div className="flex gap-2">
            <Button asChild>
              <Link to="/help">Take the tour</Link>
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                void dismissTutorial();
                setData({
                  ...data,
                  settings: { ...data.settings, tutorial_completed: true },
                });
              }}
            >
              Dismiss
            </Button>
          </div>
        </Card>
      ) : null}

      {data.income.length === 0 && data.expenses.length === 0 ? (
        <Card className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="font-medium">Start with a sample shop</p>
            <p className="text-sm text-muted">
              Loads stock, customers, sales, and a couple of ledger lines so you can click around.
            </p>
          </div>
          <Button onClick={() => void onSeed()} disabled={busy}>
            {busy ? "Loading…" : "Load sample data"}
          </Button>
        </Card>
      ) : null}

      {data.settings.monthly_revenue_goal > 0 ? (
        <Card>
          <CardTitle>Monthly revenue goal</CardTitle>
          <div className="mt-3 flex justify-between text-sm text-muted">
            <span>
              <Money amount={data.monthRevenue} symbol={symbol} /> of{" "}
              <Money amount={data.settings.monthly_revenue_goal} symbol={symbol} />
            </span>
            <span className="tabular">{data.goalProgressPct}%</span>
          </div>
          <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-surface-2">
            <div
              className="h-full rounded-full bg-brand transition-[width] duration-[var(--motion-slow)]"
              style={{ width: `${data.goalProgressPct}%` }}
            />
          </div>
        </Card>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardTitle>Total income</CardTitle>
          <p className="mt-3 font-display text-3xl tracking-tight text-in">
            <Money amount={data.totalIncome} symbol={symbol} tone="in" />
          </p>
        </Card>
        <Card>
          <CardTitle>Total expenses</CardTitle>
          <p className="mt-3 font-display text-3xl tracking-tight text-out">
            <Money amount={data.totalExpenses} symbol={symbol} tone="out" />
          </p>
        </Card>
        <Card>
          <CardTitle>Profit / loss</CardTitle>
          <p
            className={`mt-3 font-display text-3xl tracking-tight ${data.profit >= 0 ? "text-in" : "text-out"}`}
          >
            <Money amount={data.profit} symbol={symbol} />
          </p>
          <p className="mt-1 text-xs text-subtle">
            Includes sales profit <Money amount={data.salesProfit} symbol={symbol} /> and cash net{" "}
            <Money amount={data.cashNet} symbol={symbol} />
          </p>
        </Card>
      </div>

      {chartData.length > 0 ? (
        <Card className="p-5">
          <CardTitle>Income vs expenses</CardTitle>
          <div className="mt-4 h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <CartesianGrid stroke="var(--kaze-border)" vertical={false} />
                <XAxis dataKey="date" tick={{ fill: "var(--kaze-muted)", fontSize: 12 }} />
                <YAxis tick={{ fill: "var(--kaze-muted)", fontSize: 12 }} />
                <Tooltip
                  contentStyle={{
                    background: "var(--kaze-surface)",
                    border: "1px solid var(--kaze-border)",
                    borderRadius: 12,
                    color: "var(--kaze-fg)",
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="income"
                  stroke="var(--kaze-in)"
                  fill="var(--kaze-in)"
                  fillOpacity={0.15}
                />
                <Area
                  type="monotone"
                  dataKey="expenses"
                  stroke="var(--kaze-out)"
                  fill="var(--kaze-out)"
                  fillOpacity={0.12}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        {data.settings.show_low_stock_widget ? (
          <div>
            <SectionLabel>Low stock</SectionLabel>
            <DataTable
              headers={["Product", "Qty", "Unit"]}
              empty={data.lowStock.length === 0}
              colSpan={3}
            >
              {data.lowStock.map((s) => (
                <Tr key={s.product_name}>
                  <Td>{s.product_name}</Td>
                  <Td className="tabular text-out">{s.quantity}</Td>
                  <Td>{s.unit}</Td>
                </Tr>
              ))}
            </DataTable>
          </div>
        ) : null}
        {data.settings.show_sales_trend ? (
          <div>
            <SectionLabel>Sales, last 7 days</SectionLabel>
            <Card className="h-[220px] p-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={data.salesTrend.map((d) => ({ ...d, date: d.date.slice(5) }))}>
                  <CartesianGrid stroke="var(--kaze-border)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: "var(--kaze-muted)", fontSize: 12 }} />
                  <YAxis tick={{ fill: "var(--kaze-muted)", fontSize: 12 }} />
                  <Tooltip
                    contentStyle={{
                      background: "var(--kaze-surface)",
                      border: "1px solid var(--kaze-border)",
                      borderRadius: 12,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="total"
                    stroke="var(--kaze-brand)"
                    fill="var(--kaze-brand)"
                    fillOpacity={0.18}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </Card>
          </div>
        ) : null}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <form
          className="rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]"
          onSubmit={async (e) => {
            e.preventDefault();
            const form = e.currentTarget;
            const fd = new FormData(form);
            await addIncome({
              data: {
                source: String(fd.get("source") ?? ""),
                amount: Number(fd.get("amount")),
                date: String(fd.get("date") || todayISO()),
              },
            });
            form.reset();
            toast.success("Income added");
            await load();
          }}
        >
          <SectionLabel>Add income</SectionLabel>
          <div className="grid gap-3 sm:grid-cols-3">
            <Field label="Source">
              <Input name="source" required placeholder="Client A" />
            </Field>
            <Field label="Amount">
              <Input name="amount" type="number" step="0.01" required />
            </Field>
            <Field label="Date">
              <Input name="date" type="date" defaultValue={todayISO()} />
            </Field>
          </div>
          <Button type="submit" className="mt-4" size="sm">
            Add income
          </Button>
        </form>
        <form
          className="rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]"
          onSubmit={async (e) => {
            e.preventDefault();
            const form = e.currentTarget;
            const fd = new FormData(form);
            await addExpense({
              data: {
                name: String(fd.get("name") ?? ""),
                amount: Number(fd.get("amount")),
                category: String(fd.get("category") ?? "Other"),
                date: String(fd.get("date") || todayISO()),
              },
            });
            form.reset();
            toast.success("Expense added");
            await load();
          }}
        >
          <SectionLabel>Add expense</SectionLabel>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Name">
              <Input name="name" required placeholder="Rent" />
            </Field>
            <Field label="Amount">
              <Input name="amount" type="number" step="0.01" required />
            </Field>
            <Field label="Category">
              <Select name="category" defaultValue="Other">
                {EXPENSE_CATEGORIES.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </Select>
            </Field>
            <Field label="Date">
              <Input name="date" type="date" defaultValue={todayISO()} />
            </Field>
          </div>
          <Button type="submit" className="mt-4" size="sm">
            Add expense
          </Button>
        </form>
      </div>

      <div>
        <SectionLabel>Income history</SectionLabel>
        <DataTable headers={["Source", "Amount", "Date", ""]} empty={data.income.length === 0}>
          {data.income.map((i) => (
            <Tr key={i.id}>
              <Td>{i.source}</Td>
              <Td>
                <Money amount={i.amount} symbol={symbol} tone="in" />
              </Td>
              <Td className="text-muted">{i.date}</Td>
              <Td>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await deleteIncome({ data: { id: i.id } });
                    toast.success("Deleted");
                    await load();
                  }}
                >
                  Delete
                </Button>
              </Td>
            </Tr>
          ))}
        </DataTable>
      </div>

      <div>
        <SectionLabel>Expense history</SectionLabel>
        <DataTable
          headers={["Name", "Amount", "Category", "Date", ""]}
          empty={data.expenses.length === 0}
        >
          {data.expenses.map((e) => (
            <Tr key={e.id}>
              <Td>{e.name}</Td>
              <Td>
                <Money amount={e.amount} symbol={symbol} tone="out" />
              </Td>
              <Td>{e.category}</Td>
              <Td className="text-muted">{e.date}</Td>
              <Td>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await deleteExpense({ data: { id: e.id } });
                    toast.success("Deleted");
                    await load();
                  }}
                >
                  Delete
                </Button>
              </Td>
            </Tr>
          ))}
        </DataTable>
      </div>
    </div>
  );
}
