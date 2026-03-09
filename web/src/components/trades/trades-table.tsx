"use client";

import { useState } from "react";
import { useTrades } from "@/lib/queries";
import { formatINR, formatPercent, pnlColor, cn } from "@/lib/utils";
import { format, parseISO } from "date-fns";
import { ChevronUp, ChevronDown, ChevronLeft, ChevronRight } from "lucide-react";
import type { TradeFilter } from "@/lib/types";
import { TradeFilters } from "./trade-filters";

const COLUMNS = [
  { key: "symbol", label: "Symbol", align: "left" as const },
  { key: "side", label: "Side", align: "left" as const },
  { key: "entry_price", label: "Entry", align: "right" as const },
  { key: "exit_price", label: "Exit", align: "right" as const },
  { key: "qty", label: "Qty", align: "right" as const },
  { key: "pnl", label: "P&L", align: "right" as const },
  { key: "pnl_pct", label: "P&L%", align: "right" as const },
  { key: "entry_time", label: "Entry Time", align: "right" as const },
  { key: "exit_time", label: "Exit Time", align: "right" as const },
  { key: "strategy", label: "Strategy", align: "left" as const },
];

function SkeletonTable() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
      <div className="h-8 bg-zinc-800 animate-pulse rounded" />
      {Array.from({ length: 10 }).map((_, i) => (
        <div key={i} className="h-10 bg-zinc-800/50 animate-pulse rounded" />
      ))}
    </div>
  );
}

export function TradesTable() {
  const [filters, setFilters] = useState<TradeFilter>({
    page: 1,
    per_page: 20,
    sort: "exit_time",
    order: "desc",
  });

  const { data, isLoading } = useTrades(filters);

  const handleSort = (key: string) => {
    setFilters((prev) => ({
      ...prev,
      sort: key,
      order: prev.sort === key && prev.order === "desc" ? "asc" : "desc",
      page: 1,
    }));
  };

  const formatDate = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "dd MMM yy HH:mm");
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      <TradeFilters filters={filters} onFilterChange={setFilters} />

      {isLoading ? (
        <SkeletonTable />
      ) : (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-zinc-800">
                  {COLUMNS.map((col) => (
                    <th
                      key={col.key}
                      onClick={() => handleSort(col.key)}
                      className={cn(
                        "px-4 py-3 text-xs uppercase tracking-wider text-zinc-500 font-medium cursor-pointer hover:text-zinc-300 transition-colors select-none",
                        col.align === "right" ? "text-right" : "text-left"
                      )}
                    >
                      <span className="inline-flex items-center gap-1">
                        {col.label}
                        {filters.sort === col.key && (
                          filters.order === "asc" ? (
                            <ChevronUp className="h-3 w-3 text-amber-500" />
                          ) : (
                            <ChevronDown className="h-3 w-3 text-amber-500" />
                          )
                        )}
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(!data?.trades || data.trades.length === 0) ? (
                  <tr>
                    <td colSpan={COLUMNS.length} className="py-16 text-center text-zinc-500">
                      No trades found
                    </td>
                  </tr>
                ) : (
                  data.trades.map((trade) => (
                    <tr
                      key={trade.id}
                      className="border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors"
                    >
                      <td className="px-4 py-3 text-zinc-100 font-medium">
                        {trade.symbol}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={cn(
                            "inline-flex items-center rounded px-1.5 py-0.5 text-xs font-semibold",
                            trade.side === "BUY"
                              ? "bg-green-500/10 text-green-400"
                              : "bg-red-500/10 text-red-400"
                          )}
                        >
                          {trade.side}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                        {formatINR(trade.entry_price)}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                        {formatINR(trade.exit_price)}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                        {trade.qty}
                      </td>
                      <td
                        className={cn(
                          "px-4 py-3 text-right font-mono tabular-nums",
                          pnlColor(trade.pnl)
                        )}
                      >
                        {formatINR(trade.pnl)}
                      </td>
                      <td
                        className={cn(
                          "px-4 py-3 text-right font-mono tabular-nums",
                          pnlColor(trade.pnl_pct)
                        )}
                      >
                        {formatPercent(trade.pnl_pct)}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-400 whitespace-nowrap">
                        {formatDate(trade.entry_time)}
                      </td>
                      <td className="px-4 py-3 text-right text-zinc-400 whitespace-nowrap">
                        {formatDate(trade.exit_time)}
                      </td>
                      <td className="px-4 py-3 text-zinc-400">
                        {trade.strategy}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex items-center justify-between border-t border-zinc-800 px-4 py-3">
              <span className="text-sm text-zinc-500">
                Page {data.page} of {data.total_pages} ({data.total} trades)
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={() =>
                    setFilters((prev) => ({
                      ...prev,
                      page: Math.max(1, (prev.page || 1) - 1),
                    }))
                  }
                  disabled={data.page <= 1}
                  className="rounded-lg border border-zinc-700 p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() =>
                    setFilters((prev) => ({
                      ...prev,
                      page: Math.min(data.total_pages, (prev.page || 1) + 1),
                    }))
                  }
                  disabled={data.page >= data.total_pages}
                  className="rounded-lg border border-zinc-700 p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
