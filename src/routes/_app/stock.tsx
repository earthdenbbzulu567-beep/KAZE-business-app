import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { Money } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { downloadCsv } from "@/lib/kaze/format";
import { addStock, deleteStock, getSettings, listStock, updateStock } from "@/lib/kaze/server";
import type { Settings, StockRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/stock")({ component: StockPage });

function StockPage() {
  const [items, setItems] = useState<StockRow[] | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [edit, setEdit] = useState<StockRow | null>(null);

  async function load() {
    const [s, rows] = await Promise.all([getSettings(), listStock()]);
    setSettings(s);
    setItems(rows);
  }
  useEffect(() => {
    void load();
  }, []);

  if (!items || !settings) return <Skeleton className="h-64" />;
  const symbol = settings.currency_symbol;
  const chart = items.map((i) => ({
    name: i.product_name,
    value: i.quantity * i.cost_price,
  }));

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Stock"
        description="Quantity, cost, and selling price. Sales reduce quantity automatically."
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              downloadCsv(
                "stock.csv",
                ["Product", "Qty", "Unit", "Cost", "Selling"],
                items.map((i) => [
                  i.product_name,
                  String(i.quantity),
                  i.unit,
                  String(i.cost_price),
                  String(i.selling_price),
                ]),
              )
            }
          >
            Export CSV
          </Button>
        }
      />

      {chart.length > 0 ? (
        <Card className="h-64 p-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chart}>
              <CartesianGrid stroke="var(--kaze-border)" vertical={false} />
              <XAxis dataKey="name" tick={{ fill: "var(--kaze-muted)", fontSize: 11 }} />
              <YAxis tick={{ fill: "var(--kaze-muted)", fontSize: 12 }} />
              <Tooltip
                contentStyle={{
                  background: "var(--kaze-surface)",
                  border: "1px solid var(--kaze-border)",
                  borderRadius: 12,
                }}
              />
              <Bar dataKey="value" fill="var(--kaze-brand)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      ) : null}

      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-6"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          await addStock({
            data: {
              product_name: String(fd.get("product_name") ?? ""),
              quantity: Number(fd.get("quantity")),
              cost_price: Number(fd.get("cost_price")),
              selling_price: Number(fd.get("selling_price")),
              unit: String(fd.get("unit") ?? "pcs"),
            },
          });
          form.reset();
          toast.success("Stock added");
          await load();
        }}
      >
        <Field label="Product" className="sm:col-span-2 space-y-1.5">
          <Input name="product_name" required placeholder="Rice 25kg" />
        </Field>
        <Field label="Quantity">
          <Input name="quantity" type="number" step="any" required />
        </Field>
        <Field label="Cost">
          <Input name="cost_price" type="number" step="0.01" required />
        </Field>
        <Field label="Selling">
          <Input name="selling_price" type="number" step="0.01" required />
        </Field>
        <Field label="Unit">
          <Input name="unit" placeholder="pcs" />
        </Field>
        <div className="flex items-end sm:col-span-6">
          <Button type="submit" size="sm">
            Add stock
          </Button>
        </div>
      </form>

      <DataTable
        headers={["Product", "Qty", "Unit", "Cost", "Selling", "Value", ""]}
        empty={items.length === 0}
      >
        {items.map((i) => (
          <Tr key={i.id}>
            <Td>{i.product_name}</Td>
            <Td className={i.quantity < settings.low_stock_threshold ? "text-out" : ""}>
              {i.quantity}
            </Td>
            <Td>{i.unit}</Td>
            <Td>
              <Money amount={i.cost_price} symbol={symbol} />
            </Td>
            <Td>
              <Money amount={i.selling_price} symbol={symbol} />
            </Td>
            <Td>
              <Money amount={i.quantity * i.cost_price} symbol={symbol} />
            </Td>
            <Td>
              <div className="flex gap-1">
                <Button variant="ghost" size="sm" onClick={() => setEdit(i)}>
                  Edit
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (!confirm("Delete this product?")) return;
                    await deleteStock({ data: { id: i.id } });
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
            <DialogTitle>Edit stock</DialogTitle>
          </DialogHeader>
          {edit ? (
            <form
              className="space-y-3"
              onSubmit={async (e) => {
                e.preventDefault();
                const fd = new FormData(e.currentTarget);
                await updateStock({
                  data: {
                    id: edit.id,
                    product_name: String(fd.get("product_name") ?? ""),
                    quantity: Number(fd.get("quantity")),
                    cost_price: Number(fd.get("cost_price")),
                    selling_price: Number(fd.get("selling_price")),
                    unit: String(fd.get("unit") ?? "pcs"),
                  },
                });
                setEdit(null);
                toast.success("Saved");
                await load();
              }}
            >
              <Field label="Product">
                <Input name="product_name" defaultValue={edit.product_name} required />
              </Field>
              <Field label="Quantity">
                <Input name="quantity" type="number" step="any" defaultValue={edit.quantity} required />
              </Field>
              <Field label="Cost">
                <Input name="cost_price" type="number" step="0.01" defaultValue={edit.cost_price} required />
              </Field>
              <Field label="Selling">
                <Input
                  name="selling_price"
                  type="number"
                  step="0.01"
                  defaultValue={edit.selling_price}
                  required
                />
              </Field>
              <Field label="Unit">
                <Input name="unit" defaultValue={edit.unit} />
              </Field>
              <Button type="submit">Save changes</Button>
            </form>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
