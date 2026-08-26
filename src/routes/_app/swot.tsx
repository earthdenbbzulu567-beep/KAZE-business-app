import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { printHtml } from "@/lib/kaze/format";
import { addSwot, deleteSwot, listSwot } from "@/lib/kaze/server";
import type { SwotRow } from "@/lib/kaze/types";
import { Field } from "@/components/page-header";

export const Route = createFileRoute("/_app/swot")({ component: SwotPage });

function SwotPage() {
  const [rows, setRows] = useState<SwotRow[] | null>(null);
  async function load() {
    setRows(await listSwot());
  }
  useEffect(() => {
    void load();
  }, []);
  if (!rows) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="SWOT analysis"
        description="Strengths, weaknesses, opportunities, and threats — saved over time."
      />
      <form
        className="space-y-4 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          await addSwot({
            data: {
              title: String(fd.get("title") ?? ""),
              strengths: String(fd.get("strengths") ?? ""),
              weaknesses: String(fd.get("weaknesses") ?? ""),
              opportunities: String(fd.get("opportunities") ?? ""),
              threats: String(fd.get("threats") ?? ""),
            },
          });
          form.reset();
          toast.success("Analysis saved");
          await load();
        }}
      >
        <Field label="Title">
          <Input name="title" placeholder="Q3 strategy review" className="max-w-md" />
        </Field>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg bg-in/10 p-4">
            <Field label="Strengths">
              <Textarea name="strengths" rows={5} placeholder="What you do well" />
            </Field>
          </div>
          <div className="rounded-lg bg-warn/10 p-4">
            <Field label="Weaknesses">
              <Textarea name="weaknesses" rows={5} placeholder="Where you could improve" />
            </Field>
          </div>
          <div className="rounded-lg bg-brand/10 p-4">
            <Field label="Opportunities">
              <Textarea name="opportunities" rows={5} placeholder="Trends or gaps" />
            </Field>
          </div>
          <div className="rounded-lg bg-out/10 p-4">
            <Field label="Threats">
              <Textarea name="threats" rows={5} placeholder="What could hurt the business" />
            </Field>
          </div>
        </div>
        <Button type="submit" size="sm">
          Save analysis
        </Button>
      </form>

      {rows.length === 0 ? (
        <p className="text-sm text-muted">No analyses yet.</p>
      ) : (
        rows.map((a) => (
          <Card key={a.id} className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="font-display text-lg">{a.title}</h3>
                <p className="text-xs text-subtle">{a.created_date}</p>
              </div>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() =>
                    printHtml(
                      a.title,
                      `<h1>${a.title}</h1><p class="muted">${a.created_date}</p>
                       <h3>Strengths</h3><pre>${a.strengths}</pre>
                       <h3>Weaknesses</h3><pre>${a.weaknesses}</pre>
                       <h3>Opportunities</h3><pre>${a.opportunities}</pre>
                       <h3>Threats</h3><pre>${a.threats}</pre>`,
                    )
                  }
                >
                  Print
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    await deleteSwot({ data: { id: a.id } });
                    toast.success("Deleted");
                    await load();
                  }}
                >
                  Delete
                </Button>
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-md bg-in/10 p-3">
                <p className="text-xs font-medium text-in">Strengths</p>
                <p className="mt-1 whitespace-pre-wrap text-sm">{a.strengths || "—"}</p>
              </div>
              <div className="rounded-md bg-warn/10 p-3">
                <p className="text-xs font-medium text-warn">Weaknesses</p>
                <p className="mt-1 whitespace-pre-wrap text-sm">{a.weaknesses || "—"}</p>
              </div>
              <div className="rounded-md bg-brand/10 p-3">
                <p className="text-xs font-medium text-brand">Opportunities</p>
                <p className="mt-1 whitespace-pre-wrap text-sm">{a.opportunities || "—"}</p>
              </div>
              <div className="rounded-md bg-out/10 p-3">
                <p className="text-xs font-medium text-out">Threats</p>
                <p className="mt-1 whitespace-pre-wrap text-sm">{a.threats || "—"}</p>
              </div>
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
