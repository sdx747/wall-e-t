import type { StrategyInfo } from "@/lib/types";
import { cn } from "@/lib/utils";

interface StrategyCardProps {
  strategy: StrategyInfo;
}

export function StrategyCard({ strategy }: StrategyCardProps) {
  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-base font-semibold text-zinc-100">
            {strategy.name}
          </h3>
        </div>
        <div
          className={cn(
            "h-2.5 w-2.5 rounded-full mt-1",
            strategy.active ? "bg-green-500" : "bg-zinc-600"
          )}
          title={strategy.active ? "Active" : "Inactive"}
        />
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-2">
        <span className="inline-flex items-center rounded-md bg-zinc-800 px-2 py-1 text-xs font-medium text-zinc-300 ring-1 ring-inset ring-zinc-700">
          v{strategy.version}
        </span>
        <span className="inline-flex items-center rounded-md bg-amber-500/10 px-2 py-1 text-xs font-medium text-amber-400 ring-1 ring-inset ring-amber-500/20">
          {strategy.style}
        </span>
        <span className="inline-flex items-center rounded-md bg-zinc-800 px-2 py-1 text-xs font-medium text-zinc-300 ring-1 ring-inset ring-zinc-700">
          {strategy.timeframe}
        </span>
      </div>

      {/* Watchlist */}
      {strategy.watchlist && strategy.watchlist.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-zinc-500 uppercase tracking-wider">
            Watchlist
          </p>
          <div className="flex flex-wrap gap-1.5">
            {strategy.watchlist.map((sym) => (
              <span
                key={sym}
                className="inline-flex items-center rounded bg-zinc-800/60 px-2 py-0.5 text-xs text-zinc-400"
              >
                {sym}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
