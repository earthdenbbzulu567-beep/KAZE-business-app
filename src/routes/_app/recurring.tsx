import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Money } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { todayISO } from "@/lib/kaze/format";
import {
  addRecurring,
  deleteRecurring,
  getSettings,
  listRecurring,
  toggleRecurring,
} from "@/lib/kaze/server";
import type { RecurringRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/recurring")({ component: RecurringPage });

function RecurringPage() {
  const [rows, setRows] = useState<RecurringRow[] | null>(null);
  const [symbol, setSymbol] = useState("$");
  async function load() {
    const [s, list] = await Promise.all([getSettings(), listRecurring()]);
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
        title="Recurring items"
        description="Expenses or invoices that generate automatically when their date arrives."
      />
      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          await addRecurring({
            data: {
              item_type: String(fd.get("item_type") ?? "expense"),
              name: String(fd.get("name") ?? ""),
              amount: Number(fd.get("amount")),
              category: String(fd.get("category") ?? ""),
              client: String(fd.get("client") ?? ""),
              frequency: String(fd.get("frequency") ?? "monthly"),
              start_date: String(fd.get("start_date") || todayISO()),
            },
          });
          form.reset();
          toast.success("Scheduled");
          await load();
        }}
      >
        <Field label="Type">
          <Select name="item_type" defaultValue="expense">
            <option value="expense">Expense</option>
            <option value="invoice">Invoice</option>
          </Select>
        </Field>
        <Field label="Name">
          <Input name="name" required placeholder="Rent, retainer…" />
        </Field>
        <Field label="Amount">
          <Input name="amount" type="number" step="0.01" required />
        </Field>
        <Field label="Category (expenses)">
          <Input name="category" />
        </Field>
        <Field label="Client (invoices)">
          <Input name="client" />
        </Field>
        <Field label="Frequency">
          <Select name="frequency" defaultValue="monthly">
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </Select>
        </Field>
        <Field label="First run">
          <Input name="start_date" type="date" defaultValue={todayISO()} />
        </Field>
        <div className="flex items-end">
          <Button type="submit" size="sm">
            Schedule
          </Button>
        </div>
      </form>

      <DataTable
        headers={["Type", "Name", "Amount", "Frequency", "Next run", "Status", ""]}
        empty={rows.length === 0}
      >
        {rows.map((r) => (
          <Tr key={r.id}>
            <Td className="capitalize">{r.item_type}</Td>
            <Td>{r.name}</Td>
            <Td>
              <Money amount={r.amount} symbol={symbol} />
            </Td>
            <Td className="capitalize">{r.frequency}</Td>
            <Td>{r.next_run_date}</Td>
            <Td>
              <Badge tone={r.active ? "in" : "neutral"}>{r.active ? "Active" : "Paused"}</Badge>
            </Td>
            <Td>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await toggleRecurring({ data: { id: r.id } });
                    await load();
                  }}
                >
                  {r.active ? "Pause" : "Resume"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await deleteRecurring({ data: { id: r.id } });
                    toast.success("Deleted");
                    await load();
                  }}
                >
                  Delete
                </Button>
              </div>
            </Td>
          </Tr>
        ))}
      </DataTable>
    </div>
  );
}
