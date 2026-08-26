import { a as getServerFnById, i as TSS_SERVER_FUNCTION, r as createServerFn } from "./ssr.mjs";
import { Jt as object, Ut as boolean, Zt as string, qt as number } from "../_libs/@better-auth/core+[...].mjs";
import { t as authMiddleware } from "./middleware-BX86ISIa.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/server-BeIiaNi3.js
var createSsrRpc = (functionId) => {
	const url = "/_serverFn/" + functionId;
	const serverFnMeta = { id: functionId };
	const fn = async (...args) => {
		return (await getServerFnById(functionId, { origin: "server" }))(...args);
	};
	return Object.assign(fn, {
		url,
		serverFnMeta,
		[TSS_SERVER_FUNCTION]: true
	});
};
var idSchema = object({ id: number() });
var getSettings = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("b2728d6ed29cd46c4adcc73c2d2e8fd14f5de2f553fd71ea61030ca0bd411013"));
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
})).handler(createSsrRpc("197c947cfcbb09b32a5abc2e8489f57099f75ef2a27299ff7cec31536fc22f02"));
var dismissTutorial = createServerFn({ method: "POST" }).middleware([authMiddleware]).handler(createSsrRpc("c4544171e9c329f1fddb21c3557b512a7361110fbf71d3b20e73877b88c488a5"));
var recordActivity = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({ username: string() })).handler(createSsrRpc("f6add793728cf9e57d79d44791fc0bb417505a6f658013e999a33ba1e87ca5f3"));
var getDashboard = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("804167cb54f47c7583161fe8ff5ffbcc99ad83696b887b0abcfe3413b73b2f15"));
var addIncome = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	source: string().min(1),
	amount: number(),
	date: string()
})).handler(createSsrRpc("15a2310a56c9bcf5c3b5b280b3345b339905bd501bb9e8bd7c940b3fa05f7993"));
var deleteIncome = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("5ba71790ace9e363e4b6534e0beab7b34898635af30043c9c886c2da8678d703"));
var addExpense = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	amount: number(),
	category: string(),
	date: string()
})).handler(createSsrRpc("00a6080192a254f1a5122b6424fcbe6498757bb2e381e7d0fe8f6c1855f09bea"));
var deleteExpense = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("fa926866b83f0d180896a3cf274500aa20707c721dfc4b52403503a298519ad1"));
var listStock = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("89e653a16245fd3e4e015da180b794d26de30d5d7d55679f759455813682c403"));
var addStock = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	product_name: string().min(1),
	quantity: number(),
	cost_price: number(),
	selling_price: number(),
	unit: string()
})).handler(createSsrRpc("3a4bc15943b8a466f98d5dfcee26a5d10d3a4e3740b08b82b18dbd3fed73d4e1"));
var updateStock = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	id: number(),
	product_name: string().min(1),
	quantity: number(),
	cost_price: number(),
	selling_price: number(),
	unit: string()
})).handler(createSsrRpc("fbe8a5f089e663d7d8af1cf959883f8f69ac10d08d477b29aa7e212f976bfbe1"));
var deleteStock = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("e97ca9a309d5d0e1a7c10f8ecd72c6a9df2406d1c75ef03a9adb65a0094f267d"));
var listCustomers = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("6ba533b064b355145b796fe242f14aa1deaedd4fd215bc955d66b11262014774"));
var addCustomer = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	email: string(),
	phone: string(),
	address: string(),
	notes: string()
})).handler(createSsrRpc("be01efb345bb72434141ad71f54e02eb4f2c1747989c54c4be426240ce3412d7"));
var updateCustomer = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	id: number(),
	name: string().min(1),
	email: string(),
	phone: string(),
	address: string(),
	notes: string()
})).handler(createSsrRpc("fa69a5a9ece46fb7bf931c5eaa265c9739ad29db2c7c1a769c66e87f5d1509ae"));
var deleteCustomer = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("eec968cdafb4c106e8ef245a64c0893ab5b9f4983124de89ed016abbfca44f61"));
var listSales = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("ad0727229055a952b813d85cf861accfaae30f4d7fa7f5ab1d6e767a3a10e671"));
var addSale = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	stock_id: number(),
	quantity: number().positive(),
	customer_id: number().nullable(),
	customer_name: string(),
	customer_email: string(),
	date: string()
})).handler(createSsrRpc("cabcd598009d5f0f46e28ec6d13ae25e3b4c343c2937b23492bb99681d20bab5"));
var deleteSale = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("e00e09a81b1f5e4b7602c8e23e8b2a141b8384c0607ee1bea4e74c133f6bb57e"));
var listDocuments = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("49e342682191c31d785c2806065d168c1f4d841e21d6e18256b76ecf536713ce"));
var addDocument = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	doc_type: string(),
	title: string().min(1),
	client: string().min(1),
	amount: number().nullable(),
	date: string(),
	notes: string()
})).handler(createSsrRpc("438ea31559e1929e58403333243a99bc8b165b5d58a2425c02aaa24b60d82cfc"));
var deleteDocument = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("47fab243c01fc195253186954cb6df5d43d1f18b0ea90dcb5346cbcfe24e4460"));
var generateDocumentCopy = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	doc_type: string(),
	title: string(),
	client: string(),
	amount: number().nullable(),
	notes: string(),
	business_name: string()
})).handler(createSsrRpc("8fde8edccc074746d396b28c1ca62f890227a45f82a709ec3b23d4e66710d710"));
var listCash = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("966810d31760408e061a13fbdcfd746dd62a9d575f4f3032e2eca5852d379e32"));
var addCash = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	entry_type: string(),
	category: string().min(1),
	description: string(),
	amount: number(),
	date: string()
})).handler(createSsrRpc("c6dd35eec4291b9f73bee78f3744f58611f18c5f24721fbe7fcf3cfb231a93f4"));
var updateCash = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	id: number(),
	entry_type: string(),
	category: string().min(1),
	description: string(),
	amount: number(),
	date: string()
})).handler(createSsrRpc("b7b933efbfb0d570d3d006c78fec02c6203651cf4ffa7d7724c53d4605f237df"));
var deleteCash = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("de3feafd742dd141c0e6d76c0f68e6c0e150b2e7fb7fe8d39100974e937a3313"));
var listSwot = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("3576ab40e8731c545c1c98af4a9df667680294d572604bf3593e14a619a6a26c"));
var addSwot = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	title: string(),
	strengths: string(),
	weaknesses: string(),
	opportunities: string(),
	threats: string()
})).handler(createSsrRpc("1f656aba59ea3abacfb7c2bc00c575b0542869b25b155ae5d76be88a8cdd62fa"));
var deleteSwot = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("0cd6cd5c27dae72cc0b7a74ef9affa0fff2649219c3c6411b63dd880da092849"));
var getPlan = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("89d92bb482714f629b80bac98e5389c035cc96d51941741202a0b03fca13219c"));
var savePlan = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	business_name: string(),
	mission: string(),
	products_services: string(),
	target_market: string(),
	marketing_strategy: string(),
	operations_plan: string(),
	financial_plan: string(),
	goals: string()
})).handler(createSsrRpc("56d71b1c08bb5b67c63a91b99c9d1377b92bc8db6038c78fac5381de9e1658fc"));
var listRecurring = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("7085d8d704f3d23964144e522f355aa20fc8952a1c285339c7f30f75c994eb0f"));
var addRecurring = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	item_type: string(),
	name: string().min(1),
	amount: number(),
	category: string(),
	client: string(),
	frequency: string(),
	start_date: string()
})).handler(createSsrRpc("93a5e17f27f7131eaefda74bc1eb97968f5b7614f4333baf503f609799068ca3"));
var toggleRecurring = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("6e2939cc466f03fdf1db2cc759aa6dbb8e347f1a40ab04e7a832ad226cb5a99b"));
var deleteRecurring = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("f15947c30b6e756adf5c84241444a5ca6ced2ed8f9a9609ebcf7e5a2a234c175"));
var listSuppliers = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("fcef9b26a7a6e93eafc7ac411389b8817c3764a9da1d6e70de5f1d450f811c6e"));
var addSupplier = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	email: string(),
	phone: string(),
	address: string(),
	notes: string()
})).handler(createSsrRpc("1d4a320ff8c5e3cbae6b819ff708899acacf56139d0ff0c4319ec10e229a7805"));
var deleteSupplier = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("cb720b9d0e8413932298fdab9e291ba3d500920c8cce4adc423f749c9fb7f255"));
var listOrders = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("a6f9b00d876292611e82cfb92354e2d1ffd6caad8510971855488da62f0bd50a"));
var addOrder = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	supplier_id: number().nullable(),
	item_description: string().min(1),
	quantity: number().positive(),
	unit_cost: number(),
	expected_date: string(),
	stock_id: number().nullable()
})).handler(createSsrRpc("ebc942eb37a0ba69ed814e5df0e648ff8fa29b16268f84fa517bddd2fedf6622"));
var receiveOrder = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("f1d2340e20e9fdb1d432d7438ec05b85b952793f6de81874e7855efc7817ab81"));
var deleteOrder = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("cf952ffbe541846de28cf6296875aebe462e04737e39952e9842a25fa3081752"));
var listBudgets = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("108476f6fc6a1283428ecedf4b64eb83a6c675c0e6acfbdebfb39ab34808869d"));
var saveBudget = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	category: string(),
	monthly_limit: number()
})).handler(createSsrRpc("c0583961187f0a48ef787cebb0a0736b15ced627ab4ad05f383cacaa59971b99"));
var deleteBudget = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("4298966a437a5f50be7d90ffb7e4406adf98f16174af4ecbd746903965a08953"));
var listNotifications = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("485a72cfe58b2267fc8d5060849dcc48b9a69b36545dfb07446b2336d2426b94"));
var clearNotifications = createServerFn({ method: "POST" }).middleware([authMiddleware]).handler(createSsrRpc("340df13ca275630b493c07f7dcdf00f1dacde8b0a4d4d4052c2326d58e4ebea8"));
var unreadCount = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("a0c92ccdf5aab0bb3e8ad6ad0a6ec29dda6f1dc1b62b3e6063fcae009b63e7b3"));
var listTeam = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("74dad81fab049fda5ae533942dae94e908281d3318cfa2237e08b0149902ef6c"));
var addTeam = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(object({
	name: string().min(1),
	email: string(),
	role: string()
})).handler(createSsrRpc("3a39c3576c9c6526e86a47bcad447d14c436ff6aa644e17ee49c2f7d25bbfa2a"));
var deleteTeam = createServerFn({ method: "POST" }).middleware([authMiddleware]).validator(idSchema).handler(createSsrRpc("454859529bfead33ed2a73bc342877b09c2b66f02de59d08e9b7310b9c8ba1b2"));
var listActivity = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("dfd21eb7dbb182b959392e3036479d22c80771b068193292639e6e81a48ad16e"));
var getReports = createServerFn({ method: "GET" }).middleware([authMiddleware]).handler(createSsrRpc("d188ebd1d89ed6d3139216d2a6186d4ee0872c9127ea104df5e0afece56b92e1"));
var seedSample = createServerFn({ method: "POST" }).middleware([authMiddleware]).handler(createSsrRpc("7e05b478a06f094e4e17f4d11042e0df0c46b8e2d06c8b0d86aa404fd4bfce47"));
//#endregion
export { unreadCount as $, getPlan as A, listRecurring as B, deleteStock as C, dismissTutorial as D, deleteTeam as E, listCash as F, listTeam as G, listStock as H, listCustomers as I, saveBudget as J, receiveOrder as K, listDocuments as L, getSettings as M, listActivity as N, generateDocumentCopy as O, listBudgets as P, toggleRecurring as Q, listNotifications as R, deleteSale as S, deleteSwot as T, listSuppliers as U, listSales as V, listSwot as W, saveSettings as X, savePlan as Y, seedSample as Z, deleteDocument as _, addIncome as a, deleteOrder as b, addSale as c, addSwot as d, updateCash as et, addTeam as f, deleteCustomer as g, deleteCash as h, addExpense as i, getReports as j, getDashboard as k, addStock as l, deleteBudget as m, addCustomer as n, updateStock as nt, addOrder as o, clearNotifications as p, recordActivity as q, addDocument as r, addRecurring as s, addCash as t, updateCustomer as tt, addSupplier as u, deleteExpense as v, deleteSupplier as w, deleteRecurring as x, deleteIncome as y, listOrders as z };
