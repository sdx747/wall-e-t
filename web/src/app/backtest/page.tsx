"use client";

import { useState } from "react";
import type { BacktestResponse } from "@/lib/types";
import { BacktestForm } from "@/components/backtest/backtest-form";
import { BacktestResults } from "@/components/backtest/backtest-results";
import { EquityChart } from "@/components/backtest/equity-chart";
import { BacktestTrades } from "@/components/backtest/backtest-trades";
import { ArrowLeft } from "lucide-react";

export default function BacktestPage() {
  const [results, setResults] = useState<BacktestResponse | null>(null);

  if (results) {
    return (
      <div className="space-y-6">
        <button
          onClick={() => setResults(null)}
          className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 px-4 py-2 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Run Another
        </button>
        <BacktestResults results={results} />
        <EquityChart data={results.equity_curve} />
        <BacktestTrades trades={results.trades} />
      </div>
    );
  }

  return <BacktestForm onResults={setResults} />;
}
