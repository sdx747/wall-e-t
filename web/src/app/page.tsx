import { MetricsGrid } from "@/components/dashboard/metrics-grid";
import { PnlChart } from "@/components/dashboard/pnl-chart";
import { RecentTrades } from "@/components/dashboard/recent-trades";
import { PositionsSummary } from "@/components/dashboard/positions-summary";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <MetricsGrid />
      <PnlChart />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <PositionsSummary />
        <RecentTrades />
      </div>
    </div>
  );
}
