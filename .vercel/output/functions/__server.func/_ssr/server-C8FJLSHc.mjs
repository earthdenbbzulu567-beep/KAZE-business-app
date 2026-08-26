import { i as TSS_SERVER_FUNCTION, r as createServerFn } from "./ssr.mjs";
import { Jt as object, Ut as boolean, Zt as string, qt as number } from "../_libs/@better-auth/core+[...].mjs";
import { t as authMiddleware } from "./middleware-BX86ISIa.mjs";
import { a as monthKey, c as todayISO, n as addMonths, o as num } from "./format-DhlBBqua.mjs";
import { r as getSql } from "./db-B7DXj0Zy.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/server-C8FJLSHc.js
var createServerRpc = (serverFnMeta, splitImportFn) => {
	const url = "/_serverFn/" + serverFnMeta.id;
	return Object.assign(splitImportFn, {
		url,
		serverFnMeta,
		[TSS_SERVER_FUNCTION]: true
	});
};
async function ensureSettings(sql, userId) {
	await sql`insert into settings (user_id) values (${userId}) on conflict (user_id) do nothing`;
	const r = (await sql`select * from settings where user_id = ${userId}`)[0] ?? {};
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
		tutorial_completed: Boolean(r.tutorial_completed)
	};
}
async function notify(sql, userId, message, category = "info") {
	await sql`insert into notifications (user_id, message, category) values (${userId}, ${message}, ${category})`;
}
function advance(dateStr, frequency) {
	if (frequency === "weekly") {
		const dt = /* @__PURE__ */ new Date(`${dateStr}T00:00:00Z`);
		dt.setUTCDate(dt.getUTCDate() + 7);
		return dt.toISOString().slice(0, 10);
	}
	if (frequency === "monthly") return addMonths(dateStr, 1);
	if (frequency === "quarterly") return addMonths(dateStr, 3);
	if (frequency === "yearly") return addMonths(dateStr, 12);
	return dateStr;
}
async function processRecurring(sql, userId) {
	const today = todayISO();
	const due = await sql`select id, item_type, name, amount, category, client, frequency, next_run_date
     from recurring_items
     where user_id = ${userId} and active = true and next_run_date <= ${today}`;
	for (const item of due) {
		const amount = num(item.amount);
		if (item.item_type === "expense") await sql`insert into expenses (user_id, name, amount, category, date)
        values (${userId}, ${item.name}, ${amount}, ${item.category || "Other"}, ${today})`;
		else await sql`insert into documents (user_id, doc_type, title, client, amount, date, notes)
        values (${userId}, ${"invoice"}, ${item.name}, ${item.client || "Recurring client"}, ${amount}, ${today}, ${"Auto-generated from a recurring invoice."})`;
		await sql`update recurring_items set next_run_date = ${advance(item.next_run_date, item.frequency)} where id = ${item.id} and user_id = ${userId}`;
		await notify(sql, userId, `Recurring ${item.item_type} "${item.name}" (${amount.toFixed(2)}) was generated.`, "recurring");
	}
}
var idSchema = object({ id: number() });
var getSettings_createServerFn_handler = createServerRpc({
	id: "b2728d6ed29cd46c4adcc73c2d2e8fd14f5de2f553fd71ea61030ca0bd411013",
	name: "getSettings",
	filename: "src/lib/kaze/server.ts"
}, (opts) => getSettings.__executeServer(opts));
var getSettings = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(getSettings_createServerFn_handler, async ({ context }) => {
	return ensureSettings(await getSql(), context.userId);
});
var saveSettings_createServerFn_handler = createServerRpc({
	id: "197c947cfcbb09b32a5abc2e8489f57099f75ef2a27299ff7cec31536fc22f02",
	name: "saveSettings",
	filename: "src/lib/kaze/server.ts"
}, (opts) => saveSettings.__executeServer(opts));
var saveSettings = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	business_name: string(),
	currency_code: string(),
	currency_symbol: string(),
	tax_rate: number(),
	monthly_revenue_goal: number(),
	low_stock_threshold: number(),
	theme: string(),
	font_size: string(),
	default_chart_type: string(),
	animations_enabled: boolean(),
	show_low_stock_widget: boolean(),
	show_sales_trend: boolean(),
	about_text: string()
})).handler(saveSettings_createServerFn_handler, async ({ context, data }) => {
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
var dismissTutorial_createServerFn_handler = createServerRpc({
	id: "c4544171e9c329f1fddb21c3557b512a7361110fbf71d3b20e73877b88c488a5",
	name: "dismissTutorial",
	filename: "src/lib/kaze/server.ts"
}, (opts) => dismissTutorial.__executeServer(opts));
var dismissTutorial = createServerFn({ method: "POST" }).middleware([authMiddleware]).handler(dismissTutorial_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	await ensureSettings(sql, context.userId);
	await sql`update settings set tutorial_completed = true where user_id = ${context.userId}`;
});
var recordActivity_createServerFn_handler = createServerRpc({
	id: "f6add793728cf9e57d79d44791fc0bb417505a6f658013e999a33ba1e87ca5f3",
	name: "recordActivity",
	filename: "src/lib/kaze/server.ts"
}, (opts) => recordActivity.__executeServer(opts));
var recordActivity = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({ username: string() })).handler(recordActivity_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`insert into user_activity (user_id, username) values (${context.userId}, ${data.username})`;
});
var getDashboard_createServerFn_handler = createServerRpc({
	id: "804167cb54f47c7583161fe8ff5ffbcc99ad83696b887b0abcfe3413b73b2f15",
	name: "getDashboard",
	filename: "src/lib/kaze/server.ts"
}, (opts) => getDashboard.__executeServer(opts));
var getDashboard = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(getDashboard_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	const uid = context.userId;
	const settings = await ensureSettings(sql, uid);
	await processRecurring(sql, uid);
	const incomeRows = await sql`select id, source, amount, date from income where user_id = ${uid} order by date desc, id desc`;
	const expenseRows = await sql`select id, name, amount, category, date from expenses where user_id = ${uid} order by date desc, id desc`;
	const income = incomeRows.map((r) => ({
		id: num(r.id),
		source: String(r.source),
		amount: num(r.amount),
		date: String(r.date)
	}));
	const expenses = expenseRows.map((r) => ({
		id: num(r.id),
		name: String(r.name),
		amount: num(r.amount),
		category: String(r.category),
		date: String(r.date)
	}));
	const totalIncome = income.reduce((s, i) => s + i.amount, 0);
	const totalExpenses = expenses.reduce((s, e) => s + e.amount, 0);
	const profitRow = await sql`select coalesce(sum(profit),0) as p from sales where user_id = ${uid}`;
	const salesProfit = num(profitRow[0]?.p);
	const cashIn = await sql`select coalesce(sum(amount),0) as p from cash_books where user_id = ${uid} and entry_type = ${"in"}`;
	const cashOut = await sql`select coalesce(sum(amount),0) as p from cash_books where user_id = ${uid} and entry_type = ${"out"}`;
	const cashNet = num(cashIn[0]?.p) - num(cashOut[0]?.p);
	const profit = totalIncome - totalExpenses + salesProfit + cashNet;
	const monthRev = await sql`select coalesce(sum(total_amount),0) as p from sales where user_id = ${uid} and sale_date >= ${todayISO().slice(0, 8) + "01"}`;
	const monthRevenue = num(monthRev[0]?.p);
	const goalProgressPct = settings.monthly_revenue_goal ? Math.min(100, Math.round(monthRevenue / settings.monthly_revenue_goal * 1e3) / 10) : 0;
	const lowStock = await sql`
      select product_name, quantity, unit from stock
      where user_id = ${uid} and quantity < ${settings.low_stock_threshold}
      order by quantity asc`;
	const trend = [];
	for (let i = 6; i >= 0; i--) {
		const d = /* @__PURE__ */ new Date();
		d.setDate(d.getDate() - i);
		const key = d.toISOString().slice(0, 10);
		trend.push({
			date: key,
			total: 0
		});
	}
	const salesDays = await sql`
      select sale_date, sum(total_amount) as total from sales
      where user_id = ${uid} and sale_date >= ${trend[0]?.date ?? todayISO()}
      group by sale_date`;
	for (const row of salesDays) {
		const hit = trend.find((t) => t.date === String(row.sale_date));
		if (hit) hit.total = num(row.total);
	}
	const incomeByDate = {};
	for (const item of income) incomeByDate[item.date] = (incomeByDate[item.date] ?? 0) + item.amount;
	const expenseByDate = {};
	for (const item of expenses) expenseByDate[item.date] = (expenseByDate[item.date] ?? 0) + item.amount;
	const unread = await sql`select count(*) as c from notifications where user_id = ${uid} and is_read = false`;
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
			unit: r.unit
		})),
		salesTrend: trend,
		incomeByDate,
		expenseByDate,
		unreadNotifications: num(unread[0]?.c)
	};
});
var addIncome_createServerFn_handler = createServerRpc({
	id: "15a2310a56c9bcf5c3b5b280b3345b339905bd501bb9e8bd7c940b3fa05f7993",
	name: "addIncome",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addIncome.__executeServer(opts));
var addIncome = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	source: string().min(1),
	amount: number(),
	date: string()
})).handler(addIncome_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const date = data.date || todayISO();
	await sql`insert into income (user_id, source, amount, date) values (${context.userId}, ${data.source.trim()}, ${data.amount}, ${date})`;
});
var deleteIncome_createServerFn_handler = createServerRpc({
	id: "5ba71790ace9e363e4b6534e0beab7b34898635af30043c9c886c2da8678d703",
	name: "deleteIncome",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteIncome.__executeServer(opts));
var deleteIncome = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteIncome_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from income where id = ${data.id} and user_id = ${context.userId}`;
});
var addExpense_createServerFn_handler = createServerRpc({
	id: "00a6080192a254f1a5122b6424fcbe6498757bb2e381e7d0fe8f6c1855f09bea",
	name: "addExpense",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addExpense.__executeServer(opts));
var addExpense = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	amount: number(),
	category: string(),
	date: string()
})).handler(addExpense_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const date = data.date || todayISO();
	await sql`insert into expenses (user_id, name, amount, category, date) values (${context.userId}, ${data.name.trim()}, ${data.amount}, ${data.category}, ${date})`;
});
var deleteExpense_createServerFn_handler = createServerRpc({
	id: "fa926866b83f0d180896a3cf274500aa20707c721dfc4b52403503a298519ad1",
	name: "deleteExpense",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteExpense.__executeServer(opts));
var deleteExpense = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteExpense_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from expenses where id = ${data.id} and user_id = ${context.userId}`;
});
var listStock_createServerFn_handler = createServerRpc({
	id: "89e653a16245fd3e4e015da180b794d26de30d5d7d55679f759455813682c403",
	name: "listStock",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listStock.__executeServer(opts));
var listStock = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listStock_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from stock where user_id = ${context.userId} order by product_name`).map((r) => ({
		id: num(r.id),
		product_name: String(r.product_name),
		quantity: num(r.quantity),
		cost_price: num(r.cost_price),
		selling_price: num(r.selling_price),
		unit: String(r.unit ?? "pcs")
	}));
});
var addStock_createServerFn_handler = createServerRpc({
	id: "3a4bc15943b8a466f98d5dfcee26a5d10d3a4e3740b08b82b18dbd3fed73d4e1",
	name: "addStock",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addStock.__executeServer(opts));
var addStock = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	product_name: string().min(1),
	quantity: number(),
	cost_price: number(),
	selling_price: number(),
	unit: string()
})).handler(addStock_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`insert into stock (user_id, product_name, quantity, cost_price, selling_price, unit)
      values (${context.userId}, ${data.product_name.trim()}, ${data.quantity}, ${data.cost_price}, ${data.selling_price}, ${data.unit || "pcs"})`;
});
var updateStock_createServerFn_handler = createServerRpc({
	id: "fbe8a5f089e663d7d8af1cf959883f8f69ac10d08d477b29aa7e212f976bfbe1",
	name: "updateStock",
	filename: "src/lib/kaze/server.ts"
}, (opts) => updateStock.__executeServer(opts));
var updateStock = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	id: number(),
	product_name: string().min(1),
	quantity: number(),
	cost_price: number(),
	selling_price: number(),
	unit: string()
})).handler(updateStock_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`update stock set product_name = ${data.product_name.trim()}, quantity = ${data.quantity},
      cost_price = ${data.cost_price}, selling_price = ${data.selling_price}, unit = ${data.unit || "pcs"}
      where id = ${data.id} and user_id = ${context.userId}`;
});
var deleteStock_createServerFn_handler = createServerRpc({
	id: "e97ca9a309d5d0e1a7c10f8ecd72c6a9df2406d1c75ef03a9adb65a0094f267d",
	name: "deleteStock",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteStock.__executeServer(opts));
var deleteStock = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteStock_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from stock where id = ${data.id} and user_id = ${context.userId}`;
});
var listCustomers_createServerFn_handler = createServerRpc({
	id: "6ba533b064b355145b796fe242f14aa1deaedd4fd215bc955d66b11262014774",
	name: "listCustomers",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listCustomers.__executeServer(opts));
var listCustomers = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listCustomers_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	const rows = await sql`select * from customers where user_id = ${context.userId} order by name`;
	const spend = await sql`
      select customer_id, coalesce(sum(total_amount),0) as spent, count(*) as orders
      from sales where user_id = ${context.userId} and customer_id is not null
      group by customer_id`;
	const map = /* @__PURE__ */ new Map();
	for (const s of spend) map.set(num(s.customer_id), {
		spent: num(s.spent),
		orders: num(s.orders)
	});
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
			total_spent: s?.spent ?? 0
		};
	});
});
var addCustomer_createServerFn_handler = createServerRpc({
	id: "be01efb345bb72434141ad71f54e02eb4f2c1747989c54c4be426240ce3412d7",
	name: "addCustomer",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addCustomer.__executeServer(opts));
var addCustomer = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	email: string(),
	phone: string(),
	address: string(),
	notes: string()
})).handler(addCustomer_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`insert into customers (user_id, name, email, phone, address, notes)
      values (${context.userId}, ${data.name.trim()}, ${data.email}, ${data.phone}, ${data.address}, ${data.notes})`;
});
var updateCustomer_createServerFn_handler = createServerRpc({
	id: "fa69a5a9ece46fb7bf931c5eaa265c9739ad29db2c7c1a769c66e87f5d1509ae",
	name: "updateCustomer",
	filename: "src/lib/kaze/server.ts"
}, (opts) => updateCustomer.__executeServer(opts));
var updateCustomer = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	id: number(),
	name: string().min(1),
	email: string(),
	phone: string(),
	address: string(),
	notes: string()
})).handler(updateCustomer_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`update customers set name = ${data.name.trim()}, email = ${data.email}, phone = ${data.phone},
      address = ${data.address}, notes = ${data.notes}
      where id = ${data.id} and user_id = ${context.userId}`;
});
var deleteCustomer_createServerFn_handler = createServerRpc({
	id: "eec968cdafb4c106e8ef245a64c0893ab5b9f4983124de89ed016abbfca44f61",
	name: "deleteCustomer",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteCustomer.__executeServer(opts));
var deleteCustomer = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteCustomer_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from customers where id = ${data.id} and user_id = ${context.userId}`;
});
var listSales_createServerFn_handler = createServerRpc({
	id: "ad0727229055a952b813d85cf861accfaae30f4d7fa7f5ab1d6e767a3a10e671",
	name: "listSales",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listSales.__executeServer(opts));
var listSales = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listSales_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from sales where user_id = ${context.userId} order by sale_date desc, id desc`).map((r) => ({
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
		customer_id: r.customer_id == null ? null : num(r.customer_id)
	}));
});
var addSale_createServerFn_handler = createServerRpc({
	id: "cabcd598009d5f0f46e28ec6d13ae25e3b4c343c2937b23492bb99681d20bab5",
	name: "addSale",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addSale.__executeServer(opts));
var addSale = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	stock_id: number(),
	quantity: number().positive(),
	customer_id: number().nullable(),
	customer_name: string(),
	customer_email: string(),
	date: string()
})).handler(addSale_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const uid = context.userId;
	const item = (await sql`select * from stock where id = ${data.stock_id} and user_id = ${uid}`)[0];
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
		const c = await sql`select name, email from customers where id = ${data.customer_id} and user_id = ${uid}`;
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
	if (remaining < settings.low_stock_threshold) await notify(sql, uid, `${String(item.product_name)} is low (${remaining} ${String(item.unit ?? "pcs")} left).`, "stock");
});
var deleteSale_createServerFn_handler = createServerRpc({
	id: "e00e09a81b1f5e4b7602c8e23e8b2a141b8384c0607ee1bea4e74c133f6bb57e",
	name: "deleteSale",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteSale.__executeServer(opts));
var deleteSale = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteSale_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const sale = (await sql`select * from sales where id = ${data.id} and user_id = ${context.userId}`)[0];
	if (!sale) return;
	if (sale.stock_id != null) await sql`update stock set quantity = quantity + ${num(sale.quantity_sold)} where id = ${num(sale.stock_id)} and user_id = ${context.userId}`;
	await sql`delete from sales where id = ${data.id} and user_id = ${context.userId}`;
});
var listDocuments_createServerFn_handler = createServerRpc({
	id: "49e342682191c31d785c2806065d168c1f4d841e21d6e18256b76ecf536713ce",
	name: "listDocuments",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listDocuments.__executeServer(opts));
var listDocuments = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listDocuments_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from documents where user_id = ${context.userId} order by date desc, id desc`).map((r) => ({
		id: num(r.id),
		doc_type: String(r.doc_type),
		title: String(r.title),
		client: String(r.client),
		amount: r.amount == null ? null : num(r.amount),
		date: String(r.date),
		notes: String(r.notes ?? "")
	}));
});
var addDocument_createServerFn_handler = createServerRpc({
	id: "438ea31559e1929e58403333243a99bc8b165b5d58a2425c02aaa24b60d82cfc",
	name: "addDocument",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addDocument.__executeServer(opts));
var addDocument = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	doc_type: string(),
	title: string().min(1),
	client: string().min(1),
	amount: number().nullable(),
	date: string(),
	notes: string()
})).handler(addDocument_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const date = data.date || todayISO();
	await sql`insert into documents (user_id, doc_type, title, client, amount, date, notes)
      values (${context.userId}, ${data.doc_type}, ${data.title.trim()}, ${data.client.trim()}, ${data.amount}, ${date}, ${data.notes})`;
});
var deleteDocument_createServerFn_handler = createServerRpc({
	id: "47fab243c01fc195253186954cb6df5d43d1f18b0ea90dcb5346cbcfe24e4460",
	name: "deleteDocument",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteDocument.__executeServer(opts));
var deleteDocument = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteDocument_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from documents where id = ${data.id} and user_id = ${context.userId}`;
});
var generateDocumentCopy_createServerFn_handler = createServerRpc({
	id: "8fde8edccc074746d396b28c1ca62f890227a45f82a709ec3b23d4e66710d710",
	name: "generateDocumentCopy",
	filename: "src/lib/kaze/server.ts"
}, (opts) => generateDocumentCopy.__executeServer(opts));
var generateDocumentCopy = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	doc_type: string(),
	title: string(),
	client: string(),
	amount: number().nullable(),
	notes: string(),
	business_name: string()
})).handler(generateDocumentCopy_createServerFn_handler, async ({ data }) => {
	const apiKey = process.env.XAI_API_KEY;
	if (!apiKey) return {
		ok: false,
		error: "AI is not available right now."
	};
	const amountBit = data.amount != null ? ` for ${data.amount}` : "";
	const res = await fetch("https://api.x.ai/v1/chat/completions", {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `Bearer ${apiKey}`
		},
		body: JSON.stringify({
			model: "grok-4.5",
			max_tokens: 500,
			messages: [{
				role: "user",
				content: `Write a professional ${data.doc_type} titled "${data.title || "business document"}" from ${data.business_name || "the business"} for ${data.client || "the client"}${amountBit}. Details: ${data.notes || "general business services"}. Keep it under 180 words, plain text, well structured. No markdown.`
			}]
		})
	});
	if (!res.ok) return {
		ok: false,
		error: `Could not generate (${res.status}).`
	};
	return {
		ok: true,
		text: (await res.json()).choices?.[0]?.message?.content ?? ""
	};
});
var listCash_createServerFn_handler = createServerRpc({
	id: "966810d31760408e061a13fbdcfd746dd62a9d575f4f3032e2eca5852d379e32",
	name: "listCash",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listCash.__executeServer(opts));
var listCash = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listCash_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from cash_books where user_id = ${context.userId} order by date desc, id desc`).map((r) => ({
		id: num(r.id),
		entry_type: String(r.entry_type),
		category: String(r.category),
		description: String(r.description ?? ""),
		amount: num(r.amount),
		date: String(r.date)
	}));
});
var addCash_createServerFn_handler = createServerRpc({
	id: "c6dd35eec4291b9f73bee78f3744f58611f18c5f24721fbe7fcf3cfb231a93f4",
	name: "addCash",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addCash.__executeServer(opts));
var addCash = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	entry_type: string(),
	category: string().min(1),
	description: string(),
	amount: number(),
	date: string()
})).handler(addCash_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const date = data.date || todayISO();
	await sql`insert into cash_books (user_id, entry_type, category, description, amount, date)
      values (${context.userId}, ${data.entry_type}, ${data.category.trim()}, ${data.description}, ${data.amount}, ${date})`;
});
var updateCash_createServerFn_handler = createServerRpc({
	id: "b7b933efbfb0d570d3d006c78fec02c6203651cf4ffa7d7724c53d4605f237df",
	name: "updateCash",
	filename: "src/lib/kaze/server.ts"
}, (opts) => updateCash.__executeServer(opts));
var updateCash = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	id: number(),
	entry_type: string(),
	category: string().min(1),
	description: string(),
	amount: number(),
	date: string()
})).handler(updateCash_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`update cash_books set entry_type = ${data.entry_type}, category = ${data.category.trim()},
      description = ${data.description}, amount = ${data.amount}, date = ${data.date}
      where id = ${data.id} and user_id = ${context.userId}`;
});
var deleteCash_createServerFn_handler = createServerRpc({
	id: "de3feafd742dd141c0e6d76c0f68e6c0e150b2e7fb7fe8d39100974e937a3313",
	name: "deleteCash",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteCash.__executeServer(opts));
var deleteCash = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteCash_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from cash_books where id = ${data.id} and user_id = ${context.userId}`;
});
var listSwot_createServerFn_handler = createServerRpc({
	id: "3576ab40e8731c545c1c98af4a9df667680294d572604bf3593e14a619a6a26c",
	name: "listSwot",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listSwot.__executeServer(opts));
var listSwot = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listSwot_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from swot_analyses where user_id = ${context.userId} order by created_date desc, id desc`).map((r) => ({
		id: num(r.id),
		title: String(r.title),
		strengths: String(r.strengths ?? ""),
		weaknesses: String(r.weaknesses ?? ""),
		opportunities: String(r.opportunities ?? ""),
		threats: String(r.threats ?? ""),
		created_date: String(r.created_date)
	}));
});
var addSwot_createServerFn_handler = createServerRpc({
	id: "1f656aba59ea3abacfb7c2bc00c575b0542869b25b155ae5d76be88a8cdd62fa",
	name: "addSwot",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addSwot.__executeServer(opts));
var addSwot = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	title: string(),
	strengths: string(),
	weaknesses: string(),
	opportunities: string(),
	threats: string()
})).handler(addSwot_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const title = data.title.trim() || `SWOT ${todayISO()}`;
	await sql`insert into swot_analyses (user_id, title, strengths, weaknesses, opportunities, threats, created_date)
      values (${context.userId}, ${title}, ${data.strengths}, ${data.weaknesses}, ${data.opportunities}, ${data.threats}, ${todayISO()})`;
});
var deleteSwot_createServerFn_handler = createServerRpc({
	id: "0cd6cd5c27dae72cc0b7a74ef9affa0fff2649219c3c6411b63dd880da092849",
	name: "deleteSwot",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteSwot.__executeServer(opts));
var deleteSwot = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteSwot_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from swot_analyses where id = ${data.id} and user_id = ${context.userId}`;
});
var getPlan_createServerFn_handler = createServerRpc({
	id: "89d92bb482714f629b80bac98e5389c035cc96d51941741202a0b03fca13219c",
	name: "getPlan",
	filename: "src/lib/kaze/server.ts"
}, (opts) => getPlan.__executeServer(opts));
var getPlan = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(getPlan_createServerFn_handler, async ({ context }) => {
	const r = (await (await getSql())`select * from business_plans where user_id = ${context.userId}`)[0];
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
		updated_date: r.updated_date ? String(r.updated_date) : null
	};
});
var savePlan_createServerFn_handler = createServerRpc({
	id: "56d71b1c08bb5b67c63a91b99c9d1377b92bc8db6038c78fac5381de9e1658fc",
	name: "savePlan",
	filename: "src/lib/kaze/server.ts"
}, (opts) => savePlan.__executeServer(opts));
var savePlan = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	business_name: string(),
	mission: string(),
	products_services: string(),
	target_market: string(),
	marketing_strategy: string(),
	operations_plan: string(),
	financial_plan: string(),
	goals: string()
})).handler(savePlan_createServerFn_handler, async ({ context, data }) => {
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
var listRecurring_createServerFn_handler = createServerRpc({
	id: "7085d8d704f3d23964144e522f355aa20fc8952a1c285339c7f30f75c994eb0f",
	name: "listRecurring",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listRecurring.__executeServer(opts));
var listRecurring = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listRecurring_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	await processRecurring(sql, context.userId);
	return (await sql`select * from recurring_items where user_id = ${context.userId} order by active desc, next_run_date`).map((r) => ({
		id: num(r.id),
		item_type: String(r.item_type),
		name: String(r.name),
		amount: num(r.amount),
		category: String(r.category ?? ""),
		client: String(r.client ?? ""),
		frequency: String(r.frequency),
		next_run_date: String(r.next_run_date),
		active: Boolean(r.active)
	}));
});
var addRecurring_createServerFn_handler = createServerRpc({
	id: "93a5e17f27f7131eaefda74bc1eb97968f5b7614f4333baf503f609799068ca3",
	name: "addRecurring",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addRecurring.__executeServer(opts));
var addRecurring = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	item_type: string(),
	name: string().min(1),
	amount: number(),
	category: string(),
	client: string(),
	frequency: string(),
	start_date: string()
})).handler(addRecurring_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const start = data.start_date || todayISO();
	await sql`insert into recurring_items (user_id, item_type, name, amount, category, client, frequency, next_run_date, active, created_date)
      values (${context.userId}, ${data.item_type}, ${data.name.trim()}, ${data.amount}, ${data.category}, ${data.client}, ${data.frequency}, ${start}, true, ${todayISO()})`;
});
var toggleRecurring_createServerFn_handler = createServerRpc({
	id: "6e2939cc466f03fdf1db2cc759aa6dbb8e347f1a40ab04e7a832ad226cb5a99b",
	name: "toggleRecurring",
	filename: "src/lib/kaze/server.ts"
}, (opts) => toggleRecurring.__executeServer(opts));
var toggleRecurring = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(toggleRecurring_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`update recurring_items set active = not active where id = ${data.id} and user_id = ${context.userId}`;
});
var deleteRecurring_createServerFn_handler = createServerRpc({
	id: "f15947c30b6e756adf5c84241444a5ca6ced2ed8f9a9609ebcf7e5a2a234c175",
	name: "deleteRecurring",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteRecurring.__executeServer(opts));
var deleteRecurring = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteRecurring_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from recurring_items where id = ${data.id} and user_id = ${context.userId}`;
});
var listSuppliers_createServerFn_handler = createServerRpc({
	id: "fcef9b26a7a6e93eafc7ac411389b8817c3764a9da1d6e70de5f1d450f811c6e",
	name: "listSuppliers",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listSuppliers.__executeServer(opts));
var listSuppliers = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listSuppliers_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from suppliers where user_id = ${context.userId} order by name`).map((r) => ({
		id: num(r.id),
		name: String(r.name),
		email: String(r.email ?? ""),
		phone: String(r.phone ?? ""),
		address: String(r.address ?? ""),
		notes: String(r.notes ?? "")
	}));
});
var addSupplier_createServerFn_handler = createServerRpc({
	id: "1d4a320ff8c5e3cbae6b819ff708899acacf56139d0ff0c4319ec10e229a7805",
	name: "addSupplier",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addSupplier.__executeServer(opts));
var addSupplier = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	email: string(),
	phone: string(),
	address: string(),
	notes: string()
})).handler(addSupplier_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`insert into suppliers (user_id, name, email, phone, address, notes)
      values (${context.userId}, ${data.name.trim()}, ${data.email}, ${data.phone}, ${data.address}, ${data.notes})`;
});
var deleteSupplier_createServerFn_handler = createServerRpc({
	id: "cb720b9d0e8413932298fdab9e291ba3d500920c8cce4adc423f749c9fb7f255",
	name: "deleteSupplier",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteSupplier.__executeServer(opts));
var deleteSupplier = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteSupplier_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from suppliers where id = ${data.id} and user_id = ${context.userId}`;
});
var listOrders_createServerFn_handler = createServerRpc({
	id: "a6f9b00d876292611e82cfb92354e2d1ffd6caad8510971855488da62f0bd50a",
	name: "listOrders",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listOrders.__executeServer(opts));
var listOrders = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listOrders_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from purchase_orders where user_id = ${context.userId} order by order_date desc, id desc`).map((r) => ({
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
		stock_id: r.stock_id == null ? null : num(r.stock_id)
	}));
});
var addOrder_createServerFn_handler = createServerRpc({
	id: "ebc942eb37a0ba69ed814e5df0e648ff8fa29b16268f84fa517bddd2fedf6622",
	name: "addOrder",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addOrder.__executeServer(opts));
var addOrder = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	supplier_id: number().nullable(),
	item_description: string().min(1),
	quantity: number().positive(),
	unit_cost: number(),
	expected_date: string(),
	stock_id: number().nullable()
})).handler(addOrder_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	let supplierName = "";
	if (data.supplier_id) supplierName = (await sql`select name from suppliers where id = ${data.supplier_id} and user_id = ${context.userId}`)[0]?.name ?? "";
	const total = data.quantity * data.unit_cost;
	const expected = data.expected_date || null;
	await sql`insert into purchase_orders (user_id, supplier_id, supplier_name, item_description, quantity, unit_cost, total_cost, status, order_date, expected_date, stock_id)
      values (${context.userId}, ${data.supplier_id}, ${supplierName}, ${data.item_description.trim()}, ${data.quantity}, ${data.unit_cost}, ${total}, ${"pending"}, ${todayISO()}, ${expected}, ${data.stock_id})`;
});
var receiveOrder_createServerFn_handler = createServerRpc({
	id: "f1d2340e20e9fdb1d432d7438ec05b85b952793f6de81874e7855efc7817ab81",
	name: "receiveOrder",
	filename: "src/lib/kaze/server.ts"
}, (opts) => receiveOrder.__executeServer(opts));
var receiveOrder = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(receiveOrder_createServerFn_handler, async ({ context, data }) => {
	const sql = await getSql();
	const po = (await sql`select * from purchase_orders where id = ${data.id} and user_id = ${context.userId}`)[0];
	if (!po) throw new Error("Order not found");
	await sql`update purchase_orders set status = ${"received"} where id = ${data.id} and user_id = ${context.userId}`;
	if (po.stock_id != null) await sql`update stock set quantity = quantity + ${num(po.quantity)} where id = ${num(po.stock_id)} and user_id = ${context.userId}`;
	await notify(sql, context.userId, `Purchase order for "${String(po.item_description)}" marked received${po.stock_id != null ? " and added to stock" : ""}.`, "purchase_order");
});
var deleteOrder_createServerFn_handler = createServerRpc({
	id: "cf952ffbe541846de28cf6296875aebe462e04737e39952e9842a25fa3081752",
	name: "deleteOrder",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteOrder.__executeServer(opts));
var deleteOrder = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteOrder_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from purchase_orders where id = ${data.id} and user_id = ${context.userId}`;
});
var listBudgets_createServerFn_handler = createServerRpc({
	id: "108476f6fc6a1283428ecedf4b64eb83a6c675c0e6acfbdebfb39ab34808869d",
	name: "listBudgets",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listBudgets.__executeServer(opts));
var listBudgets = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listBudgets_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	const rows = await sql`select * from budgets where user_id = ${context.userId} order by category`;
	const monthStart = todayISO().slice(0, 8) + "01";
	const result = [];
	for (const r of rows) {
		const category = String(r.category);
		const spentRow = await sql`select coalesce(sum(amount),0) as p from expenses where user_id = ${context.userId} and category = ${category} and date >= ${monthStart}`;
		result.push({
			id: num(r.id),
			category,
			monthly_limit: num(r.monthly_limit),
			spent: num(spentRow[0]?.p)
		});
	}
	return result;
});
var saveBudget_createServerFn_handler = createServerRpc({
	id: "c0583961187f0a48ef787cebb0a0736b15ced627ab4ad05f383cacaa59971b99",
	name: "saveBudget",
	filename: "src/lib/kaze/server.ts"
}, (opts) => saveBudget.__executeServer(opts));
var saveBudget = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	category: string(),
	monthly_limit: number()
})).handler(saveBudget_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`insert into budgets (user_id, category, monthly_limit, created_date)
      values (${context.userId}, ${data.category}, ${data.monthly_limit}, ${todayISO()})
      on conflict (user_id, category) do update set monthly_limit = excluded.monthly_limit`;
});
var deleteBudget_createServerFn_handler = createServerRpc({
	id: "4298966a437a5f50be7d90ffb7e4406adf98f16174af4ecbd746903965a08953",
	name: "deleteBudget",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteBudget.__executeServer(opts));
var deleteBudget = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteBudget_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from budgets where id = ${data.id} and user_id = ${context.userId}`;
});
var listNotifications_createServerFn_handler = createServerRpc({
	id: "485a72cfe58b2267fc8d5060849dcc48b9a69b36545dfb07446b2336d2426b94",
	name: "listNotifications",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listNotifications.__executeServer(opts));
var listNotifications = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listNotifications_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	const rows = await sql`select * from notifications where user_id = ${context.userId} order by created_date desc limit 100`;
	await sql`update notifications set is_read = true where user_id = ${context.userId} and is_read = false`;
	return rows.map((r) => ({
		id: num(r.id),
		message: String(r.message),
		category: String(r.category),
		is_read: Boolean(r.is_read),
		created_date: String(r.created_date)
	}));
});
var clearNotifications_createServerFn_handler = createServerRpc({
	id: "340df13ca275630b493c07f7dcdf00f1dacde8b0a4d4d4052c2326d58e4ebea8",
	name: "clearNotifications",
	filename: "src/lib/kaze/server.ts"
}, (opts) => clearNotifications.__executeServer(opts));
var clearNotifications = createServerFn({ method: "POST" }).middleware([authMiddleware]).handler(clearNotifications_createServerFn_handler, async ({ context }) => {
	await (await getSql())`delete from notifications where user_id = ${context.userId}`;
});
var unreadCount_createServerFn_handler = createServerRpc({
	id: "a0c92ccdf5aab0bb3e8ad6ad0a6ec29dda6f1dc1b62b3e6063fcae009b63e7b3",
	name: "unreadCount",
	filename: "src/lib/kaze/server.ts"
}, (opts) => unreadCount.__executeServer(opts));
var unreadCount = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(unreadCount_createServerFn_handler, async ({ context }) => {
	const rows = await (await getSql())`select count(*) as c from notifications where user_id = ${context.userId} and is_read = false`;
	return num(rows[0]?.c);
});
var listTeam_createServerFn_handler = createServerRpc({
	id: "74dad81fab049fda5ae533942dae94e908281d3318cfa2237e08b0149902ef6c",
	name: "listTeam",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listTeam.__executeServer(opts));
var listTeam = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listTeam_createServerFn_handler, async ({ context }) => {
	return (await (await getSql())`select * from team_members where user_id = ${context.userId} order by name`).map((r) => ({
		id: num(r.id),
		name: String(r.name),
		email: String(r.email ?? ""),
		role: String(r.role ?? "Staff")
	}));
});
var addTeam_createServerFn_handler = createServerRpc({
	id: "3a39c3576c9c6526e86a47bcad447d14c436ff6aa644e17ee49c2f7d25bbfa2a",
	name: "addTeam",
	filename: "src/lib/kaze/server.ts"
}, (opts) => addTeam.__executeServer(opts));
var addTeam = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	email: string(),
	role: string()
})).handler(addTeam_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`insert into team_members (user_id, name, email, role) values (${context.userId}, ${data.name.trim()}, ${data.email}, ${data.role || "Staff"})`;
});
var deleteTeam_createServerFn_handler = createServerRpc({
	id: "454859529bfead33ed2a73bc342877b09c2b66f02de59d08e9b7310b9c8ba1b2",
	name: "deleteTeam",
	filename: "src/lib/kaze/server.ts"
}, (opts) => deleteTeam.__executeServer(opts));
var deleteTeam = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(deleteTeam_createServerFn_handler, async ({ context, data }) => {
	await (await getSql())`delete from team_members where id = ${data.id} and user_id = ${context.userId}`;
});
var listActivity_createServerFn_handler = createServerRpc({
	id: "dfd21eb7dbb182b959392e3036479d22c80771b068193292639e6e81a48ad16e",
	name: "listActivity",
	filename: "src/lib/kaze/server.ts"
}, (opts) => listActivity.__executeServer(opts));
var listActivity = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(listActivity_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	const rows = await sql`select id, username, login_time from user_activity where user_id = ${context.userId} order by login_time desc limit 50`;
	const today = todayISO();
	const count = await sql`select count(*) as c from user_activity where user_id = ${context.userId} and login_time::date = ${today}`;
	return {
		logs: rows.map((r) => ({
			id: num(r.id),
			username: String(r.username),
			login_time: String(r.login_time)
		})),
		todayCount: num(count[0]?.c)
	};
});
var getReports_createServerFn_handler = createServerRpc({
	id: "d188ebd1d89ed6d3139216d2a6186d4ee0872c9127ea104df5e0afece56b92e1",
	name: "getReports",
	filename: "src/lib/kaze/server.ts"
}, (opts) => getReports.__executeServer(opts));
var getReports = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(getReports_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	const uid = context.userId;
	const months = [];
	const start = todayISO().slice(0, 8) + "01";
	for (let i = 5; i >= 0; i--) months.push(addMonths(start, -i).slice(0, 7));
	const monthlyIncome = Object.fromEntries(months.map((m) => [m, 0]));
	const monthlyExpenses = Object.fromEntries(months.map((m) => [m, 0]));
	const monthlyProfit = Object.fromEntries(months.map((m) => [m, 0]));
	const inc = await sql`select date, amount from income where user_id = ${uid}`;
	for (const r of inc) {
		const k = monthKey(String(r.date));
		if (k in monthlyIncome) monthlyIncome[k] += num(r.amount);
	}
	const exp = await sql`select date, amount from expenses where user_id = ${uid}`;
	for (const r of exp) {
		const k = monthKey(String(r.date));
		if (k in monthlyExpenses) monthlyExpenses[k] += num(r.amount);
	}
	const sp = await sql`select sale_date, profit from sales where user_id = ${uid}`;
	const salesProfit = Object.fromEntries(months.map((m) => [m, 0]));
	for (const r of sp) {
		const k = monthKey(String(r.sale_date));
		if (k in salesProfit) salesProfit[k] += num(r.profit);
	}
	for (const m of months) monthlyProfit[m] = (monthlyIncome[m] ?? 0) - (monthlyExpenses[m] ?? 0) + (salesProfit[m] ?? 0);
	const topProducts = await sql`
      select product_name, sum(total_amount) as revenue, sum(profit) as profit, sum(quantity_sold) as units
      from sales where user_id = ${uid}
      group by product_name order by sum(total_amount) desc limit 5`;
	const topCustomers = await sql`
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
			units: num(p.units)
		})),
		topCustomers: topCustomers.map((c) => ({
			customer_name: c.customer_name,
			spent: num(c.spent),
			orders: num(c.orders)
		}))
	};
});
var seedSample_createServerFn_handler = createServerRpc({
	id: "7e05b478a06f094e4e17f4d11042e0df0c46b8e2d06c8b0d86aa404fd4bfce47",
	name: "seedSample",
	filename: "src/lib/kaze/server.ts"
}, (opts) => seedSample.__executeServer(opts));
var seedSample = createServerFn({ method: "POST" }).middleware([authMiddleware]).handler(seedSample_createServerFn_handler, async ({ context }) => {
	const sql = await getSql();
	const uid = context.userId;
	await ensureSettings(sql, uid);
	await sql`update settings set business_name = ${"KAZE Traders"}, monthly_revenue_goal = ${8e3}, currency_symbol = ${"$"} where user_id = ${uid} and business_name = ${""}`;
	const existing = await sql`select count(*) as c from stock where user_id = ${uid}`;
	if (num(existing[0]?.c) > 0) return { seeded: false };
	for (const p of [
		[
			"Rice 25kg",
			40,
			18,
			24,
			"bag"
		],
		[
			"Cooking oil 2L",
			60,
			4.5,
			6.2,
			"btl"
		],
		[
			"Sugar 1kg",
			80,
			1.1,
			1.6,
			"pkt"
		],
		[
			"Bar soap",
			120,
			.6,
			1,
			"pcs"
		],
		[
			"Maize meal 10kg",
			35,
			7.5,
			10,
			"bag"
		]
	]) await sql`insert into stock (user_id, product_name, quantity, cost_price, selling_price, unit)
        values (${uid}, ${p[0]}, ${p[1]}, ${p[2]}, ${p[3]}, ${p[4]})`;
	const stock = await sql`select id, product_name, cost_price, selling_price from stock where user_id = ${uid}`;
	await sql`insert into customers (user_id, name, email, phone, address) values
      (${uid}, ${"Lusaka Grocers"}, ${"orders@lusakagrocers.example"}, ${"+260 97 111 0001"}, ${"Cairo Road"}),
      (${uid}, ${"Chilenje Market Stall"}, ${""}, ${"+260 96 222 0002"}, ${"Chilenje"}),
      (${uid}, ${"Northmead Cafe"}, ${"hello@northmead.example"}, ${""}, ${"Northmead"})`;
	const customers = await sql`select id, name, email from customers where user_id = ${uid}`;
	const today = /* @__PURE__ */ new Date();
	for (let i = 0; i < 8; i++) {
		const d = new Date(today);
		d.setDate(d.getDate() - i);
		const date = d.toISOString().slice(0, 10);
		const item = stock[i % stock.length];
		if (!item) continue;
		const cust = customers[i % customers.length];
		const qty = 1 + i % 4;
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
//#endregion
export { addCash_createServerFn_handler, addCustomer_createServerFn_handler, addDocument_createServerFn_handler, addExpense_createServerFn_handler, addIncome_createServerFn_handler, addOrder_createServerFn_handler, addRecurring_createServerFn_handler, addSale_createServerFn_handler, addStock_createServerFn_handler, addSupplier_createServerFn_handler, addSwot_createServerFn_handler, addTeam_createServerFn_handler, clearNotifications_createServerFn_handler, deleteBudget_createServerFn_handler, deleteCash_createServerFn_handler, deleteCustomer_createServerFn_handler, deleteDocument_createServerFn_handler, deleteExpense_createServerFn_handler, deleteIncome_createServerFn_handler, deleteOrder_createServerFn_handler, deleteRecurring_createServerFn_handler, deleteSale_createServerFn_handler, deleteStock_createServerFn_handler, deleteSupplier_createServerFn_handler, deleteSwot_createServerFn_handler, deleteTeam_createServerFn_handler, dismissTutorial_createServerFn_handler, generateDocumentCopy_createServerFn_handler, getDashboard_createServerFn_handler, getPlan_createServerFn_handler, getReports_createServerFn_handler, getSettings_createServerFn_handler, listActivity_createServerFn_handler, listBudgets_createServerFn_handler, listCash_createServerFn_handler, listCustomers_createServerFn_handler, listDocuments_createServerFn_handler, listNotifications_createServerFn_handler, listOrders_createServerFn_handler, listRecurring_createServerFn_handler, listSales_createServerFn_handler, listStock_createServerFn_handler, listSuppliers_createServerFn_handler, listSwot_createServerFn_handler, listTeam_createServerFn_handler, receiveOrder_createServerFn_handler, recordActivity_createServerFn_handler, saveBudget_createServerFn_handler, savePlan_createServerFn_handler, saveSettings_createServerFn_handler, seedSample_createServerFn_handler, toggleRecurring_createServerFn_handler, unreadCount_createServerFn_handler, updateCash_createServerFn_handler, updateCustomer_createServerFn_handler, updateStock_createServerFn_handler };
