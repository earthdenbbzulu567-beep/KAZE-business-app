import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import { getSql } from "@/lib/db";
import { authMiddleware } from "@/lib/auth/middleware";
import { addMonths, monthKey, num, todayISO } from "./format";
import { ensureSettings, notify, processRecurring } from "./helpers";
import type {
  ActivityRow,
  BudgetRow,
  CashRow,
  CustomerRow,
  DashboardData,
  DocumentRow,
  ExpenseRow,
  IncomeRow,
  NotificationRow,
  PlanRow,
  PurchaseOrderRow,
  RecurringRow,
  SaleRow,
  Settings,
  StockRow,
  SupplierRow,
  SwotRow,
  TeamRow,
} from "./types";

const idSchema = z.object({ id: z.number() });

export const getSettings = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    const sql = await getSql();
    return ensureSettings(sql, context.userId);
  });

export const saveSettings = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      business_name: z.string(),
      currency_code: z.string(),
      currency_symbol: z.string(),
      tax_rate: z.number(),
      monthly_revenue_goal: z.number(),
      low_stock_threshold: z.number(),
      theme: z.string(),
      font_size: z.string(),
      default_chart_type: z.string(),
      animations_enabled: z.boolean(),
      show_low_stock_widget: z.boolean(),
      show_sales_trend: z.boolean(),
      about_text: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await ensureSettings(sql, context.userId);
    await sql`update settings set
      business_name = ${data.business_name},
      currency_code = ${data.currency_code},
      currency_symbol = ${data.currency_symbol},
      tax_rate = ${data.tax_rate},
      monthly_revenue_goal = ${data.monthly_revenue_goal},
      low_stock_threshold = ${data.low_stock_threshold},
      theme = ${data.theme},
      font_size = ${data.font_size},
      default_chart_type = ${data.default_chart_type},
      animations_enabled = ${data.animations_enabled},
      show_low_stock_widget = ${data.show_low_stock_widget},
      show_sales_trend = ${data.show_sales_trend},
      about_text = ${data.about_text}
      where user_id = ${context.userId}`;
    return ensureSettings(sql, context.userId);
  });

export const dismissTutorial = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    const sql = await getSql();
    await ensureSettings(sql, context.userId);
    await sql`update settings set tutorial_completed = true where user_id = ${context.userId}`;
  });

export const recordActivity = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(z.object({ username: z.string() }))
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`insert into user_activity (user_id, username) values (${context.userId}, ${data.username})`;
  });

