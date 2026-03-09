"use client";

import { useDashboard } from "@/lib/queries";
import { formatINR, formatPercent } from "@/lib/utils";
import { MetricCard } from "./metric-card";

function SkeletonCard() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-3">
      <div className="h-4 w-24 bg-zinc-800 animate-pulse rounded" />
      <div className="h-8 w-32 bg-zinc-800 animate-pulse rounded" />
      <div className="h-4 w-20 bg-zinc-800 animate-pulse rounded" />
    </div>
  );
}

export function MetricsGrid() {
  const { data, isLoading } = useDashboard();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (!data) return null;

  const totalTrend =
    data.total_pnl > 0 ? "up" : data.total_pnl < 0 ? "down" : "neutral";
  const todayTrend =
    data.today_pnl > 0 ? "up" : data.today_pnl < 0 ? "down" : "neutral";

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
      <MetricCard
        title="Total P&L"
        value={formatINR(data.total_pnl)}
        subtitle={formatPercent(data.total_pnl_pct)}
        trend={totalTrend}
      />
      <MetricCard
        title="Today's P&L"
        value={formatINR(data.today_pnl)}
        subtitle={formatPercent(data.today_pnl_pct)}
        trend={todayTrend}
      />
      <MetricCard
        title="Win Rate"
        value={`${data.win_rate.toFixed(1)}%`}
        subtitle={`${data.winning_trades}W / ${data.losing_trades}L`}
        trend="neutral"
      />
      <MetricCard
        title="Open Positions"
        value={String(data.open_positions)}
        subtitle={`${formatINR(data.capital_deployed)} deployed`}
        trend="neutral"
      />
    </div>
  );
}
