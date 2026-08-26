import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

export function Badge({
  className,
  tone = "neutral",
  ...props
}: HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "in" | "out" | "warn" | "brand";
}) {
  const tones = {
    neutral: "bg-surface-2 text-muted",
    in: "bg-in/15 text-in",
    out: "bg-out/15 text-out",
    warn: "bg-warn/15 text-warn",
    brand: "bg-brand/15 text-brand",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-medium tracking-wide",
        tones[tone],
        className,
      )}
      {...props}
    />
  );
}