export const getDashboard = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<DashboardData> => {
    const sql = await getSql();
    const uid = context.userId;
    const settings = await ensureSettings(sql, uid);
    await processRecurring(sql, uid);

    const incomeRows = await sql<Record<string, unknown>>`select id, source, amount, date from income where user_id = ${uid} order by date desc, id desc`;
    const expenseRows = await sql<Record<string, unknown>>`select id, name, amount, category, date from expenses where user_id = ${uid} order by date desc, id desc`;
    const income: IncomeRow[] = incomeRows.map((r) => ({
      id: num(r.id),
      source: String(r.source),
      amount: num(r.amount),
      date: String(r.date),
    }));
    const expenses: ExpenseRow[] = expenseRows.map((r) => ({
      id: num(r.id),
      name: String(r.name),
      amount: num(r.amount),
      category: String(r.category),
      date: String(r.date),
    }));
    const totalIncome = income.reduce((s, i) => s + i.amount, 0);
    const totalExpenses = expenses.reduce((s, e) => s + e.amount, 0);

    const profitRow = await sql<{ p: unknown }>`select coalesce(sum(profit),0) as p from sales where user_id = ${uid}`;
    const salesProfit = num(profitRow[0]?.p);
    const cashIn = await sql<{ p: unknown }>`select coalesce(sum(amount),0) as p from cash_books where user_id = ${uid} and entry_type = ${"in"}`;
    const cashOut = await sql<{ p: unknown }>`select coalesce(sum(amount),0) as p from cash_books where user_id = ${uid} and entry_type = ${"out"}`;
    const cashNet = num(cashIn[0]?.p) - num(cashOut[0]?.p);
    const profit = totalIncome - totalExpenses + salesProfit + cashNet;

    const monthStart = todayISO().slice(0, 8) + "01";
    const monthRev = await sql<{ p: unknown }>`select coalesce(sum(total_amount),0) as p from sales where user_id = ${uid} and sale_date >= ${monthStart}`;
    const monthRevenue = num(monthRev[0]?.p);
    const goalProgressPct = settings.monthly_revenue_goal
      ? Math.min(100, Math.round((monthRevenue / settings.monthly_revenue_goal) * 1000) / 10)
      : 0;

    const lowStock = await sql<{ product_name: string; quantity: unknown; unit: string }>`
      select product_name, quantity, unit from stock
      where user_id = ${uid} and quantity < ${settings.low_stock_threshold}
      order by quantity asc`;

    const trend: { date: string; total: number }[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      trend.push({ date: key, total: 0 });
    }
    const since = trend[0]?.date ?? todayISO();
    const salesDays = await sql<{ sale_date: string; total: unknown }>`
      select sale_date, sum(total_amount) as total from sales
      where user_id = ${uid} and sale_date >= ${since}
      group by sale_date`;
    for (const row of salesDays) {
      const hit = trend.find((t) => t.date === String(row.sale_date));
      if (hit) hit.total = num(row.total);
    }

    const incomeByDate: Record<string, number> = {};
    for (const item of income) incomeByDate[item.date] = (incomeByDate[item.date] ?? 0) + item.amount;
    const expenseByDate: Record<string, number> = {};
    for (const item of expenses) expenseByDate[item.date] = (expenseByDate[item.date] ?? 0) + item.amount;

    const unread = await sql<{ c: unknown }>`select count(*) as c from notifications where user_id = ${uid} and is_read = false`;

    return {
      settings,
      income,
      expenses,
      totalIncome,
      totalExpenses,
      salesProfit,
      cashNet,
      profit,
      monthRevenue,
      goalProgressPct,
      lowStock: lowStock.map((r) => ({
        product_name: r.product_name,
        quantity: num(r.quantity),
        unit: r.unit,
      })),
      salesTrend: trend,
      incomeByDate,
      expenseByDate,
      unreadNotifications: num(unread[0]?.c),
    };
  });

export const addIncome = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(z.object({ source: z.string().min(1), amount: z.number(), date: z.string() }))
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const date = data.date || todayISO();
    await sql`insert into income (user_id, source, amount, date) values (${context.userId}, ${data.source.trim()}, ${data.amount}, ${date})`;
  });

export const deleteIncome = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from income where id = ${data.id} and user_id = ${context.userId}`;
  });

export const addExpense = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      name: z.string().min(1),
      amount: z.number(),
      category: z.string(),
      date: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const date = data.date || todayISO();
    await sql`insert into expenses (user_id, name, amount, category, date) values (${context.userId}, ${data.name.trim()}, ${data.amount}, ${data.category}, ${date})`;
  });

export const deleteExpense = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from expenses where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listStock = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<StockRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from stock where user_id = ${context.userId} order by product_name`;
    return rows.map((r) => ({
      id: num(r.id),
      product_name: String(r.product_name),
      quantity: num(r.quantity),
      cost_price: num(r.cost_price),
      selling_price: num(r.selling_price),
      unit: String(r.unit ?? "pcs"),
    }));
  });

export const addStock = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      product_name: z.string().min(1),
      quantity: z.number(),
      cost_price: z.number(),
      selling_price: z.number(),
      unit: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`insert into stock (user_id, product_name, quantity, cost_price, selling_price, unit)
      values (${context.userId}, ${data.product_name.trim()}, ${data.quantity}, ${data.cost_price}, ${data.selling_price}, ${data.unit || "pcs"})`;
  });

export const updateStock = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      id: z.number(),
      product_name: z.string().min(1),
      quantity: z.number(),
      cost_price: z.number(),
      selling_price: z.number(),
      unit: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`update stock set product_name = ${data.product_name.trim()}, quantity = ${data.quantity},
      cost_price = ${data.cost_price}, selling_price = ${data.selling_price}, unit = ${data.unit || "pcs"}
      where id = ${data.id} and user_id = ${context.userId}`;
  });

