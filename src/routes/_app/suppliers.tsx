import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { addSupplier, deleteSupplier, listSuppliers } from "@/lib/kaze/server";
import type { SupplierRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/suppliers")({ component: SuppliersPage });

function SuppliersPage() {
  const [rows, setRows] = useState<SupplierRow[] | null>(null);
  async function load() {
    setRows(await listSuppliers());
  }
  useEffect(() => {
    void load();
  }, []);
  if (!rows) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Suppliers"
        description="Vendors you buy stock from."
        actions={
          <Button variant="secondary" size="sm" asChild>
            <Link to="/orders">Purchase orders</Link>
          </Button>
        }
      />
      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-2"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          await addSupplier({
            data: {
              name: String(fd.get("name") ?? ""),
              email: String(fd.get("email") ?? ""),
              phone: String(fd.get("phone") ?? ""),
              address: String(fd.get("address") ?? ""),
              notes: "",
            },
          });
          form.reset();
          toast.success("Supplier saved");
          await load();
        }}
      >
        <Field label="Name">
          <Input name="name" required />
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
        <div>
          <Button type="submit" size="sm">
            Save supplier
          </Button>
        </div>
      </form>
      <DataTable headers={["Name", "Email", "Phone", "Address", ""]} empty={rows.length === 0}>
        {rows.map((s) => (
          <Tr key={s.id}>
            <Td>{s.name}</Td>
            <Td className="text-muted">{s.email || "—"}</Td>
            <Td>{s.phone || "—"}</Td>
            <Td>{s.address || "—"}</Td>
            <Td>
              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  await deleteSupplier({ data: { id: s.id } });
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
  );
}
