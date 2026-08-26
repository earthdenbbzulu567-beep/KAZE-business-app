import type { Sql } from "@/lib/db";
import { addMonths, num, todayISO } from "./format";
import type { Settings } from "./types";

export async function ensureSettings(sql: Sql, userId: string): Promise<Settings> {
  await sql`insert into settings (user_id) values (${userId}) on conflict (user_id) do nothing`;
  const rows = await sql<Record<string, unknown>>`select * from settings where user_id = ${userId}`;
  const r = rows[0] ?? {};
  return {
    user_id: userId,
    business_name: String(r.business_name ?? ""),
    currency_code: String(r.currency_code ?? "USD"),
    currency_symbol: String(r.currency_symbol ?? "$"),
    tax_rate: num(r.tax_rate),
    monthly_revenue_goal: num(r.monthly_revenue_goal),
    low_stock_threshold: num(r.low_stock_threshold) || 10,
    theme: String(r.theme ?? "dark"),
    font_size: String(r.font_size ?? "medium"),
    default_chart_type: String(r.default_chart_type ?? "line"),
    animations_enabled: Boolean(r.animations_enabled ?? true),
    show_low_stock_widget: Boolean(r.show_low_stock_widget ?? true),
    show_sales_trend: Boolean(r.show_sales_trend ?? true),
    about_text: String(r.about_text ?? ""),
    tutorial_completed: Boolean(r.tutorial_completed),
  };
}

export async function notify(
  sql: Sql,
  userId: string,
  message: string,
  category = "info",
) {
  await sql`insert into notifications (user_id, message, category) values (${userId}, ${message}, ${category})`;
}

function advance(dateStr: string, frequency: string): string {
  if (frequency === "weekly") {
    const dt = new Date(`${dateStr}T00:00:00Z`);
    dt.setUTCDate(dt.getUTCDate() + 7);
    return dt.toISOString().slice(0, 10);
  }
  if (frequency === "monthly") return addMonths(dateStr, 1);
  if (frequency === "quarterly") return addMonths(dateStr, 3);
  if (frequency === "yearly") return addMonths(dateStr, 12);
  return dateStr;
}

export async function processRecurring(sql: Sql, userId: string) {
  const today = todayISO();
  const due = await sql<{
    id: number;
    item_type: string;
    name: string;
    amount: unknown;
    category: string;
    client: string;
    frequency: string;
    next_run_date: string;
  }>`select id, item_type, name, amount, category, client, frequency, next_run_date
     from recurring_items
     where user_id = ${userId} and active = true and next_run_date <= ${today}`;

  for (const item of due) {
    const amount = num(item.amount);
    if (item.item_type === "expense") {
      await sql`insert into expenses (user_id, name, amount, category, date)
        values (${userId}, ${item.name}, ${amount}, ${item.category || "Other"}, ${today})`;
    } else {
      await sql`insert into documents (user_id, doc_type, title, client, amount, date, notes)
        values (${userId}, ${"invoice"}, ${item.name}, ${item.client || "Recurring client"}, ${amount}, ${today}, ${"Auto-generated from a recurring invoice."})`;
    }
    const next = advance(item.next_run_date, item.frequency);
    await sql`update recurring_items set next_run_date = ${next} where id = ${item.id} and user_id = ${userId}`;
    await notify(
      sql,
      userId,
      `Recurring ${item.item_type} "${item.name}" (${amount.toFixed(2)}) was generated.`,
      "recurring",
    );
  }
}