export const deleteStock = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from stock where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listCustomers = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<CustomerRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from customers where user_id = ${context.userId} order by name`;
    const spend = await sql<{ customer_id: unknown; spent: unknown; orders: unknown }>`
      select customer_id, coalesce(sum(total_amount),0) as spent, count(*) as orders
      from sales where user_id = ${context.userId} and customer_id is not null
      group by customer_id`;
    const map = new Map<number, { spent: number; orders: number }>();
    for (const s of spend) map.set(num(s.customer_id), { spent: num(s.spent), orders: num(s.orders) });
    return rows.map((r) => {
      const id = num(r.id);
      const s = map.get(id);
      return {
        id,
        name: String(r.name),
        email: String(r.email ?? ""),
        phone: String(r.phone ?? ""),
        address: String(r.address ?? ""),
        notes: String(r.notes ?? ""),
        order_count: s?.orders ?? 0,
        total_spent: s?.spent ?? 0,
      };
    });
  });

export const addCustomer = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      name: z.string().min(1),
      email: z.string(),
      phone: z.string(),
      address: z.string(),
      notes: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`insert into customers (user_id, name, email, phone, address, notes)
      values (${context.userId}, ${data.name.trim()}, ${data.email}, ${data.phone}, ${data.address}, ${data.notes})`;
  });

export const updateCustomer = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      id: z.number(),
      name: z.string().min(1),
      email: z.string(),
      phone: z.string(),
      address: z.string(),
      notes: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`update customers set name = ${data.name.trim()}, email = ${data.email}, phone = ${data.phone},
      address = ${data.address}, notes = ${data.notes}
      where id = ${data.id} and user_id = ${context.userId}`;
  });

export const deleteCustomer = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from customers where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listSales = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<SaleRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from sales where user_id = ${context.userId} order by sale_date desc, id desc`;
    return rows.map((r) => ({
      id: num(r.id),
      stock_id: r.stock_id == null ? null : num(r.stock_id),
      product_name: String(r.product_name),
      quantity_sold: num(r.quantity_sold),
      selling_price_at_time: num(r.selling_price_at_time),
      total_amount: num(r.total_amount),
      profit: num(r.profit),
      sale_date: String(r.sale_date),
      customer_name: String(r.customer_name ?? ""),
      customer_email: String(r.customer_email ?? ""),
      customer_id: r.customer_id == null ? null : num(r.customer_id),
    }));
  });

export const addSale = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      stock_id: z.number(),
      quantity: z.number().positive(),
      customer_id: z.number().nullable(),
      customer_name: z.string(),
      customer_email: z.string(),
      date: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const uid = context.userId;
    const items = await sql<Record<string, unknown>>`select * from stock where id = ${data.stock_id} and user_id = ${uid}`;
    const item = items[0];
    if (!item) throw new Error("Product not found");
    const qty = num(item.quantity);
    if (data.quantity > qty) throw new Error("Not enough stock");
    const price = num(item.selling_price);
    const cost = num(item.cost_price);
    const total = data.quantity * price;
    const profit = data.quantity * (price - cost);
    let name = data.customer_name.trim();
    let email = data.customer_email.trim();
    if (data.customer_id) {
      const c = await sql<Record<string, unknown>>`select name, email from customers where id = ${data.customer_id} and user_id = ${uid}`;
      if (c[0]) {
        name = String(c[0].name);
        email = String(c[0].email ?? email);
      }
    }
    const date = data.date || todayISO();
    await sql`insert into sales (user_id, stock_id, product_name, quantity_sold, selling_price_at_time, total_amount, profit, sale_date, customer_name, customer_email, customer_id)
      values (${uid}, ${data.stock_id}, ${String(item.product_name)}, ${data.quantity}, ${price}, ${total}, ${profit}, ${date}, ${name}, ${email}, ${data.customer_id})`;
    await sql`update stock set quantity = quantity - ${data.quantity} where id = ${data.stock_id} and user_id = ${uid}`;
    const settings = await ensureSettings(sql, uid);
    const remaining = qty - data.quantity;
    if (remaining < settings.low_stock_threshold) {
      await notify(sql, uid, `${String(item.product_name)} is low (${remaining} ${String(item.unit ?? "pcs")} left).`, "stock");
    }
  });

