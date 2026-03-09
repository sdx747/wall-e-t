"use client";

import { usePositions } from "@/lib/queries";
import { formatINR, formatPercent, pnlColor, cn } from "@/lib/utils";
import { format, parseISO } from "date-fns";
import { Briefcase } from "lucide-react";

function SkeletonTable() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
      <div className="h-8 bg-zinc-800 animate-pulse rounded" />
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-10 bg-zinc-800/50 animate-pulse rounded" />
      ))}
    </div>
  );
}

export function PositionsTable() {
  const { data, isLoading } = usePositions();

  if (isLoading) return <SkeletonTable />;

  const positions = data || [];

  if (positions.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="flex flex-col items-center justify-center py-16 text-zinc-500">
          <Briefcase className="h-10 w-10 mb-3 text-zinc-600" />
          <p className="text-sm">No open positions</p>
          <p className="text-xs text-zinc-600 mt-1">
            Positions will appear here when trades are active
          </p>
        </div>
      </div>
    );
  }

  const formatDate = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "dd MMM yy HH:mm");
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Symbol
              </th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Exchange
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Qty
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Avg Price
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Current Price
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Unrealized P&L
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                P&L%
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Entry Time
              </th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Strategy
              </th>
            </tr>
          </thead>
          <tbody>
            {positions.map((pos) => (
              <tr
                key={`${pos.symbol}-${pos.exchange}-${pos.entry_time}`}
                className="border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors"
              >
                <td className="px-4 py-3 text-zinc-100 font-medium">
                  {pos.symbol}
                </td>
                <td className="px-4 py-3 text-zinc-400">{pos.exchange}</td>
                <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                  {pos.qty}
                </td>
                <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                  {formatINR(pos.avg_price)}
                </td>
                <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                  {formatINR(pos.current_price)}
                </td>
                <td
                  className={cn(
                    "px-4 py-3 text-right font-mono tabular-nums",
                    pnlColor(pos.unrealized_pnl)
                  )}
                >
                  {formatINR(pos.unrealized_pnl)}
                </td>
                <td
                  className={cn(
                    "px-4 py-3 text-right font-mono tabular-nums",
                    pnlColor(pos.pnl_pct)
                  )}
                >
                  {formatPercent(pos.pnl_pct)}
                </td>
                <td className="px-4 py-3 text-right text-zinc-400 whitespace-nowrap">
                  {formatDate(pos.entry_time)}
                </td>
                <td className="px-4 py-3 text-zinc-400">{pos.strategy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
