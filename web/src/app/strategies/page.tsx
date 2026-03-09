"use client";

import { useStrategies } from "@/lib/queries";
import { StrategyCard } from "@/components/strategies/strategy-card";
import { Blocks } from "lucide-react";

export default function StrategiesPage() {
  const { data, isLoading } = useStrategies();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={i}
            className="rounded-xl border border-zinc-800 bg-zinc-900 p-6 space-y-4"
          >
            <div className="h-5 w-32 bg-zinc-800 animate-pulse rounded" />
            <div className="h-4 w-48 bg-zinc-800 animate-pulse rounded" />
            <div className="flex gap-2">
              <div className="h-6 w-12 bg-zinc-800 animate-pulse rounded" />
              <div className="h-6 w-16 bg-zinc-800 animate-pulse rounded" />
              <div className="h-6 w-14 bg-zinc-800 animate-pulse rounded" />
            </div>
            <div className="h-16 bg-zinc-800/50 animate-pulse rounded" />
          </div>
        ))}
      </div>
    );
  }

  const strategies = data || [];

  if (strategies.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-6">
        <div className="flex flex-col items-center justify-center py-16 text-zinc-500">
          <Blocks className="h-10 w-10 mb-3 text-zinc-600" />
          <p className="text-sm">No strategies configured</p>
          <p className="text-xs text-zinc-600 mt-1">
            Strategies will appear here once configured in the backend
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {strategies.map((strategy) => (
        <StrategyCard key={strategy.name} strategy={strategy} />
      ))}
    </div>
  );
}