export const deleteSale = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from sales where id = ${data.id} and user_id = ${context.userId}`;
    const sale = rows[0];
    if (!sale) return;
    if (sale.stock_id != null) {
      await sql`update stock set quantity = quantity + ${num(sale.quantity_sold)} where id = ${num(sale.stock_id)} and user_id = ${context.userId}`;
    }
    await sql`delete from sales where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listDocuments = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<DocumentRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from documents where user_id = ${context.userId} order by date desc, id desc`;
    return rows.map((r) => ({
      id: num(r.id),
      doc_type: String(r.doc_type),
      title: String(r.title),
      client: String(r.client),
      amount: r.amount == null ? null : num(r.amount),
      date: String(r.date),
      notes: String(r.notes ?? ""),
    }));
  });

export const addDocument = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      doc_type: z.string(),
      title: z.string().min(1),
      client: z.string().min(1),
      amount: z.number().nullable(),
      date: z.string(),
      notes: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const date = data.date || todayISO();
    await sql`insert into documents (user_id, doc_type, title, client, amount, date, notes)
      values (${context.userId}, ${data.doc_type}, ${data.title.trim()}, ${data.client.trim()}, ${data.amount}, ${date}, ${data.notes})`;
  });

export const deleteDocument = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from documents where id = ${data.id} and user_id = ${context.userId}`;
  });

export const generateDocumentCopy = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      doc_type: z.string(),
      title: z.string(),
      client: z.string(),
      amount: z.number().nullable(),
      notes: z.string(),
      business_name: z.string(),
    }),
  )
  .handler(async ({ data }) => {
    const apiKey = process.env.XAI_API_KEY;
    if (!apiKey) return { ok: false as const, error: "AI is not available right now." };
    const amountBit = data.amount != null ? ` for ${data.amount}` : "";
    const res = await fetch("https://api.x.ai/v1/chat/completions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: "grok-4.5",
        max_tokens: 500,
        messages: [
          {
            role: "user",
            content: `Write a professional ${data.doc_type} titled "${data.title || "business document"}" from ${data.business_name || "the business"} for ${data.client || "the client"}${amountBit}. Details: ${data.notes || "general business services"}. Keep it under 180 words, plain text, well structured. No markdown.`,
          },
        ],
      }),
    });
    if (!res.ok) return { ok: false as const, error: `Could not generate (${res.status}).` };
    const body = (await res.json()) as { choices?: { message?: { content?: string } }[] };
    return { ok: true as const, text: body.choices?.[0]?.message?.content ?? "" };
  });

export const listCash = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<CashRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from cash_books where user_id = ${context.userId} order by date desc, id desc`;
    return rows.map((r) => ({
      id: num(r.id),
      entry_type: String(r.entry_type),
      category: String(r.category),
      description: String(r.description ?? ""),
      amount: num(r.amount),
      date: String(r.date),
    }));
  });

export const addCash = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      entry_type: z.string(),
      category: z.string().min(1),
      description: z.string(),
      amount: z.number(),
      date: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const date = data.date || todayISO();
    await sql`insert into cash_books (user_id, entry_type, category, description, amount, date)
      values (${context.userId}, ${data.entry_type}, ${data.category.trim()}, ${data.description}, ${data.amount}, ${date})`;
  });

export const updateCash = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      id: z.number(),
      entry_type: z.string(),
      category: z.string().min(1),
      description: z.string(),
      amount: z.number(),
      date: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`update cash_books set entry_type = ${data.entry_type}, category = ${data.category.trim()},
      description = ${data.description}, amount = ${data.amount}, date = ${data.date}
      where id = ${data.id} and user_id = ${context.userId}`;
  });

export const deleteCash = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from cash_books where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listSwot = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<SwotRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from swot_analyses where user_id = ${context.userId} order by created_date desc, id desc`;
    return rows.map((r) => ({
      id: num(r.id),
      title: String(r.title),
      strengths: String(r.strengths ?? ""),
      weaknesses: String(r.weaknesses ?? ""),
      opportunities: String(r.opportunities ?? ""),
      threats: String(r.threats ?? ""),
      created_date: String(r.created_date),
    }));
  });

export const addSwot = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      title: z.string(),
      strengths: z.string(),
      weaknesses: z.string(),
      opportunities: z.string(),
      threats: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const title = data.title.trim() || `SWOT ${todayISO()}`;
    await sql`insert into swot_analyses (user_id, title, strengths, weaknesses, opportunities, threats, created_date)
      values (${context.userId}, ${title}, ${data.strengths}, ${data.weaknesses}, ${data.opportunities}, ${data.threats}, ${todayISO()})`;
  });

