import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { printHtml } from "@/lib/kaze/format";
import { getPlan, getSettings, savePlan } from "@/lib/kaze/server";
import type { PlanRow } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/plan")({ component: PlanPage });

const SECTIONS: { key: keyof PlanRow; label: string; hint: string }[] = [
  { key: "mission", label: "Mission", hint: "Why the business exists." },
  { key: "products_services", label: "Products / services", hint: "What you sell, and why it is different." },
  { key: "target_market", label: "Target market", hint: "Who the ideal buyer is." },
  { key: "marketing_strategy", label: "Marketing", hint: "How people find you." },
  { key: "operations_plan", label: "Operations", hint: "How the day actually runs." },
  { key: "financial_plan", label: "Financial plan", hint: "Costs, pricing, funding." },
  { key: "goals", label: "Goals", hint: "What success looks like in 6 months, a year, three years." },
];

function PlanPage() {
  const [plan, setPlan] = useState<PlanRow | null | undefined>(undefined);
  const [biz, setBiz] = useState("");
  useEffect(() => {
    void (async () => {
      const [p, s] = await Promise.all([getPlan(), getSettings()]);
      setPlan(p);
      setBiz(s.business_name);
    })();
  }, []);
  if (plan === undefined) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader
        title="Business plan"
        description="A living document. Save whenever the strategy shifts."
        actions={
          plan ? (
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                printHtml(
                  "Business plan",
                  `<h1>${plan.business_name || biz || "Business plan"}</h1>
                   <p class="muted">Updated ${plan.updated_date ?? "—"}</p>
                   ${SECTIONS.map((s) => `<h3>${s.label}</h3><pre>${String(plan[s.key] ?? "")}</pre>`).join("")}`,
                )
              }
            >
              Print
            </Button>
          ) : null
        }
      />
      {plan?.updated_date ? (
        <p className="text-xs text-subtle">Last updated {plan.updated_date}</p>
      ) : null}
      <form
        className="space-y-5"
        onSubmit={async (e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          const payload = {
            business_name: String(fd.get("business_name") ?? ""),
            mission: String(fd.get("mission") ?? ""),
            products_services: String(fd.get("products_services") ?? ""),
            target_market: String(fd.get("target_market") ?? ""),
            marketing_strategy: String(fd.get("marketing_strategy") ?? ""),
            operations_plan: String(fd.get("operations_plan") ?? ""),
            financial_plan: String(fd.get("financial_plan") ?? ""),
            goals: String(fd.get("goals") ?? ""),
          };
          await savePlan({ data: payload });
          toast.success("Plan saved");
          setPlan({ ...payload, updated_date: new Date().toISOString().slice(0, 10) });
        }}
      >
        <Field label="Business name">
          <Input
            name="business_name"
            defaultValue={plan?.business_name || biz}
            className="max-w-md"
          />
        </Field>
        {SECTIONS.map((s) => (
          <Field key={s.key} label={s.label}>
            <p className="text-xs text-subtle">{s.hint}</p>
            <Textarea name={s.key} rows={3} defaultValue={String(plan?.[s.key] ?? "")} />
          </Field>
        ))}
        <Button type="submit">Save plan</Button>
      </form>
    </div>
  );
}
