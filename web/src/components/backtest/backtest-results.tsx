import type { BacktestResponse } from "@/lib/types";
import { formatINR, formatPercent } from "@/lib/utils";
import { MetricCard } from "@/components/dashboard/metric-card";

interface BacktestResultsProps {
  results: BacktestResponse;
}

export function BacktestResults({ results }: BacktestResultsProps) {
  const returnTrend =
    results.total_return > 0 ? "up" : results.total_return < 0 ? "down" : "neutral";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Total Return"
        value={formatINR(results.total_return)}
        subtitle={formatPercent(results.total_return_pct)}
        trend={returnTrend}
      />
      <MetricCard
        title="CAGR"
        value={formatPercent(results.cagr)}
        trend={results.cagr > 0 ? "up" : results.cagr < 0 ? "down" : "neutral"}
      />
      <MetricCard
        title="Max Drawdown"
        value={formatPercent(results.max_drawdown)}
        trend="down"
      />
      <MetricCard
        title="Sharpe Ratio"
        value={results.sharpe_ratio.toFixed(2)}
        trend={results.sharpe_ratio > 1 ? "up" : "neutral"}
      />
      <MetricCard
        title="Profit Factor"
        value={results.profit_factor.toFixed(2)}
        trend={results.profit_factor > 1 ? "up" : "down"}
      />
      <MetricCard
        title="Win Rate"
        value={`${results.win_rate.toFixed(1)}%`}
        trend={results.win_rate > 50 ? "up" : "down"}
      />
      <MetricCard
        title="Total Trades"
        value={String(results.total_trades)}
        trend="neutral"
      />
      <MetricCard
        title="Avg Win / Loss"
        value={`${formatINR(results.avg_win)} / ${formatINR(results.avg_loss)}`}
        trend="neutral"
      />
    </div>
  );
}