export const deleteSwot = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from swot_analyses where id = ${data.id} and user_id = ${context.userId}`;
  });

export const getPlan = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<PlanRow | null> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from business_plans where user_id = ${context.userId}`;
    const r = rows[0];
    if (!r) return null;
    return {
      business_name: String(r.business_name ?? ""),
      mission: String(r.mission ?? ""),
      products_services: String(r.products_services ?? ""),
      target_market: String(r.target_market ?? ""),
      marketing_strategy: String(r.marketing_strategy ?? ""),
      operations_plan: String(r.operations_plan ?? ""),
      financial_plan: String(r.financial_plan ?? ""),
      goals: String(r.goals ?? ""),
      updated_date: r.updated_date ? String(r.updated_date) : null,
    };
  });

export const savePlan = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      business_name: z.string(),
      mission: z.string(),
      products_services: z.string(),
      target_market: z.string(),
      marketing_strategy: z.string(),
      operations_plan: z.string(),
      financial_plan: z.string(),
      goals: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const today = todayISO();
    await sql`insert into business_plans (user_id, business_name, mission, products_services, target_market, marketing_strategy, operations_plan, financial_plan, goals, updated_date)
      values (${context.userId}, ${data.business_name}, ${data.mission}, ${data.products_services}, ${data.target_market}, ${data.marketing_strategy}, ${data.operations_plan}, ${data.financial_plan}, ${data.goals}, ${today})
      on conflict (user_id) do update set
        business_name = excluded.business_name,
        mission = excluded.mission,
        products_services = excluded.products_services,
        target_market = excluded.target_market,
        marketing_strategy = excluded.marketing_strategy,
        operations_plan = excluded.operations_plan,
        financial_plan = excluded.financial_plan,
        goals = excluded.goals,
        updated_date = excluded.updated_date`;
  });

export const listRecurring = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<RecurringRow[]> => {
    const sql = await getSql();
    await processRecurring(sql, context.userId);
    const rows = await sql<Record<string, unknown>>`select * from recurring_items where user_id = ${context.userId} order by active desc, next_run_date`;
    return rows.map((r) => ({
      id: num(r.id),
      item_type: String(r.item_type),
      name: String(r.name),
      amount: num(r.amount),
      category: String(r.category ?? ""),
      client: String(r.client ?? ""),
      frequency: String(r.frequency),
      next_run_date: String(r.next_run_date),
      active: Boolean(r.active),
    }));
  });

export const addRecurring = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      item_type: z.string(),
      name: z.string().min(1),
      amount: z.number(),
      category: z.string(),
      client: z.string(),
      frequency: z.string(),
      start_date: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const start = data.start_date || todayISO();
    await sql`insert into recurring_items (user_id, item_type, name, amount, category, client, frequency, next_run_date, active, created_date)
      values (${context.userId}, ${data.item_type}, ${data.name.trim()}, ${data.amount}, ${data.category}, ${data.client}, ${data.frequency}, ${start}, true, ${todayISO()})`;
  });

export const toggleRecurring = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`update recurring_items set active = not active where id = ${data.id} and user_id = ${context.userId}`;
  });

export const deleteRecurring = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from recurring_items where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listSuppliers = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<SupplierRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from suppliers where user_id = ${context.userId} order by name`;
    return rows.map((r) => ({
      id: num(r.id),
      name: String(r.name),
      email: String(r.email ?? ""),
      phone: String(r.phone ?? ""),
      address: String(r.address ?? ""),
      notes: String(r.notes ?? ""),
    }));
  });

export const addSupplier = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      name: z.string().min(1),
      email: z.string(),
      phone: z.string(),
      address: z.string(),
      notes: z.string(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`insert into suppliers (user_id, name, email, phone, address, notes)
      values (${context.userId}, ${data.name.trim()}, ${data.email}, ${data.phone}, ${data.address}, ${data.notes})`;
  });

export const deleteSupplier = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from suppliers where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listOrders = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<PurchaseOrderRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from purchase_orders where user_id = ${context.userId} order by order_date desc, id desc`;
    return rows.map((r) => ({
      id: num(r.id),
      supplier_id: r.supplier_id == null ? null : num(r.supplier_id),
      supplier_name: String(r.supplier_name ?? ""),
      item_description: String(r.item_description),
      quantity: num(r.quantity),
      unit_cost: num(r.unit_cost),
      total_cost: num(r.total_cost),
      status: String(r.status),
      order_date: String(r.order_date),
      expected_date: r.expected_date ? String(r.expected_date) : null,
      stock_id: r.stock_id == null ? null : num(r.stock_id),
    }));
  });

