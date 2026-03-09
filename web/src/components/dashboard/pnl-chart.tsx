"use client";

import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from "recharts";
import { useDailyPnl } from "@/lib/queries";
import { formatINR } from "@/lib/utils";
import { format, parseISO } from "date-fns";

interface TooltipPayloadEntry {
  dataKey: string;
  value: number;
  color: string;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: TooltipPayloadEntry[];
  label?: string;
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload?.length) return null;

  return (
    <div className="rounded-lg border border-zinc-700 bg-zinc-900 p-3 shadow-xl">
      <p className="text-xs text-zinc-400 mb-2">
        {label ? format(parseISO(label), "dd MMM yyyy") : ""}
      </p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center justify-between gap-4 text-sm">
          <span className="text-zinc-400">
            {entry.dataKey === "pnl" ? "Daily P&L" : "Cumulative"}
          </span>
          <span
            className={`font-mono tabular-nums ${
              entry.value >= 0 ? "text-profit" : "text-loss"
            }`}
          >
            {formatINR(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

function ChartSkeleton() {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <div className="h-5 w-32 bg-zinc-800 animate-pulse rounded mb-6" />
      <div className="h-[350px] bg-zinc-800/30 animate-pulse rounded" />
    </div>
  );
}

export function PnlChart() {
  const { data, isLoading } = useDailyPnl(30);

  if (isLoading) return <ChartSkeleton />;

  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <h3 className="text-sm font-medium text-zinc-400 mb-6">
          P&L Performance
        </h3>
        <div className="flex h-[350px] items-center justify-center text-zinc-500">
          No data available yet
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <h3 className="text-sm font-medium text-zinc-400 mb-6">
        P&L Performance (30 Days)
      </h3>
      <ResponsiveContainer width="100%" height={350}>
        <ComposedChart data={data}>
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#27272a"
            vertical={false}
          />
          <XAxis
            dataKey="date"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#71717a", fontSize: 12 }}
            tickFormatter={(v: string) => {
              try {
                return format(parseISO(v), "dd MMM");
              } catch {
                return v;
              }
            }}
          />
          <YAxis
            yAxisId="bar"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#71717a", fontSize: 12 }}
            tickFormatter={(v: number) =>
              new Intl.NumberFormat("en-IN", {
                notation: "compact",
                compactDisplay: "short",
              }).format(v)
            }
          />
          <YAxis
            yAxisId="line"
            orientation="right"
            axisLine={false}
            tickLine={false}
            tick={{ fill: "#71717a", fontSize: 12 }}
            tickFormatter={(v: number) =>
              new Intl.NumberFormat("en-IN", {
                notation: "compact",
                compactDisplay: "short",
              }).format(v)
            }
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar
            yAxisId="bar"
            dataKey="pnl"
            radius={[2, 2, 0, 0]}
            maxBarSize={24}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.pnl >= 0 ? "#22c55e" : "#ef4444"}
                fillOpacity={0.8}
              />
            ))}
          </Bar>
          <Line
            yAxisId="line"
            type="monotone"
            dataKey="cumulative_pnl"
            stroke="#f59e0b"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, fill: "#f59e0b" }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
