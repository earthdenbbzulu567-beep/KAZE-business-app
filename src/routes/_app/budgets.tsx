import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Money } from "@/components/app-shell";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { EXPENSE_CATEGORIES } from "@/lib/kaze/format";
import { deleteBudget, getSettings, listBudgets, saveBudget } from "@/lib/kaze/server";
import type { BudgetRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/budgets")({ component: BudgetsPage });

function BudgetsPage() {
  const [rows, setRows] = useState<BudgetRow[] | null>(null);
  const [symbol, setSymbol] = useState("$");
  async function load() {
    const [s, list] = await Promise.all([getSettings(), listBudgets()]);
    setSymbol(s.currency_symbol);
    setRows(list);
  }
  useEffect(() => {
    void load();
  }, []);
  if (!rows) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Budgets"
        description="Monthly spending limits per expense category, tracked against this month."
      />
      <form
        className="flex flex-wrap items-end gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]"
        onSubmit={async (e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          await saveBudget({
            data: {
              category: String(fd.get("category") ?? "Other"),
              monthly_limit: Number(fd.get("monthly_limit")),
            },
          });
          toast.success("Budget saved");
          await load();
        }}
      >
        <Field label="Category">
          <Select name="category" defaultValue="Other">
            {EXPENSE_CATEGORIES.map((c) => (
              <option key={c}>{c}</option>
            ))}
          </Select>
        </Field>
        <Field label="Monthly limit">
          <Input name="monthly_limit" type="number" step="0.01" required />
        </Field>
        <Button type="submit" size="sm">
          Save budget
        </Button>
      </form>

      {rows.length === 0 ? (
        <p className="text-sm text-muted">No budgets yet.</p>
      ) : (
        <div className="space-y-3">
          {rows.map((b) => {
            const pct = b.monthly_limit ? (b.spent / b.monthly_limit) * 100 : 0;
            const over = b.spent > b.monthly_limit;
            return (
              <Card key={b.id}>
                <div className="mb-2 flex items-center justify-between gap-3">
                  <h3 className="font-medium">{b.category}</h3>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      await deleteBudget({ data: { id: b.id } });
                      toast.success("Removed");
                      await load();
                    }}
                  >
                    Remove
                  </Button>
                </div>
                <div className="mb-2 flex justify-between text-sm text-muted">
                  <span>
                    <Money amount={b.spent} symbol={symbol} /> of{" "}
                    <Money amount={b.monthly_limit} symbol={symbol} />
                  </span>
                  <span className={over ? "font-medium text-out" : "tabular"}>
                    {Math.round(pct)}%{over ? " — over budget" : ""}
                  </span>
                </div>
                <div className="h-2.5 overflow-hidden rounded-full bg-surface-2">
                  <div
                    className={`h-full rounded-full ${over ? "bg-out" : "bg-brand"}`}
                    style={{ width: `${Math.min(pct, 100)}%` }}
                  />
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
