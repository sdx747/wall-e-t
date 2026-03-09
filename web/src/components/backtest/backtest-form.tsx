"use client";

import { useState } from "react";
import { useStrategies, useBacktest } from "@/lib/queries";
import type { BacktestResponse } from "@/lib/types";
import { Loader2 } from "lucide-react";

interface BacktestFormProps {
  onResults: (results: BacktestResponse) => void;
}

export function BacktestForm({ onResults }: BacktestFormProps) {
  const { data: strategies, isLoading: loadingStrategies } = useStrategies();
  const backtest = useBacktest();

  const [strategy, setStrategy] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [capital, setCapital] = useState(100000);

  const canSubmit = strategy && startDate && endDate && capital > 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    backtest.mutate(
      {
        strategy,
        start_date: startDate,
        end_date: endDate,
        capital,
      },
      {
        onSuccess: (data) => onResults(data),
      }
    );
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-6">
        <h3 className="text-lg font-semibold text-zinc-100">
          Configure Backtest
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {/* Strategy */}
          <div className="space-y-2">
            <label className="text-xs text-zinc-500 uppercase tracking-wider">
              Strategy
            </label>
            <select
              value={strategy}
              onChange={(e) => setStrategy(e.target.value)}
              disabled={loadingStrategies}
              className="block w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            >
              <option value="">Select a strategy</option>
              {strategies?.map((s) => (
                <option key={s.name} value={s.name}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>

          {/* Capital */}
          <div className="space-y-2">
            <label className="text-xs text-zinc-500 uppercase tracking-wider">
              Capital (INR)
            </label>
            <input
              type="number"
              value={capital}
              onChange={(e) => setCapital(Number(e.target.value))}
              min={1000}
              step={1000}
              className="block w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 font-mono focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500"
            />
          </div>

          {/* Start Date */}
          <div className="space-y-2">
            <label className="text-xs text-zinc-500 uppercase tracking-wider">
              Start Date
            </label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="block w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500 [color-scheme:dark]"
            />
          </div>

          {/* End Date */}
          <div className="space-y-2">
            <label className="text-xs text-zinc-500 uppercase tracking-wider">
              End Date
            </label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="block w-full rounded-lg border border-zinc-700 bg-zinc-900 px-3 py-2.5 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-amber-500 focus:border-amber-500 [color-scheme:dark]"
            />
          </div>
        </div>

        {backtest.isError && (
          <div className="rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-sm text-red-400">
            {backtest.error.message}
          </div>
        )}

        <button
          type="submit"
          disabled={!canSubmit || backtest.isPending}
          className="inline-flex items-center gap-2 rounded-lg bg-amber-500 px-6 py-2.5 text-sm font-medium text-zinc-950 hover:bg-amber-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {backtest.isPending && (
            <Loader2 className="h-4 w-4 animate-spin" />
          )}
          {backtest.isPending ? "Running..." : "Run Backtest"}
        </button>
      </div>
    </form>
  );
}
