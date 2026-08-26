import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { DataTable, Td, Tr } from "@/components/data-table";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { clearNotifications, listNotifications } from "@/lib/kaze/server";
import type { NotificationRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/notifications")({
  component: NotificationsPage,
});

function NotificationsPage() {
  const [rows, setRows] = useState<NotificationRow[] | null>(null);
  async function load() {
    setRows(await listNotifications());
  }
  useEffect(() => {
    void load();
  }, []);
  if (!rows) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Alerts"
        description="Low stock, recurring items, purchase orders, and other notices."
        actions={
          rows.length ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={async () => {
                await clearNotifications();
                toast.success("Cleared");
                await load();
              }}
            >
              Clear all
            </Button>
          ) : null
        }
      />
      <DataTable headers={["Message", "Category", "When"]} empty={rows.length === 0}>
        {rows.map((n) => (
          <Tr key={n.id}>
            <Td>{n.message}</Td>
            <Td>
              <Badge>{n.category}</Badge>
            </Td>
            <Td className="text-muted">{n.created_date}</Td>
          </Tr>
        ))}
      </DataTable>
    </div>
  );
}