export const addOrder = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(
    z.object({
      supplier_id: z.number().nullable(),
      item_description: z.string().min(1),
      quantity: z.number().positive(),
      unit_cost: z.number(),
      expected_date: z.string(),
      stock_id: z.number().nullable(),
    }),
  )
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    let supplierName = "";
    if (data.supplier_id) {
      const s = await sql<{ name: string }>`select name from suppliers where id = ${data.supplier_id} and user_id = ${context.userId}`;
      supplierName = s[0]?.name ?? "";
    }
    const total = data.quantity * data.unit_cost;
    const expected = data.expected_date || null;
    await sql`insert into purchase_orders (user_id, supplier_id, supplier_name, item_description, quantity, unit_cost, total_cost, status, order_date, expected_date, stock_id)
      values (${context.userId}, ${data.supplier_id}, ${supplierName}, ${data.item_description.trim()}, ${data.quantity}, ${data.unit_cost}, ${total}, ${"pending"}, ${todayISO()}, ${expected}, ${data.stock_id})`;
  });

export const receiveOrder = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from purchase_orders where id = ${data.id} and user_id = ${context.userId}`;
    const po = rows[0];
    if (!po) throw new Error("Order not found");
    await sql`update purchase_orders set status = ${"received"} where id = ${data.id} and user_id = ${context.userId}`;
    if (po.stock_id != null) {
      await sql`update stock set quantity = quantity + ${num(po.quantity)} where id = ${num(po.stock_id)} and user_id = ${context.userId}`;
    }
    await notify(
      sql,
      context.userId,
      `Purchase order for "${String(po.item_description)}" marked received${po.stock_id != null ? " and added to stock" : ""}.`,
      "purchase_order",
    );
  });

export const deleteOrder = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from purchase_orders where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listBudgets = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<BudgetRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from budgets where user_id = ${context.userId} order by category`;
    const monthStart = todayISO().slice(0, 8) + "01";
    const result: BudgetRow[] = [];
    for (const r of rows) {
      const category = String(r.category);
      const spentRow = await sql<{ p: unknown }>`select coalesce(sum(amount),0) as p from expenses where user_id = ${context.userId} and category = ${category} and date >= ${monthStart}`;
      result.push({
        id: num(r.id),
        category,
        monthly_limit: num(r.monthly_limit),
        spent: num(spentRow[0]?.p),
      });
    }
    return result;
  });

export const saveBudget = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(z.object({ category: z.string(), monthly_limit: z.number() }))
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`insert into budgets (user_id, category, monthly_limit, created_date)
      values (${context.userId}, ${data.category}, ${data.monthly_limit}, ${todayISO()})
      on conflict (user_id, category) do update set monthly_limit = excluded.monthly_limit`;
  });

export const deleteBudget = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from budgets where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listNotifications = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<NotificationRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from notifications where user_id = ${context.userId} order by created_date desc limit 100`;
    await sql`update notifications set is_read = true where user_id = ${context.userId} and is_read = false`;
    return rows.map((r) => ({
      id: num(r.id),
      message: String(r.message),
      category: String(r.category),
      is_read: Boolean(r.is_read),
      created_date: String(r.created_date),
    }));
  });

export const clearNotifications = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    const sql = await getSql();
    await sql`delete from notifications where user_id = ${context.userId}`;
  });

export const unreadCount = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    const sql = await getSql();
    const rows = await sql<{ c: unknown }>`select count(*) as c from notifications where user_id = ${context.userId} and is_read = false`;
    return num(rows[0]?.c);
  });

export const listTeam = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<TeamRow[]> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select * from team_members where user_id = ${context.userId} order by name`;
    return rows.map((r) => ({
      id: num(r.id),
      name: String(r.name),
      email: String(r.email ?? ""),
      role: String(r.role ?? "Staff"),
    }));
  });

