import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import {
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Money, SectionLabel } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getReports, getSettings } from "@/lib/kaze/server";

export const Route = createFileRoute("/_app/reports")({ component: ReportsPage });

function ReportsPage() {
  const [data, setData] = useState<Awaited<ReturnType<typeof getReports>> | null>(null);
  const [symbol, setSymbol] = useState("$");
  useEffect(() => {
    void (async () => {
      const [s, r] = await Promise.all([getSettings(), getReports()]);
      setSymbol(s.currency_symbol);
      setData(r);
    })();
  }, []);
  if (!data) return <Skeleton className="h-64" />;
  const chart = data.months.map((m) => ({
    month: m,
    income: data.monthlyIncome[m] ?? 0,
    expenses: data.monthlyExpenses[m] ?? 0,
    profit: data.monthlyProfit[m] ?? 0,
  }));

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Reports"
        description="Six-month profit trend and your best products and customers."
      />
      <Card className="h-72 p-4">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chart}>
            <CartesianGrid stroke="var(--kaze-border)" vertical={false} />
            <XAxis dataKey="month" tick={{ fill: "var(--kaze-muted)", fontSize: 12 }} />
            <YAxis tick={{ fill: "var(--kaze-muted)", fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: "var(--kaze-surface)",
                border: "1px solid var(--kaze-border)",
                borderRadius: 12,
              }}
            />
            <Bar dataKey="income" fill="var(--kaze-in)" fillOpacity={0.45} />
            <Bar dataKey="expenses" fill="var(--kaze-out)" fillOpacity={0.45} />
            <Line type="monotone" dataKey="profit" stroke="var(--kaze-brand)" strokeWidth={2} />
          </ComposedChart>
        </ResponsiveContainer>
      </Card>
      <div className="grid gap-6 lg:grid-cols-2">
        <div>
          <SectionLabel>Top products</SectionLabel>
          <DataTable
            headers={["Product", "Units", "Revenue", "Profit"]}
            empty={data.topProducts.length === 0}
          >
            {data.topProducts.map((p) => (
              <Tr key={p.product_name}>
                <Td>{p.product_name}</Td>
                <Td className="tabular">{p.units}</Td>
                <Td>
                  <Money amount={p.revenue} symbol={symbol} />
                </Td>
                <Td>
                  <Money amount={p.profit} symbol={symbol} tone="in" />
                </Td>
              </Tr>
            ))}
          </DataTable>
        </div>
        <div>
          <SectionLabel>Top customers</SectionLabel>
          <DataTable
            headers={["Customer", "Orders", "Spent"]}
            empty={data.topCustomers.length === 0}
          >
            {data.topCustomers.map((c) => (
              <Tr key={c.customer_name}>
                <Td>{c.customer_name}</Td>
                <Td className="tabular">{c.orders}</Td>
                <Td>
                  <Money amount={c.spent} symbol={symbol} />
                </Td>
              </Tr>
            ))}
          </DataTable>
        </div>
      </div>
    </div>
  );
}
