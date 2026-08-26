import { cn } from "@/lib/utils";

export function LogoMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      className={cn("size-8 shrink-0", className)}
      aria-hidden="true"
    >
      <rect width="32" height="32" rx="8" className="fill-surface-2" />
      <rect
        x="1"
        y="1"
        width="30"
        height="30"
        rx="7"
        className="stroke-brand"
        fill="none"
        strokeWidth="1.5"
      />
      <path
        d="M10 8.5V23.5H13.1V17.2L18.6 23.5H22.4L15.7 15.7L21.9 8.5H18.1L13.1 14.4V8.5H10Z"
        className="fill-fg"
      />
    </svg>
  );
}

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <LogoMark />
      <span className="font-display text-[15px] font-medium tracking-[0.14em] uppercase">
        KAZE
      </span>
    </span>
  );
}
