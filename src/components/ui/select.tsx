import { type SelectHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

export const Select = forwardRef<
  HTMLSelectElement,
  SelectHTMLAttributes<HTMLSelectElement>
>(({ className, children, ...props }, ref) => (
  <select
    ref={ref}
    className={cn(
      "flex h-11 w-full appearance-none rounded-md bg-surface-2 bg-[length:12px] bg-[right_12px_center] bg-no-repeat px-3 pr-9 text-sm text-fg shadow-[var(--kaze-shadow)] transition-[box-shadow] duration-[var(--motion-quick)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/70 disabled:cursor-not-allowed disabled:opacity-50",
      className,
    )}
    style={{
      backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' fill='none'><path d='M1 1.5 6 6.5 11 1.5' stroke='%238b928b' stroke-width='1.5' stroke-linecap='round' stroke-linejoin='round'/></svg>")`,
    }}
    {...props}
  >
    {children}
  </select>
));
Select.displayName = "Select";
