"use client";

import { useState } from "react";
import { useStrategies } from "@/lib/queries";
import type { TradeFilter } from "@/lib/types";
import { X } from "lucide-react";

interface TradeFiltersProps {
  filters: TradeFilter;
  onFilterChange: (filters: TradeFilter) => void;
}

export function TradeFilters({ filters, onFilterChange }: TradeFiltersProps) {
  const { data: strategies } = useStrategies();
  const [symbol, setSymbol] = useState(filters.symbol || "");

  const hasFilters = filters.symbol || filters.strategy || filters.start_date || filters.end_date;

  const handleSymbolSubmit = () => {
    onFilterChange({ ...filters, symbol: symbol || undefined, page: 1 });
  };

  const clearFilters = () => {
    setSymbol("");
    onFilterChange({ page: 1, per_page: filters.per_page, sort: filters.sort, order: filters.order });
  };

  return (
    <div className="flex flex-wrap items-end gap-4 rounded-xl border border-zinc-800 bg-zinc-900 p-4">
      {/* Symbol */}
      <div className="space-y-1.5">
        <label className="text-xs text-zinc-500 uppercase tracking-wider">
          Symbol
        </label>
        <input
          type="text"
          value={symbol}
          onChange={(e) => setSymbol(e.target.value.toUpperCase())}
          onKeyDown={(e) => e.key === "Enter" && handleSymbolSubmit()}
          onBlur={handleSymbolSubmit}
          placeholder="e.g. RELIANCE"
          className="block w-40 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
        />
      </div>

      {/* Strategy */}
      <div className="space-y-1.5">
        <label className="text-xs text-zinc-500 uppercase tracking-wider">
          Strategy
        </label>
        <select
          value={filters.strategy || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              strategy: e.target.value || undefined,
              page: 1,
            })
          }
          className="block w-44 rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
        >
          <option value="">All Strategies</option>
          {strategies?.map((s) => (
            <option key={s.name} value={s.name}>
              {s.name}
            </option>
          ))}
        </select>
      </div>

      {/* Start Date */}
      <div className="space-y-1.5">
        <label className="text-xs text-zinc-500 uppercase tracking-wider">
          Start Date
        </label>
        <input
          type="date"
          value={filters.start_date || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              start_date: e.target.value || undefined,
              page: 1,
            })
          }
          className="block rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500 [color-scheme:dark]"
        />
      </div>

      {/* End Date */}
      <div className="space-y-1.5">
        <label className="text-xs text-zinc-500 uppercase tracking-wider">
          End Date
        </label>
        <input
          type="date"
          value={filters.end_date || ""}
          onChange={(e) =>
            onFilterChange({
              ...filters,
              end_date: e.target.value || undefined,
              page: 1,
            })
          }
          className="block rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500 [color-scheme:dark]"
        />
      </div>

      {/* Clear */}
      {hasFilters && (
        <button
          onClick={clearFilters}
          className="flex items-center gap-1.5 rounded-lg border border-zinc-700 px-3 py-2 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
        >
          <X className="h-3.5 w-3.5" />
          Clear
        </button>
      )}
    </div>
  );
}
