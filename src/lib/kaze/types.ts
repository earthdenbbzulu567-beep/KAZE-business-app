export type Settings = {
  user_id: string;
  business_name: string;
  currency_code: string;
  currency_symbol: string;
  tax_rate: number;
  monthly_revenue_goal: number;
  low_stock_threshold: number;
  theme: string;
  font_size: string;
  default_chart_type: string;
  animations_enabled: boolean;
  show_low_stock_widget: boolean;
  show_sales_trend: boolean;
  about_text: string;
  tutorial_completed: boolean;
};

export type IncomeRow = {
  id: number;
  source: string;
  amount: number;
  date: string;
};

export type ExpenseRow = {
  id: number;
  name: string;
  amount: number;
  category: string;
  date: string;
};

export type StockRow = {
  id: number;
  product_name: string;
  quantity: number;
  cost_price: number;
  selling_price: number;
  unit: string;
};

export type CustomerRow = {
  id: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
  order_count: number;
  total_spent: number;
};

export type SaleRow = {
  id: number;
  stock_id: number | null;
  product_name: string;
  quantity_sold: number;
  selling_price_at_time: number;
  total_amount: number;
  profit: number;
  sale_date: string;
  customer_name: string;
  customer_email: string;
  customer_id: number | null;
};

export type DocumentRow = {
  id: number;
  doc_type: string;
  title: string;
  client: string;
  amount: number | null;
  date: string;
  notes: string;
};

export type CashRow = {
  id: number;
  entry_type: string;
  category: string;
  description: string;
  amount: number;
  date: string;
};

export type SwotRow = {
  id: number;
  title: string;
  strengths: string;
  weaknesses: string;
  opportunities: string;
  threats: string;
  created_date: string;
};

export type PlanRow = {
  business_name: string;
  mission: string;
  products_services: string;
  target_market: string;
  marketing_strategy: string;
  operations_plan: string;
  financial_plan: string;
  goals: string;
  updated_date: string | null;
};

export type RecurringRow = {
  id: number;
  item_type: string;
  name: string;
  amount: number;
  category: string;
  client: string;
  frequency: string;
  next_run_date: string;
  active: boolean;
};

export type SupplierRow = {
  id: number;
  name: string;
  email: string;
  phone: string;
  address: string;
  notes: string;
};

export type PurchaseOrderRow = {
  id: number;
  supplier_id: number | null;
  supplier_name: string;
  item_description: string;
  quantity: number;
  unit_cost: number;
  total_cost: number;
  status: string;
  order_date: string;
  expected_date: string | null;
  stock_id: number | null;
};

export type BudgetRow = {
  id: number;
  category: string;
  monthly_limit: number;
  spent: number;
};

export type NotificationRow = {
  id: number;
  message: string;
  category: string;
  is_read: boolean;
  created_date: string;
};

export type TeamRow = {
  id: number;
  name: string;
  email: string;
  role: string;
};

export type ActivityRow = {
  id: number;
  username: string;
  login_time: string;
};

export type DashboardData = {
  settings: Settings;
  income: IncomeRow[];
  expenses: ExpenseRow[];
  totalIncome: number;
  totalExpenses: number;
  salesProfit: number;
  cashNet: number;
  profit: number;
  monthRevenue: number;
  goalProgressPct: number;
  lowStock: { product_name: string; quantity: number; unit: string }[];
  salesTrend: { date: string; total: number }[];
  incomeByDate: Record<string, number>;
  expenseByDate: Record<string, number>;
  unreadNotifications: number;
};
