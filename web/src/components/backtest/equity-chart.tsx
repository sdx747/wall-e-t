"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import type { EquityPoint } from "@/lib/types";
import { formatINR } from "@/lib/utils";
import { format, parseISO } from "date-fns";

interface TooltipPayloadEntry {
  value: number;
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
      <p className="text-xs text-zinc-400 mb-1">
        {label ? format(parseISO(label), "dd MMM yyyy") : ""}
      </p>
      <p className="text-sm font-mono tabular-nums text-amber-500">
        {formatINR(payload[0].value)}
      </p>
    </div>
  );
}

interface EquityChartProps {
  data: EquityPoint[];
}

export function EquityChart({ data }: EquityChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <h3 className="text-sm font-medium text-zinc-400 mb-6">
          Equity Curve
        </h3>
        <div className="flex h-[350px] items-center justify-center text-zinc-500">
          No equity data
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <h3 className="text-sm font-medium text-zinc-400 mb-6">Equity Curve</h3>
      <ResponsiveContainer width="100%" height={350}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
            </linearGradient>
          </defs>
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
          <Area
            type="monotone"
            dataKey="equity"
            stroke="#f59e0b"
            strokeWidth={2}
            fill="url(#equityGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
