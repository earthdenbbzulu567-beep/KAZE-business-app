import { createFileRoute, Link } from "@tanstack/react-router";
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
import {
  addOrder,
  deleteOrder,
  getSettings,
  listOrders,
  listStock,
  listSuppliers,
  receiveOrder,
} from "@/lib/kaze/server";
import type { PurchaseOrderRow, StockRow, SupplierRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/orders")({ component: OrdersPage });

function OrdersPage() {
  const [rows, setRows] = useState<PurchaseOrderRow[] | null>(null);
  const [suppliers, setSuppliers] = useState<SupplierRow[]>([]);
  const [stock, setStock] = useState<StockRow[]>([]);
  const [symbol, setSymbol] = useState("$");

  async function load() {
    const [s, list, sup, st] = await Promise.all([
      getSettings(),
      listOrders(),
      listSuppliers(),
      listStock(),
    ]);
    setSymbol(s.currency_symbol);
    setRows(list);
    setSuppliers(sup);
    setStock(st);
  }
  useEffect(() => {
    void load();
  }, []);
  if (!rows) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Purchase orders"
        description="Order stock from suppliers. Receiving an order can add quantity to inventory."
        actions={
          <Button variant="secondary" size="sm" asChild>
            <Link to="/suppliers">Suppliers</Link>
          </Button>
        }
      />
      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          const sid = String(fd.get("supplier_id") ?? "");
          const stid = String(fd.get("stock_id") ?? "");
          await addOrder({
            data: {
              supplier_id: sid ? Number(sid) : null,
              item_description: String(fd.get("item_description") ?? ""),
              quantity: Number(fd.get("quantity")),
              unit_cost: Number(fd.get("unit_cost")),
              expected_date: String(fd.get("expected_date") ?? ""),
              stock_id: stid ? Number(stid) : null,
            },
          });
          form.reset();
          toast.success("Order created");
          await load();
        }}
      >
        <Field label="Supplier">
          <Select name="supplier_id" defaultValue="">
            <option value="">No supplier</option>
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Item" className="sm:col-span-2 space-y-1.5">
          <Input name="item_description" required placeholder="What are you ordering?" />
        </Field>
        <Field label="Link to stock">
          <Select name="stock_id" defaultValue="">
            <option value="">Not linked</option>
            {stock.map((s) => (
              <option key={s.id} value={s.id}>
                {s.product_name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Quantity">
          <Input name="quantity" type="number" step="any" required />
        </Field>
        <Field label="Unit cost">
          <Input name="unit_cost" type="number" step="0.01" required />
        </Field>
        <Field label="Expected">
          <Input name="expected_date" type="date" />
        </Field>
        <div className="flex items-end">
          <Button type="submit" size="sm">
            Create order
          </Button>
        </div>
      </form>

      <DataTable
        headers={["Item", "Supplier", "Qty", "Unit cost", "Total", "Status", "Expected", ""]}
        empty={rows.length === 0}
      >
        {rows.map((po) => (
          <Tr key={po.id}>
            <Td>{po.item_description}</Td>
            <Td>{po.supplier_name || "—"}</Td>
            <Td className="tabular">{po.quantity}</Td>
            <Td>
              <Money amount={po.unit_cost} symbol={symbol} />
            </Td>
            <Td>
              <Money amount={po.total_cost} symbol={symbol} />
            </Td>
            <Td>
              <Badge tone={po.status === "received" ? "in" : "warn"}>
                {po.status === "received" ? "Received" : "Pending"}
              </Badge>
            </Td>
            <Td className="text-muted">{po.expected_date || "—"}</Td>
            <Td>
              <div className="flex gap-1">
                {po.status !== "received" ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={async () => {
                      await receiveOrder({ data: { id: po.id } });
                      toast.success("Received");
                      await load();
                    }}
                  >
                    Receive
                  </Button>
                ) : null}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await deleteOrder({ data: { id: po.id } });
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