export const addTeam = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(z.object({ name: z.string().min(1), email: z.string(), role: z.string() }))
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`insert into team_members (user_id, name, email, role) values (${context.userId}, ${data.name.trim()}, ${data.email}, ${data.role || "Staff"})`;
  });

export const deleteTeam = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .validator(idSchema)
  .handler(async ({ context, data }) => {
    const sql = await getSql();
    await sql`delete from team_members where id = ${data.id} and user_id = ${context.userId}`;
  });

export const listActivity = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }): Promise<{ logs: ActivityRow[]; todayCount: number }> => {
    const sql = await getSql();
    const rows = await sql<Record<string, unknown>>`select id, username, login_time from user_activity where user_id = ${context.userId} order by login_time desc limit 50`;
    const today = todayISO();
    const count = await sql<{ c: unknown }>`select count(*) as c from user_activity where user_id = ${context.userId} and login_time::date = ${today}`;
    return {
      logs: rows.map((r) => ({
        id: num(r.id),
        username: String(r.username),
        login_time: String(r.login_time),
      })),
      todayCount: num(count[0]?.c),
    };
  });

export const getReports = createServerFn({ method: "GET" })
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    const sql = await getSql();
    const uid = context.userId;
    const months: string[] = [];
    const start = todayISO().slice(0, 8) + "01";
    for (let i = 5; i >= 0; i--) months.push(addMonths(start, -i).slice(0, 7));
    const monthlyIncome: Record<string, number> = Object.fromEntries(months.map((m) => [m, 0]));
    const monthlyExpenses: Record<string, number> = Object.fromEntries(months.map((m) => [m, 0]));
    const monthlyProfit: Record<string, number> = Object.fromEntries(months.map((m) => [m, 0]));
    const inc = await sql<{ date: string; amount: unknown }>`select date, amount from income where user_id = ${uid}`;
    for (const r of inc) {
      const k = monthKey(String(r.date));
      if (k in monthlyIncome) monthlyIncome[k] += num(r.amount);
    }
    const exp = await sql<{ date: string; amount: unknown }>`select date, amount from expenses where user_id = ${uid}`;
    for (const r of exp) {
      const k = monthKey(String(r.date));
      if (k in monthlyExpenses) monthlyExpenses[k] += num(r.amount);
    }
    const sp = await sql<{ sale_date: string; profit: unknown }>`select sale_date, profit from sales where user_id = ${uid}`;
    const salesProfit: Record<string, number> = Object.fromEntries(months.map((m) => [m, 0]));
    for (const r of sp) {
      const k = monthKey(String(r.sale_date));
      if (k in salesProfit) salesProfit[k] += num(r.profit);
    }
    for (const m of months) {
      monthlyProfit[m] = (monthlyIncome[m] ?? 0) - (monthlyExpenses[m] ?? 0) + (salesProfit[m] ?? 0);
    }
    const topProducts = await sql<{ product_name: string; revenue: unknown; profit: unknown; units: unknown }>`
      select product_name, sum(total_amount) as revenue, sum(profit) as profit, sum(quantity_sold) as units
      from sales where user_id = ${uid}
      group by product_name order by sum(total_amount) desc limit 5`;
    const topCustomers = await sql<{ customer_name: string; spent: unknown; orders: unknown }>`
      select coalesce(nullif(customer_name, ''), 'Walk-in') as customer_name,
             sum(total_amount) as spent, count(*) as orders
      from sales where user_id = ${uid}
      group by coalesce(nullif(customer_name, ''), 'Walk-in')
      order by sum(total_amount) desc limit 5`;
    return {
      months,
      monthlyIncome,
      monthlyExpenses,
      monthlyProfit,
      topProducts: topProducts.map((p) => ({
        product_name: p.product_name,
        revenue: num(p.revenue),
        profit: num(p.profit),
        units: num(p.units),
      })),
      topCustomers: topCustomers.map((c) => ({
        customer_name: c.customer_name,
        spent: num(c.spent),
        orders: num(c.orders),
      })),
    };
  });

