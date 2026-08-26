import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Field, PageHeader } from "@/components/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { getSettings, saveSettings } from "@/lib/kaze/server";
import type { Settings } from "@/lib/kaze/types";

export const Route = createFileRoute("/_app/settings")({ component: SettingsPage });

function SettingsPage() {
  const [s, setS] = useState<Settings | null>(null);
  useEffect(() => {
    void getSettings().then(setS);
  }, []);
  if (!s) return <Skeleton className="h-64" />;

  return (
    <div className="kaze-enter space-y-8">
      <PageHeader title="Settings" description="Business details, appearance, and dashboard widgets." />
      <form
        className="max-w-xl space-y-6"
        onSubmit={async (e) => {
          e.preventDefault();
          const fd = new FormData(e.currentTarget);
          const next = await saveSettings({
            data: {
              business_name: String(fd.get("business_name") ?? ""),
              currency_code: String(fd.get("currency_code") ?? "USD"),
              currency_symbol: String(fd.get("currency_symbol") ?? "$"),
              tax_rate: Number(fd.get("tax_rate") || 0),
              monthly_revenue_goal: Number(fd.get("monthly_revenue_goal") || 0),
              low_stock_threshold: Number(fd.get("low_stock_threshold") || 10),
              theme: String(fd.get("theme") ?? "dark"),
              font_size: String(fd.get("font_size") ?? "medium"),
              default_chart_type: String(fd.get("default_chart_type") ?? "line"),
              animations_enabled: fd.get("animations_enabled") === "on",
              show_low_stock_widget: fd.get("show_low_stock_widget") === "on",
              show_sales_trend: fd.get("show_sales_trend") === "on",
              about_text: String(fd.get("about_text") ?? ""),
            },
          });
          setS(next);
          document.documentElement.dataset.theme = next.theme === "light" ? "light" : "dark";
          document.documentElement.dataset.density = next.font_size;
          toast.success("Settings saved");
        }}
      >
        <section className="space-y-3">
          <h2 className="text-xs font-medium tracking-[0.14em] text-subtle uppercase">Business</h2>
          <Field label="Business name (on receipts)">
            <Input name="business_name" defaultValue={s.business_name} />
          </Field>
          <div className="grid grid-cols-2 gap-3">
            <Field label="Currency">
              <Select name="currency_code" defaultValue={s.currency_code}>
                <option value="USD">USD</option>
                <option value="ZMW">ZMW</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="ZAR">ZAR</option>
              </Select>
            </Field>
            <Field label="Symbol">
              <Input name="currency_symbol" defaultValue={s.currency_symbol} maxLength={4} />
            </Field>
          </div>
          <Field label="Tax / VAT rate (%)">
            <Input name="tax_rate" type="number" step="0.01" defaultValue={s.tax_rate} />
          </Field>
          <Field label="Monthly revenue goal">
            <Input
              name="monthly_revenue_goal"
              type="number"
              step="0.01"
              defaultValue={s.monthly_revenue_goal}
            />
          </Field>
          <Field label="Low stock threshold">
            <Input
              name="low_stock_threshold"
              type="number"
              step="1"
              defaultValue={s.low_stock_threshold}
            />
          </Field>
        </section>

        <section className="space-y-3">
          <h2 className="text-xs font-medium tracking-[0.14em] text-subtle uppercase">Appearance</h2>
          <Field label="Theme">
            <Select name="theme" defaultValue={s.theme}>
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </Select>
          </Field>
          <Field label="Text size">
            <Select name="font_size" defaultValue={s.font_size}>
              <option value="small">Small</option>
              <option value="medium">Medium</option>
              <option value="large">Large</option>
            </Select>
          </Field>
          <Field label="Default chart">
            <Select name="default_chart_type" defaultValue={s.default_chart_type}>
              <option value="line">Line</option>
              <option value="bar">Bar</option>
            </Select>
          </Field>
          <label className="flex h-11 items-center gap-2 text-sm">
            <input
              type="checkbox"
              name="animations_enabled"
              defaultChecked={s.animations_enabled}
              className="size-4 accent-brand"
            />
            Motion
          </label>
        </section>

        <section className="space-y-3">
          <h2 className="text-xs font-medium tracking-[0.14em] text-subtle uppercase">Dashboard</h2>
          <label className="flex h-11 items-center gap-2 text-sm">
            <input
              type="checkbox"
              name="show_low_stock_widget"
              defaultChecked={s.show_low_stock_widget}
              className="size-4 accent-brand"
            />
            Show low stock
          </label>
          <label className="flex h-11 items-center gap-2 text-sm">
            <input
              type="checkbox"
              name="show_sales_trend"
              defaultChecked={s.show_sales_trend}
              className="size-4 accent-brand"
            />
            Show sales trend
          </label>
          <Field label="About">
            <Textarea name="about_text" rows={3} defaultValue={s.about_text} />
          </Field>
        </section>

        <Button type="submit">Save settings</Button>
      </form>
    </div>
  );
}
