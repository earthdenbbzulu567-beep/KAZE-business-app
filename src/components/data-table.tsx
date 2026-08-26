import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function DataTable({
  headers,
  children,
  empty,
  colSpan,
}: {
  headers: string[];
  children: ReactNode;
  empty?: boolean;
  colSpan?: number;
}) {
  return (
    <div className="overflow-x-auto rounded-xl bg-surface shadow-[var(--kaze-shadow)]">
      <table className="w-full min-w-[36rem] text-left text-sm">
        <thead>
          <tr className="border-b border-border">
            {headers.map((h) => (
              <th
                key={h}
                className="px-4 py-3 text-[11px] font-medium tracking-[0.12em] text-subtle uppercase"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="[&_tr:last-child_td]:border-b-0">
          {empty ? (
            <tr>
              <td
                colSpan={colSpan ?? headers.length}
                className="px-4 py-10 text-center text-sm text-muted"
              >
                Nothing here yet.
              </td>
            </tr>
          ) : (
            children
          )}
        </tbody>
      </table>
    </div>
  );
}

export function Td({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return (
    <td className={cn("border-b border-border px-4 py-3 text-fg", className)}>
      {children}
    </td>
  );
}

export function Tr({ children }: { children: ReactNode }) {
  return (
    <tr className="transition-colors duration-[var(--motion-quick)] hover:bg-surface-2/60">
      {children}
    </tr>
  );
}
