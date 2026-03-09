import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string;
  subtitle?: string;
  trend?: "up" | "down" | "neutral";
}

export function MetricCard({ title, value, subtitle, trend }: MetricCardProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
      <p className="text-sm text-zinc-400">{title}</p>
      <p
        className={cn(
          "mt-2 text-3xl font-bold font-mono tabular-nums",
          trend === "up" && "text-profit",
          trend === "down" && "text-loss",
          !trend || trend === "neutral" ? "text-zinc-100" : ""
        )}
      >
        {value}
      </p>
      {subtitle && (
        <div className="mt-2 flex items-center gap-1.5 text-sm">
          {trend === "up" && (
            <TrendingUp className="h-3.5 w-3.5 text-profit" />
          )}
          {trend === "down" && (
            <TrendingDown className="h-3.5 w-3.5 text-loss" />
          )}
          {trend === "neutral" && (
            <Minus className="h-3.5 w-3.5 text-zinc-500" />
          )}
          <span
            className={cn(
              trend === "up" && "text-profit",
              trend === "down" && "text-loss",
              (!trend || trend === "neutral") && "text-zinc-500"
            )}
          >
            {subtitle}
          </span>
        </div>
      )}
    </div>
  );
}
