import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Money } from "@/components/app-shell";
import { DataTable, Td, Tr } from "@/components/data-table";
import { Field, PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { money, printHtml, todayISO } from "@/lib/kaze/format";
import {
  addDocument,
  deleteDocument,
  generateDocumentCopy,
  getSettings,
  listDocuments,
} from "@/lib/kaze/server";
import type { DocumentRow, Settings } from "@/lib/kaze/types";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/documents")({ component: DocumentsPage });

function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentRow[] | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [filter, setFilter] = useState("all");
  const [ai, setAi] = useState<string | null>(null);
  const [aiBusy, setAiBusy] = useState(false);

  async function load() {
    const [s, list] = await Promise.all([getSettings(), listDocuments()]);
    setSettings(s);
    setDocs(list);
  }
  useEffect(() => {
    void load();
  }, []);
  if (!docs || !settings) return <Skeleton className="h-64" />;
  const symbol = settings.currency_symbol;
  const shown = filter === "all" ? docs : docs.filter((d) => d.doc_type === filter);

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Documents"
        description="Invoices, contracts, and reports — print a clean copy any time."
      />

      <div className="flex flex-wrap gap-2">
        {["all", "invoice", "contract", "report"].map((t) => (
          <Button
            key={t}
            size="sm"
            variant={filter === t ? "default" : "secondary"}
            onClick={() => setFilter(t)}
            className={cn("capitalize")}
          >
            {t === "all" ? "All" : t}
          </Button>
        ))}
      </div>

      <form
        className="space-y-3 rounded-xl bg-surface p-5 shadow-[var(--kaze-shadow)]"
        onSubmit={async (e) => {
          e.preventDefault();
          const form = e.currentTarget;
          const fd = new FormData(form);
          const amountRaw = String(fd.get("amount") ?? "");
          await addDocument({
            data: {
              doc_type: String(fd.get("doc_type") ?? "invoice"),
              title: String(fd.get("title") ?? ""),
              client: String(fd.get("client") ?? ""),
              amount: amountRaw ? Number(amountRaw) : null,
              date: String(fd.get("date") || todayISO()),
              notes: String(fd.get("notes") ?? ""),
            },
          });
          form.reset();
          toast.success("Document saved");
          await load();
        }}
      >
        <div className="grid gap-3 sm:grid-cols-2">
          <Field label="Type">
            <Select name="doc_type" defaultValue="invoice">
              <option value="invoice">Invoice</option>
              <option value="contract">Contract</option>
              <option value="report">Report</option>
            </Select>
          </Field>
          <Field label="Date">
            <Input name="date" type="date" defaultValue={todayISO()} />
          </Field>
          <Field label="Title">
            <Input name="title" required placeholder="Invoice 1042 — Acme" />
          </Field>
          <Field label="Client">
            <Input name="client" required />
          </Field>
          <Field label="Amount (optional)">
            <Input name="amount" type="number" step="0.01" />
          </Field>
        </div>
        <Field label="Notes">
          <Textarea name="notes" rows={3} placeholder="Scope, terms, details…" />
        </Field>
        <div className="flex flex-wrap gap-2">
          <Button type="submit" size="sm">
            Save document
          </Button>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            disabled={aiBusy}
            onClick={async (e) => {
              const form = (e.currentTarget as HTMLButtonElement).form;
              if (!form) return;
              const fd = new FormData(form);
              setAiBusy(true);
              setAi("Generating…");
              try {
                const amountRaw = String(fd.get("amount") ?? "");
                const r = await generateDocumentCopy({
                  data: {
                    doc_type: String(fd.get("doc_type") ?? "invoice"),
                    title: String(fd.get("title") ?? ""),
                    client: String(fd.get("client") ?? ""),
                    amount: amountRaw ? Number(amountRaw) : null,
                    notes: String(fd.get("notes") ?? ""),
                    business_name: settings.business_name,
                  },
                });
                if (!r.ok) {
                  setAi(r.error);
                  toast.error(r.error);
                } else {
                  setAi(r.text);
                  const notes = form.elements.namedItem("notes") as HTMLTextAreaElement | null;
                  if (notes && r.text) notes.value = r.text;
                }
              } finally {
                setAiBusy(false);
              }
            }}
          >
            {aiBusy ? "Generating…" : "Draft with AI"}
          </Button>
        </div>
        {ai ? (
          <pre className="max-h-48 overflow-auto rounded-md bg-surface-2 p-3 text-xs whitespace-pre-wrap text-muted">
            {ai}
          </pre>
        ) : null}
      </form>

      <DataTable
        headers={["Type", "Title", "Client", "Amount", "Date", ""]}
        empty={shown.length === 0}
      >
        {shown.map((d) => (
          <Tr key={d.id}>
            <Td>
              <Badge tone={d.doc_type === "invoice" ? "in" : d.doc_type === "contract" ? "brand" : "neutral"}>
                {d.doc_type}
              </Badge>
            </Td>
            <Td className="font-medium">{d.title}</Td>
            <Td>{d.client}</Td>
            <Td>{d.amount != null ? <Money amount={d.amount} symbol={symbol} /> : "—"}</Td>
            <Td className="text-muted">{d.date}</Td>
            <Td>
              <div className="flex gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    const tax =
                      d.amount != null && settings.tax_rate
                        ? (d.amount * settings.tax_rate) / 100
                        : 0;
                    printHtml(
                      d.title,
                      `<h1>${settings.business_name || "KAZE Traders"}</h1>
                       <p class="muted">${d.doc_type.toUpperCase()} · ${d.date}</p>
                       <h2>${d.title}</h2>
                       <p>Client: ${d.client}</p>
                       ${d.amount != null ? `<p>Amount: ${money(d.amount, symbol)}</p>` : ""}
                       ${tax ? `<p>Tax (${settings.tax_rate}%): ${money(tax, symbol)}</p><p class="total">Total ${money(d.amount! + tax, symbol)}</p>` : ""}
                       <pre>${d.notes || ""}</pre>`,
                    );
                  }}
                >
                  Print
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={async () => {
                    if (!confirm("Delete this document?")) return;
                    await deleteDocument({ data: { id: d.id } });
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
