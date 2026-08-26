import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Money } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { downloadCsv } from "@/lib/kaze/format";
import {
  addCustomer,
  deleteCustomer,
  getSettings,
  listCustomers,
  updateCustomer,
} from "@/lib/kaze/server";
import type { CustomerRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/customers")({ component: CustomersPage });

function CustomersPage() {
  const [rows, setRows] = useState<CustomerRow[] | null>(null);
  const [symbol, setSymbol] = useState("$");
  const [edit, setEdit] = useState<CustomerRow | null>(null);

  async function load() {
    const [s, list] = await Promise.all([getSettings(), listCustomers()]);
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
        title="Customers"
        description="Contacts and lifetime spend from recorded sales."
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              downloadCsv(
                "customers.csv",
                ["Name", "Email", "Phone", "Address", "Orders", "Spent"],
                rows.map((c) => [
                  c.name,
                  c.email,
                  c.phone,
                  c.address,
                  String(c.order_count),
                  String(c.total_spent),
                ]),
              )
            }
          >
            Export CSV
          </Button>
        }
      />

      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-2"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          await addCustomer({
            data: {
              name: String(fd.get("name") ?? ""),
              email: String(fd.get("email") ?? ""),
              phone: String(fd.get("phone") ?? ""),
              address: String(fd.get("address") ?? ""),
              notes: String(fd.get("notes") ?? ""),
            },
          });
          form.reset();
          toast.success("Customer saved");
          await load();
        }}
      >
        <Field label="Name">
          <Input name="name" required placeholder="Customer name" />
        </Field>
        <Field label="Email">
          <Input name="email" type="email" />
        </Field>
        <Field label="Phone">
          <Input name="phone" />
        </Field>
        <Field label="Address">
          <Input name="address" />
        </Field>
        <Field label="Notes" className="sm:col-span-2 space-y-1.5">
          <Textarea name="notes" rows={2} />
        </Field>
        <div>
          <Button type="submit" size="sm">
            Save customer
          </Button>
        </div>
      </form>

      <DataTable
        headers={["Name", "Email", "Phone", "Orders", "Spent", ""]}
        empty={rows.length === 0}
      >
        {rows.map((c) => (
          <Tr key={c.id}>
            <Td>{c.name}</Td>
            <Td className="text-muted">{c.email || "—"}</Td>
            <Td>{c.phone || "—"}</Td>
            <Td className="tabular">{c.order_count}</Td>
            <Td>
              <Money amount={c.total_spent} symbol={symbol} />
            </Td>
            <Td>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" onClick={() => setEdit(c)}>
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (!confirm("Delete this customer?")) return;
                    await deleteCustomer({ data: { id: c.id } });
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
            <DialogTitle>Edit customer</DialogTitle>
          </DialogHeader>
          {edit ? (
            <form
              className="space-y-3"
              onSubmit={async (e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                await updateCustomer({
                  data: {
                    id: edit.id,
                    name: String(fd.get("name") ?? ""),
                    email: String(fd.get("email") ?? ""),
                    phone: String(fd.get("phone") ?? ""),
                    address: String(fd.get("address") ?? ""),
                    notes: String(fd.get("notes") ?? ""),
                  },
                });
                setEdit(null);
                toast.success("Saved");
                await load();
              }}
            >
              <Field label="Name">
                <Input name="name" defaultValue={edit.name} required />
              </Field>
              <Field label="Email">
                <Input name="email" type="email" defaultValue={edit.email} />
              </Field>
              <Field label="Phone">
                <Input name="phone" defaultValue={edit.phone} />
              </Field>
              <Field label="Address">
                <Input name="address" defaultValue={edit.address} />
              </Field>
              <Field label="Notes">
                <Textarea name="notes" defaultValue={edit.notes} rows={3} />
              </Field>
              <Button type="submit">Save changes</Button>
            </form>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
