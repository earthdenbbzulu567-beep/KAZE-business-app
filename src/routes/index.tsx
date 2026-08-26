import { createFileRoute, Link } from "@tanstack/react-router";
import {
  FileText,
  LineChart,
  Package,
  ShoppingCart,
  Wallet,
  ArrowRight,
} from "lucide-react";
import { Logo, LogoMark } from "@/components/logo";
import { Button } from "@/components/ui/button";
import { SignedIn, SignedOut } from "@/lib/auth/gates";
import { useCurrentUserState } from "@/lib/auth/use-current-user";

export const Route = createFileRoute("/")({ component: Home });

const FEATURES = [
  {
    icon: Wallet,
    title: "Income and expenses",
    body: "Log every dollar in and out, see profit at a glance, and watch the trend over time.",
  },
  {
    icon: Package,
    title: "Stock and inventory",
    body: "Track quantity, cost, and selling price. Low-stock alerts fire before you run dry.",
  },
  {
    icon: ShoppingCart,
    title: "Sales and customers",
    body: "Record sales against inventory, attach them to customers, and see lifetime spend.",
  },
  {
    icon: FileText,
    title: "Invoices and receipts",
    body: "Create invoices, contracts, and reports. Print a clean copy whenever you need one.",
  },
  {
    icon: Wallet,
    title: "Cash book",
    body: "Keep till cash separate from the income statement — categorized and dated.",
  },
  {
    icon: LineChart,
    title: "Reports and plans",
    body: "Six-month profit trend, top products, SWOT, and a living business plan.",
  },
];

function Home() {
  const { isPending } = useCurrentUserState();

  return (
    <div className="min-h-screen bg-bg text-fg">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <Logo />
        <div className="flex items-center gap-2">
          {isPending ? (
            <div className="h-11 w-24 animate-pulse rounded-sm bg-surface-2" />
          ) : (
            <>
              <SignedOut>
                <Button variant="ghost" asChild>
                  <Link to="/login">Log in</Link>
                </Button>
                <Button asChild>
                  <Link to="/login">Get started</Link>
                </Button>
              </SignedOut>
              <SignedIn>
                <Button asChild>
                  <Link to="/dashboard">
                    Open dashboard
                    <ArrowRight className="size-4" />
                  </Link>
                </Button>
              </SignedIn>
            </>
          )}
        </div>
      </header>

      <section className="relative mx-auto max-w-3xl overflow-hidden px-5 pt-16 pb-12 text-center sm:pt-24">
        <div
          aria-hidden
          className="pointer-events-none absolute top-1/2 left-1/2 size-[28rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand/20"
        />
        <div
          aria-hidden
          className="pointer-events-none absolute top-1/2 left-1/2 size-[22rem] -translate-x-1/2 -translate-y-1/2 rounded-full border border-brand/10"
        />
        <div className="relative kaze-enter">
          <LogoMark className="mx-auto mb-6 size-16" />
          <p className="mb-3 text-[11px] font-medium tracking-[0.22em] text-brand uppercase">
            Business manager
          </p>
          <h1 className="font-display text-4xl leading-[1.1] font-medium tracking-tight sm:text-5xl">
            Run the whole business
            <br />
            from one desk.
          </h1>
          <p className="mx-auto mt-5 max-w-lg text-base text-muted">
            Stock, sales, cash, invoices, budgets, and a plan — kept together so a
            small trading house can see the day clearly.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <SignedOut>
              <Button size="lg" asChild>
                <Link to="/login">Create an account</Link>
              </Button>
              <Button size="lg" variant="secondary" asChild>
                <Link to="/login">Log in</Link>
              </Button>
            </SignedOut>
            <SignedIn>
              <Button size="lg" asChild>
                <Link to="/dashboard">Go to dashboard</Link>
              </Button>
            </SignedIn>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-20">
        <h2 className="mb-6 font-display text-2xl tracking-tight">
          Everything a trading desk needs
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.map((f, i) => (
            <article
              key={f.title}
              className="kaze-enter rounded-xl bg-surface p-6 shadow-[var(--kaze-shadow)] transition-[box-shadow,transform] duration-[var(--motion-fast)] hover:shadow-[var(--kaze-shadow-hover)]"
              style={{ animationDelay: `${i * 40}ms` }}
            >
              <f.icon className="mb-4 size-5 text-brand" strokeWidth={1.75} />
              <h3 className="font-medium text-fg">{f.title}</h3>
              <p className="mt-1.5 text-sm text-muted">{f.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="mx-auto mb-20 max-w-6xl px-5">
        <div className="rounded-2xl bg-surface px-6 py-12 text-center shadow-[var(--kaze-shadow)] sm:px-12">
          <h2 className="font-display text-3xl tracking-tight">Ready to get organized?</h2>
          <p className="mt-2 text-muted">Set up the books in a couple of minutes.</p>
          <div className="mt-6">
            <Button asChild>
              <Link to="/login">
                Open KAZE Traders
                <ArrowRight className="size-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>
    </div>
  );
}
