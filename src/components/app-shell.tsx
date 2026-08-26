import { Link, Outlet, useRouterState } from "@tanstack/react-router";
import {
  Bell,
  BookOpen,
  ClipboardList,
  FileText,
  LayoutDashboard,
  LineChart,
  Menu,
  Package,
  Repeat,
  Settings as SettingsIcon,
  ShoppingCart,
  Target,
  Truck,
  Users,
  Wallet,
  Compass,
  ScrollText,
  Clock,
  UserRound,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { Logo } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { RedirectToSignIn, UserButton } from "@/lib/auth/gates";
import { useCurrentUser, useCurrentUserState } from "@/lib/auth/use-current-user";
import { getSettings, recordActivity, unreadCount } from "@/lib/kaze/server";
import type { Settings } from "@/lib/kaze/types";
import { cn } from "@/lib/utils";

type NavItem = { to: string; label: string; icon: typeof LayoutDashboard };

const GROUPS: { label: string; items: NavItem[] }[] = [
  {
    label: "Overview",
    items: [
      { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { to: "/reports", label: "Reports", icon: LineChart },
    ],
  },
  {
    label: "Trade",
    items: [
      { to: "/stock", label: "Stock", icon: Package },
      { to: "/sales", label: "Sales", icon: ShoppingCart },
      { to: "/customers", label: "Customers", icon: Users },
    ],
  },
  {
    label: "Money",
    items: [
      { to: "/cashbook", label: "Cash book", icon: Wallet },
      { to: "/budgets", label: "Budgets", icon: Target },
      { to: "/recurring", label: "Recurring", icon: Repeat },
    ],
  },
  {
    label: "Operations",
    items: [
      { to: "/documents", label: "Documents", icon: FileText },
      { to: "/suppliers", label: "Suppliers", icon: Truck },
      { to: "/orders", label: "Purchase orders", icon: ClipboardList },
    ],
  },
  {
    label: "Strategy",
    items: [
      { to: "/swot", label: "SWOT", icon: Compass },
      { to: "/plan", label: "Business plan", icon: ScrollText },
    ],
  },
];

const ACCOUNT: NavItem[] = [
  { to: "/notifications", label: "Alerts", icon: Bell },
  { to: "/team", label: "Team", icon: UserRound },
  { to: "/activity", label: "Activity", icon: Clock },
  { to: "/help", label: "Guide", icon: BookOpen },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

function NavLink({
  item,
  active,
  onClick,
  badge,
}: {
  item: NavItem;
  active: boolean;
  onClick?: () => void;
  badge?: number;
}) {
  const Icon = item.icon;
  return (
    <Link
      to={item.to}
      onClick={onClick}
      className={cn(
        "flex h-10 items-center gap-2.5 rounded-md px-2.5 text-sm transition-colors duration-[var(--motion-quick)]",
        active ? "bg-surface-2 text-fg" : "text-muted hover:bg-surface/80 hover:text-fg",
      )}
    >
      <Icon className="size-4 shrink-0" strokeWidth={1.75} />
      <span className="flex-1 truncate">{item.label}</span>
      {badge ? (
        <span className="grid min-w-5 place-items-center rounded-full bg-out/20 px-1.5 text-[10px] font-medium text-out">
          {badge}
        </span>
      ) : null}
    </Link>
  );
}

function SideNav({
  pathname,
  unread,
  onNavigate,
}: {
  pathname: string;
  unread: number;
  onNavigate?: () => void;
}) {
  return (
    <div className="flex h-full flex-col">
      <Link to="/dashboard" onClick={onNavigate} className="mb-6 flex items-center px-1 pt-1">
        <Logo />
      </Link>
      <nav className="flex-1 space-y-5 overflow-y-auto pr-1">
        {GROUPS.map((g) => (
          <div key={g.label}>
            <p className="mb-1.5 px-2.5 text-[10px] font-medium tracking-[0.16em] text-subtle uppercase">
              {g.label}
            </p>
            <div className="space-y-0.5">
              {g.items.map((item) => (
                <NavLink
                  key={item.to}
                  item={item}
                  active={pathname === item.to}
                  onClick={onNavigate}
                />
              ))}
            </div>
          </div>
        ))}
        <div>
          <p className="mb-1.5 px-2.5 text-[10px] font-medium tracking-[0.16em] text-subtle uppercase">
            Account
          </p>
          <div className="space-y-0.5">
            {ACCOUNT.map((item) => (
              <NavLink
                key={item.to}
                item={item}
                active={pathname === item.to}
                onClick={onNavigate}
                badge={item.to === "/notifications" ? unread : undefined}
              />
            ))}
          </div>
        </div>
      </nav>
      <div className="mt-4 border-t border-border pt-3">
        <UserButton />
      </div>
    </div>
  );
}

export function AppShell() {
  const { user, isPending } = useCurrentUserState();
  const current = useCurrentUser();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const [settings, setSettings] = useState<Settings | null>(null);
  const [unread, setUnread] = useState(0);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!user) return;
    let cancelled = false;
    void (async () => {
      try {
        const [s, n] = await Promise.all([getSettings(), unreadCount()]);
        if (!cancelled) {
          setSettings(s);
          setUnread(n);
        }
      } catch {
        /* signed-out race */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [user, pathname]);

  useEffect(() => {
    if (!user) return;
    const key = `kaze-login-${user.id}`;
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key, "1");
    void recordActivity({
      data: { username: user.displayName ?? user.primaryEmail ?? "User" },
    }).catch(() => {});
  }, [user]);

  useEffect(() => {
    if (!settings) return;
    document.documentElement.dataset.theme = settings.theme === "light" ? "light" : "dark";
    document.documentElement.dataset.density = settings.font_size || "medium";
    if (!settings.animations_enabled) {
      document.documentElement.dataset.motion = "off";
    } else {
      delete document.documentElement.dataset.motion;
    }
  }, [settings]);

  if (isPending) {
    return (
      <div className="flex min-h-screen bg-bg">
        <aside className="hidden w-60 shrink-0 border-r border-border p-4 md:block">
          <Skeleton className="mb-6 h-8 w-28" />
          <div className="space-y-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </aside>
        <div className="flex-1 p-8">
          <Skeleton className="mb-4 h-8 w-48" />
          <Skeleton className="h-40 w-full" />
        </div>
      </div>
    );
  }

  if (!user) return <RedirectToSignIn />;

  const title =
    settings?.business_name?.trim() ||
    current?.displayName ||
    "KAZE Traders";

  return (
    <div className="flex min-h-screen bg-bg text-fg">
      <aside className="sticky top-0 hidden h-screen w-60 shrink-0 border-r border-border bg-bg-elevated p-4 md:block">
        <SideNav pathname={pathname} unread={unread} />
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-bg/90 px-4 backdrop-blur-sm md:hidden">
          <Button variant="ghost" size="icon" onClick={() => setOpen(true)} aria-label="Open menu">
            <Menu className="size-5" />
          </Button>
          <Logo />
          <span className="ml-auto truncate text-xs text-muted">{title}</span>
        </header>
        <Sheet open={open} onOpenChange={setOpen}>
          <SheetContent side="left">
            <SideNav
              pathname={pathname}
              unread={unread}
              onNavigate={() => setOpen(false)}
            />
          </SheetContent>
        </Sheet>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export function Money({
  amount,
  symbol = "$",
  tone,
}: {
  amount: number;
  symbol?: string;
  tone?: "in" | "out" | "plain";
}) {
  const abs = Math.abs(amount).toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  const text = amount < 0 ? `-${symbol}${abs}` : `${symbol}${abs}`;
  const color =
    tone === "in" ? "text-in" : tone === "out" ? "text-out" : amount < 0 ? "text-out" : "text-fg";
  return <span className={cn("tabular font-medium", color)}>{text}</span>;
}

export function SectionLabel({ children }: { children: ReactNode }) {
  return (
    <h2 className="mb-3 flex items-center gap-2 text-xs font-medium tracking-[0.14em] text-subtle uppercase">
      <span className="inline-block h-3 w-0.5 rounded-full bg-brand" />
      {children}
    </h2>
  );
}