export const seedSample = createServerFn({ method: "POST" })
  .middleware([authMiddleware])
  .handler(async ({ context }) => {
    const sql = await getSql();
    const uid = context.userId;
    await ensureSettings(sql, uid);
    await sql`update settings set business_name = ${"KAZE Traders"}, monthly_revenue_goal = ${8000}, currency_symbol = ${"$"} where user_id = ${uid} and business_name = ${""}`;

    const existing = await sql<{ c: unknown }>`select count(*) as c from stock where user_id = ${uid}`;
    if (num(existing[0]?.c) > 0) return { seeded: false };

    const products = [
      ["Rice 25kg", 40, 18, 24, "bag"],
      ["Cooking oil 2L", 60, 4.5, 6.2, "btl"],
      ["Sugar 1kg", 80, 1.1, 1.6, "pkt"],
      ["Bar soap", 120, 0.6, 1.0, "pcs"],
      ["Maize meal 10kg", 35, 7.5, 10, "bag"],
    ] as const;
    for (const p of products) {
      await sql`insert into stock (user_id, product_name, quantity, cost_price, selling_price, unit)
        values (${uid}, ${p[0]}, ${p[1]}, ${p[2]}, ${p[3]}, ${p[4]})`;
    }
    const stock = await sql<{ id: number; product_name: string; cost_price: unknown; selling_price: unknown }>`select id, product_name, cost_price, selling_price from stock where user_id = ${uid}`;
    await sql`insert into customers (user_id, name, email, phone, address) values
      (${uid}, ${"Lusaka Grocers"}, ${"orders@lusakagrocers.example"}, ${"+260 97 111 0001"}, ${"Cairo Road"}),
      (${uid}, ${"Chilenje Market Stall"}, ${""}, ${"+260 96 222 0002"}, ${"Chilenje"}),
      (${uid}, ${"Northmead Cafe"}, ${"hello@northmead.example"}, ${""}, ${"Northmead"})`;
    const customers = await sql<{ id: number; name: string; email: string }>`select id, name, email from customers where user_id = ${uid}`;

    const today = new Date();
    for (let i = 0; i < 8; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const date = d.toISOString().slice(0, 10);
      const item = stock[i % stock.length];
      if (!item) continue;
      const cust = customers[i % customers.length];
      const qty = 1 + (i % 4);
      const price = num(item.selling_price);
      const cost = num(item.cost_price);
      await sql`insert into sales (user_id, stock_id, product_name, quantity_sold, selling_price_at_time, total_amount, profit, sale_date, customer_name, customer_email, customer_id)
        values (${uid}, ${item.id}, ${item.product_name}, ${qty}, ${price}, ${qty * price}, ${qty * (price - cost)}, ${date}, ${cust?.name ?? ""}, ${cust?.email ?? ""}, ${cust?.id ?? null})`;
      await sql`update stock set quantity = quantity - ${qty} where id = ${item.id} and user_id = ${uid}`;
    }

    await sql`insert into income (user_id, source, amount, date) values
      (${uid}, ${"Wholesale delivery"}, ${420}, ${todayISO()}),
      (${uid}, ${"Cafe contract"}, ${180}, ${addMonths(todayISO(), 0)})`;
    await sql`insert into expenses (user_id, name, amount, category, date) values
      (${uid}, ${"Shop rent"}, ${350}, ${"Rent"}, ${todayISO()}),
      (${uid}, ${"Fuel"}, ${48}, ${"Transport"}, ${todayISO()})`;
    await sql`insert into cash_books (user_id, entry_type, category, description, amount, date) values
      (${uid}, ${"in"}, ${"Till"}, ${"Opening float"}, ${200}, ${todayISO()}),
      (${uid}, ${"out"}, ${"Change"}, ${"Bank deposit"}, ${150}, ${todayISO()})`;
    await sql`insert into suppliers (user_id, name, email, phone) values
      (${uid}, ${"National Milling"}, ${"sales@nmc.example"}, ${"+260 21 111 0000"})`;
    await sql`insert into budgets (user_id, category, monthly_limit, created_date) values
      (${uid}, ${"Rent"}, ${400}, ${todayISO()}),
      (${uid}, ${"Transport"}, ${120}, ${todayISO()})`;
    await notify(sql, uid, "Sample business data loaded. Explore the dashboard, stock, and sales.", "info");
    return { seeded: true };
  });
