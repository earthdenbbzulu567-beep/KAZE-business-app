import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Money } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { downloadCsv, todayISO } from "@/lib/kaze/format";
import { addCash, deleteCash, getSettings, listCash, updateCash } from "@/lib/kaze/server";
import type { CashRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/cashbook")({ component: CashPage });

function CashPage() {
  const [rows, setRows] = useState<CashRow[] | null>(null);
  const [symbol, setSymbol] = useState("$");
  const [edit, setEdit] = useState<CashRow | null>(null);

  async function load() {
    const [s, list] = await Promise.all([getSettings(), listCash()]);
    setSymbol(s.currency_symbol);
    setRows(list);
  }
  useEffect(() => {
    void load();
  }, []);
  if (!rows) return <Skeleton className="h-64" />;

  const inn = rows.filter((r) => r.entry_type === "in").reduce((s, r) => s + r.amount, 0);
  const out = rows.filter((r) => r.entry_type === "out").reduce((s, r) => s + r.amount, 0);

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Cash book"
        description="Till cash in and out, separate from the income statement."
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              downloadCsv(
                "cashbook.csv",
                ["Type", "Category", "Description", "Amount", "Date"],
                rows.map((r) => [r.entry_type, r.category, r.description, String(r.amount), r.date]),
              )
            }
          >
            Export CSV
          </Button>
        }
      />
      <p className="text-sm text-muted">
        In <Money amount={inn} symbol={symbol} tone="in" /> · Out{" "}
        <Money amount={out} symbol={symbol} tone="out" /> · Net{" "}
        <Money amount={inn - out} symbol={symbol} />
      </p>

      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-5"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          await addCash({
            data: {
              entry_type: String(fd.get("entry_type") ?? "in"),
              category: String(fd.get("category") ?? ""),
              description: String(fd.get("description") ?? ""),
              amount: Number(fd.get("amount")),
              date: String(fd.get("date") || todayISO()),
            },
          });
          form.reset();
          toast.success("Entry added");
          await load();
        }}
      >
        <Field label="Type">
          <Select name="entry_type" defaultValue="in">
            <option value="in">Cash in</option>
            <option value="out">Cash out</option>
          </Select>
        </Field>
        <Field label="Category">
          <Input name="category" required placeholder="Rent, Sales…" />
        </Field>
        <Field label="Description">
          <Input name="description" />
        </Field>
        <Field label="Amount">
          <Input name="amount" type="number" step="0.01" required />
        </Field>
        <Field label="Date">
          <Input name="date" type="date" defaultValue={todayISO()} />
        </Field>
        <div className="sm:col-span-5">
          <Button type="submit" size="sm">
            Add entry
          </Button>
        </div>
      </form>

      <DataTable
        headers={["Type", "Category", "Description", "Amount", "Date", ""]}
        empty={rows.length === 0}
      >
        {rows.map((r) => (
          <Tr key={r.id}>
            <Td>
              <Badge tone={r.entry_type === "in" ? "in" : "out"}>
                {r.entry_type === "in" ? "In" : "Out"}
              </Badge>
            </Td>
            <Td>{r.category}</Td>
            <Td className="text-muted">{r.description || "—"}</Td>
            <Td>
              <Money amount={r.amount} symbol={symbol} tone={r.entry_type === "in" ? "in" : "out"} />
            </Td>
            <Td className="text-muted">{r.date}</Td>
            <Td>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" onClick={() => setEdit(r)}>
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await deleteCash({ data: { id: r.id } });
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

      <Dialog open={!!edit} onOpenChange={(o) => !o && setEdit(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit cash entry</DialogTitle>
          </DialogHeader>
          {edit ? (
            <form
              className="space-y-3"
              onSubmit={async (e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                await updateCash({
                  data: {
                    id: edit.id,
                    entry_type: String(fd.get("entry_type") ?? "in"),
                    category: String(fd.get("category") ?? ""),
                    description: String(fd.get("description") ?? ""),
                    amount: Number(fd.get("amount")),
                    date: String(fd.get("date") || todayISO()),
                  },
                });
                setEdit(null);
                toast.success("Saved");
                await load();
              }}
            >
              <Field label="Type">
                <Select name="entry_type" defaultValue={edit.entry_type}>
                  <option value="in">Cash in</option>
                  <option value="out">Cash out</option>
                </Select>
              </Field>
              <Field label="Category">
                <Input name="category" defaultValue={edit.category} required />
              </Field>
              <Field label="Description">
                <Input name="description" defaultValue={edit.description} />
              </Field>
              <Field label="Amount">
                <Input name="amount" type="number" step="0.01" defaultValue={edit.amount} required />
              </Field>
              <Field label="Date">
                <Input name="date" type="date" defaultValue={edit.date} required />
              </Field>
              <Button type="submit">Save</Button>
            </form>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
