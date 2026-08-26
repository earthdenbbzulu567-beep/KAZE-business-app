-- KAZE Traders business data. All rows are scoped by user_id (Better Auth text id).

create table if not exists settings (
  user_id text primary key,
  business_name text not null default '',
  currency_code text not null default 'USD',
  currency_symbol text not null default '$',
  tax_rate double precision not null default 0,
  monthly_revenue_goal double precision not null default 0,
  low_stock_threshold double precision not null default 10,
  theme text not null default 'dark',
  font_size text not null default 'medium',
  default_chart_type text not null default 'line',
  animations_enabled boolean not null default true,
  show_low_stock_widget boolean not null default true,
  show_sales_trend boolean not null default true,
  about_text text not null default '',
  tutorial_completed boolean not null default false
);

create table if not exists income (
  id serial primary key,
  user_id text not null,
  source text not null,
  amount double precision not null,
  date date not null,
  created_at timestamptz not null default now()
);
create index if not exists income_user_idx on income (user_id);

create table if not exists expenses (
  id serial primary key,
  user_id text not null,
  name text not null,
  amount double precision not null,
  category text not null,
  date date not null,
  created_at timestamptz not null default now()
);
create index if not exists expenses_user_idx on expenses (user_id);

create table if not exists documents (
  id serial primary key,
  user_id text not null,
  doc_type text not null,
  title text not null,
  client text not null,
  amount double precision,
  date date not null,
  notes text not null default '',
  created_at timestamptz not null default now()
);
create index if not exists documents_user_idx on documents (user_id);

create table if not exists cash_books (
  id serial primary key,
  user_id text not null,
  entry_type text not null,
  category text not null,
  description text not null default '',
  amount double precision not null,
  date date not null,
  created_at timestamptz not null default now()
);
create index if not exists cash_books_user_idx on cash_books (user_id);

create table if not exists stock (
  id serial primary key,
  user_id text not null,
  product_name text not null,
  quantity double precision not null,
  cost_price double precision not null,
  selling_price double precision not null,
  unit text not null default 'pcs'
);
create index if not exists stock_user_idx on stock (user_id);

create table if not exists customers (
  id serial primary key,
  user_id text not null,
  name text not null,
  email text not null default '',
  phone text not null default '',
  address text not null default '',
  notes text not null default ''
);
create index if not exists customers_user_idx on customers (user_id);

create table if not exists sales (
  id serial primary key,
  user_id text not null,
  stock_id integer,
  product_name text not null,
  quantity_sold double precision not null,
  selling_price_at_time double precision not null,
  total_amount double precision not null,
  profit double precision not null,
  sale_date date not null,
  customer_name text not null default '',
  customer_email text not null default '',
  customer_id integer
);
create index if not exists sales_user_idx on sales (user_id);

create table if not exists user_activity (
  id serial primary key,
  user_id text not null,
  username text not null,
  login_time timestamptz not null default now()
);
create index if not exists user_activity_user_idx on user_activity (user_id);

create table if not exists swot_analyses (
  id serial primary key,
  user_id text not null,
  title text not null,
  strengths text not null default '',
  weaknesses text not null default '',
  opportunities text not null default '',
  threats text not null default '',
  created_date date not null
);
create index if not exists swot_user_idx on swot_analyses (user_id);

create table if not exists business_plans (
  user_id text primary key,
  business_name text not null default '',
  mission text not null default '',
  products_services text not null default '',
  target_market text not null default '',
  marketing_strategy text not null default '',
  operations_plan text not null default '',
  financial_plan text not null default '',
  goals text not null default '',
  updated_date date
);

create table if not exists recurring_items (
  id serial primary key,
  user_id text not null,
  item_type text not null,
  name text not null,
  amount double precision not null,
  category text not null default '',
  client text not null default '',
  frequency text not null default 'monthly',
  next_run_date date not null,
  active boolean not null default true,
  created_date date not null
);
create index if not exists recurring_user_idx on recurring_items (user_id);

create table if not exists suppliers (
  id serial primary key,
  user_id text not null,
  name text not null,
  email text not null default '',
  phone text not null default '',
  address text not null default '',
  notes text not null default ''
);
create index if not exists suppliers_user_idx on suppliers (user_id);

create table if not exists purchase_orders (
  id serial primary key,
  user_id text not null,
  supplier_id integer,
  supplier_name text not null default '',
  item_description text not null,
  quantity double precision not null,
  unit_cost double precision not null,
  total_cost double precision not null,
  status text not null default 'pending',
  order_date date not null,
  expected_date date,
  stock_id integer
);
create index if not exists purchase_orders_user_idx on purchase_orders (user_id);

create table if not exists budgets (
  id serial primary key,
  user_id text not null,
  category text not null,
  monthly_limit double precision not null,
  created_date date not null,
  unique (user_id, category)
);
create index if not exists budgets_user_idx on budgets (user_id);

create table if not exists notifications (
  id serial primary key,
  user_id text not null,
  message text not null,
  category text not null default 'info',
  is_read boolean not null default false,
  created_date timestamptz not null default now()
);
create index if not exists notifications_user_idx on notifications (user_id);

create table if not exists team_members (
  id serial primary key,
  user_id text not null,
  name text not null,
  email text not null default '',
  role text not null default 'Staff',
  created_at timestamptz not null default now()
);
create index if not exists team_members_user_idx on team_members (user_id);
