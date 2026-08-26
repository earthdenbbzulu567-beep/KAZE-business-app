import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { useCurrentUser } from "@/lib/auth/use-current-user";
import { addTeam, deleteTeam, listTeam } from "@/lib/kaze/server";
import type { TeamRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/team")({ component: TeamPage });

function TeamPage() {
  const user = useCurrentUser();
  const [rows, setRows] = useState<TeamRow[] | null>(null);
  async function load() {
    setRows(await listTeam());
  }
  useEffect(() => {
    void load();
  }, []);
  if (!rows) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Team"
        description="A roster of people who work this desk. Each person still signs in with their own account."
      />
      <form
        className="grid gap-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)] sm:grid-cols-3"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          await addTeam({
            data: {
              name: String(fd.get("name") ?? ""),
              email: String(fd.get("email") ?? ""),
              role: String(fd.get("role") ?? "Staff"),
            },
          });
          form.reset();
          toast.success("Added to team");
          await load();
        }}
      >
        <Field label="Name">
          <Input name="name" required />
        </Field>
        <Field label="Email">
          <Input name="email" type="email" />
        </Field>
        <Field label="Role">
          <Input name="role" placeholder="Staff" />
        </Field>
        <div>
          <Button type="submit" size="sm">
            Add member
          </Button>
        </div>
      </form>
      <DataTable headers={["Name", "Email", "Role", ""]} empty={false}>
        <Tr>
          <Td>{user?.displayName ?? "You"}</Td>
          <Td className="text-muted">{user?.primaryEmail ?? "—"}</Td>
          <Td>Owner</Td>
          <Td>—</Td>
        </Tr>
        {rows.map((m) => (
          <Tr key={m.id}>
            <Td>{m.name}</Td>
            <Td className="text-muted">{m.email || "—"}</Td>
            <Td>{m.role}</Td>
            <Td>
              <Button
                variant="ghost"
                size="sm"
                onClick={async () => {
                  await deleteTeam({ data: { id: m.id } });
                  toast.success("Removed");
                  await load();
                }}
              >
                Remove
              </Button>
            </Td>
          </Tr>
        ))}
      </DataTable>
    </div>
  );
}
