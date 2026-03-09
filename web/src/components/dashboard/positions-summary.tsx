"use client";

import Link from "next/link";
import { usePositions } from "@/lib/queries";
import { formatINR, pnlColor, cn } from "@/lib/utils";
import { ArrowRight } from "lucide-react";

export function PositionsSummary() {
  const { data, isLoading } = usePositions();

  if (isLoading) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="h-5 w-32 bg-zinc-800 animate-pulse rounded mb-4" />
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-8 bg-zinc-800 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  const positions = data || [];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-zinc-400">Open Positions</h3>
        <Link
          href="/positions"
          className="flex items-center gap-1 text-xs text-amber-500 hover:text-amber-400 transition-colors"
        >
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {positions.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-sm text-zinc-500">
          No open positions
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="pb-3 text-left text-xs uppercase tracking-wider text-zinc-500 font-medium">
                  Symbol
                </th>
                <th className="pb-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                  Qty
                </th>
                <th className="pb-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                  Avg Price
                </th>
                <th className="pb-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                  P&L
                </th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr
                  key={`${pos.symbol}-${pos.exchange}`}
                  className="border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors"
                >
                  <td className="py-3 text-zinc-100 font-medium">
                    {pos.symbol}
                  </td>
                  <td className="py-3 text-right text-zinc-300 font-mono tabular-nums">
                    {pos.qty}
                  </td>
                  <td className="py-3 text-right text-zinc-300 font-mono tabular-nums">
                    {formatINR(pos.avg_price)}
                  </td>
                  <td
                    className={cn(
                      "py-3 text-right font-mono tabular-nums",
                      pnlColor(pos.unrealized_pnl)
                    )}
                  >
                    {formatINR(pos.unrealized_pnl)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
