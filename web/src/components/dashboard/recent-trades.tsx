"use client";

import Link from "next/link";
import { useTrades } from "@/lib/queries";
import { formatINR, pnlColor, cn } from "@/lib/utils";
import { format, parseISO } from "date-fns";
import { ArrowRight } from "lucide-react";

export function RecentTrades() {
  const { data, isLoading } = useTrades({
    per_page: 5,
    sort: "exit_time",
    order: "desc",
  });

  if (isLoading) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="h-5 w-28 bg-zinc-800 animate-pulse rounded mb-4" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-8 bg-zinc-800 animate-pulse rounded" />
          ))}
        </div>
      </div>
    );
  }

  const trades = data?.trades || [];

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-zinc-400">Recent Trades</h3>
        <Link
          href="/trades"
          className="flex items-center gap-1 text-xs text-amber-500 hover:text-amber-400 transition-colors"
        >
          View all <ArrowRight className="h-3 w-3" />
        </Link>
      </div>

      {trades.length === 0 ? (
        <div className="flex h-32 items-center justify-center text-sm text-zinc-500">
          No trades yet
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
                  P&L
                </th>
                <th className="pb-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                  Date
                </th>
              </tr>
            </thead>
            <tbody>
              {trades.map((trade) => (
                <tr
                  key={trade.id}
                  className="border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors"
                >
                  <td className="py-3 text-zinc-100 font-medium">
                    {trade.symbol}
                  </td>
                  <td
                    className={cn(
                      "py-3 text-right font-mono tabular-nums",
                      pnlColor(trade.pnl)
                    )}
                  >
                    {formatINR(trade.pnl)}
                  </td>
                  <td className="py-3 text-right text-zinc-400">
                    {(() => {
                      try {
                        return format(parseISO(trade.exit_time), "dd MMM");
                      } catch {
                        return trade.exit_time;
                      }
                    })()}
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
