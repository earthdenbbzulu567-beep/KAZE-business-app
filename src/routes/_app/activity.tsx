import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { DataTable, Td, Tr } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";
import { Card, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { listActivity } from "@/lib/kaze/server";
import type { ActivityRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/activity")({ component: ActivityPage });

function ActivityPage() {
  const [data, setData] = useState<{ logs: ActivityRow[]; todayCount: number } | null>(null);
  useEffect(() => {
    void listActivity().then(setData);
  }, []);
  if (!data) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader title="Login activity" description="Recent sign-ins on this account." />
      <Card className="max-w-xs">
        <CardTitle>Logins today</CardTitle>
        <p className="mt-3 font-display text-3xl tabular">{data.todayCount}</p>
      </Card>
      <DataTable headers={["Name", "Time"]} empty={data.logs.length === 0}>
        {data.logs.map((l) => (
          <Tr key={l.id}>
            <Td>{l.username}</Td>
            <Td className="text-muted">{l.login_time}</Td>
          </Tr>
        ))}
      </DataTable>
    </div>
  );
}
