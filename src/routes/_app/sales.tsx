import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { toast } from "sonner";
import { Money } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { downloadCsv, money, printHtml, todayISO } from "@/lib/kaze/format";
import { addSale, deleteSale, getSettings, listCustomers, listSales, listStock } from "@/lib/kaze/server";
import type { CustomerRow, SaleRow, Settings, StockRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/sales")({ component: SalesPage });

function SalesPage() {
  const [sales, setSales] = useState<SaleRow[] | null>(null);
  const [stock, setStock] = useState<StockRow[]>([]);
  const [customers, setCustomers] = useState<CustomerRow[]>([]);
  const [settings, setSettings] = useState<Settings | null>(null);

  async function load() {
    const [s, rows, st, cu] = await Promise.all([
      getSettings(),
      listSales(),
      listStock(),
      listCustomers(),
    ]);
    setSettings(s);
    setSales(rows);
    setStock(st);
    setCustomers(cu);
  }
  useEffect(() => {
    void load();
  }, []);

  if (!sales || !settings) return <Skeleton className="h-64" />;
  const symbol = settings.currency_symbol;
  const byDate: Record<string, number> = {};
  for (const s of sales) byDate[s.sale_date] = (byDate[s.sale_date] ?? 0) + s.total_amount;
  const chart = Object.keys(byDate)
    .sort()
    .map((d) => ({ date: d.slice(5), total: byDate[d] }));

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Sales"
        description="Record a sale against stock. Profit is calculated and inventory drops."
        actions={
          <Button
            variant="secondary"
            size="sm"
            onClick={() =>
              downloadCsv(
                "sales.csv",
                ["Product", "Qty", "Price", "Total", "Profit", "Date", "Customer"],
                sales.map((s) => [
                  s.product_name,
                  String(s.quantity_sold),
                  String(s.selling_price_at_time),
                  String(s.total_amount),
                  String(s.profit),
                  s.sale_date,
                  s.customer_name,
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
            <AreaChart data={chart}>
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
                stroke="var(--kaze-in)"
                fill="var(--kaze-in)"
                fillOpacity={0.15}
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      ) : null}

      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          const cid = String(fd.get("customer_id") ?? "");
          try {
            await addSale({
              data: {
                stock_id: Number(fd.get("stock_id")),
                quantity: Number(fd.get("quantity")),
                customer_id: cid ? Number(cid) : null,
                customer_name: String(fd.get("customer_name") ?? ""),
                customer_email: String(fd.get("customer_email") ?? ""),
                date: String(fd.get("date") || todayISO()),
              },
            });
            form.reset();
            toast.success("Sale recorded");
            await load();
          } catch (err) {
            toast.error(err instanceof Error ? err.message : "Could not record sale");
          }
        }}
      >
        <Field label="Product" className="sm:col-span-2 space-y-1.5">
          <Select name="stock_id" required defaultValue="">
            <option value="" disabled>
              Select product
            </option>
            {stock.map((s) => (
              <option key={s.id} value={s.id}>
                {s.product_name} (stock {s.quantity}, {money(s.selling_price, symbol)})
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Quantity">
          <Input name="quantity" type="number" step="any" required />
        </Field>
        <Field label="Saved customer">
          <Select name="customer_id" defaultValue="">
            <option value="">Walk-in / new</option>
            {customers.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </Select>
        </Field>
        <Field label="Name if new">
          <Input name="customer_name" placeholder="Optional" />
        </Field>
        <Field label="Email if new">
          <Input name="customer_email" type="email" placeholder="Optional" />
        </Field>
        <Field label="Date">
          <Input name="date" type="date" defaultValue={todayISO()} />
        </Field>
        <div className="sm:col-span-3">
          <Button type="submit" size="sm">
            Record sale
          </Button>
        </div>
      </form>

      <DataTable
        headers={["Product", "Qty", "Price", "Total", "Profit", "Date", "Customer", ""]}
        empty={sales.length === 0}
      >
        {sales.map((s) => (
          <Tr key={s.id}>
            <Td>{s.product_name}</Td>
            <Td className="tabular">{s.quantity_sold}</Td>
            <Td>
              <Money amount={s.selling_price_at_time} symbol={symbol} />
            </Td>
            <Td>
              <Money amount={s.total_amount} symbol={symbol} />
            </Td>
            <Td>
              <Money amount={s.profit} symbol={symbol} tone="in" />
            </Td>
            <Td className="text-muted">{s.sale_date}</Td>
            <Td>{s.customer_name || "Walk-in"}</Td>
            <Td>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const tax = (s.total_amount * (settings.tax_rate || 0)) / 100;
                    printHtml(
                      "Receipt",
                      `<h1>${settings.business_name || "KAZE Traders"}</h1>
                       <p class="muted">Sales receipt · ${s.sale_date}</p>
                       <table>
                         <tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr>
                         <tr><td>${s.product_name}</td><td>${s.quantity_sold}</td><td>${money(s.selling_price_at_time, symbol)}</td><td>${money(s.total_amount, symbol)}</td></tr>
                       </table>
                       <p>Customer: ${s.customer_name || "Walk-in"}</p>
                       ${settings.tax_rate ? `<p>Tax (${settings.tax_rate}%): ${money(tax, symbol)}</p>` : ""}
                       <p class="total">Total ${money(s.total_amount + tax, symbol)}</p>`,
                    );
                  }}
                >
                  Receipt
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (!confirm("Delete this sale and restore stock?")) return;
                    await deleteSale({ data: { id: s.id } });
                    toast.success("Sale deleted");
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
