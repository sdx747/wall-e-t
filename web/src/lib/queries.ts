import { useQuery, useMutation } from "@tanstack/react-query";
import { apiFetch } from "./api";
import type {
  DashboardMetrics,
  DailyPnL,
  Position,
  TradeFilter,
  TradeListResponse,
  StrategyInfo,
  StrategyDetail,
  BacktestRequest,
  BacktestResponse,
  ConfigInfo,
} from "./types";

export function useDashboard() {
  return useQuery<DashboardMetrics>({
    queryKey: ["dashboard"],
    queryFn: () => apiFetch("/api/dashboard"),
    refetchInterval: 60000,
  });
}

export function useDailyPnl(days: number = 30) {
  return useQuery<DailyPnL[]>({
    queryKey: ["daily-pnl", days],
    queryFn: () => apiFetch(`/api/dashboard/daily-pnl?days=${days}`),
  });
}

export function usePositions() {
  return useQuery<Position[]>({
    queryKey: ["positions"],
    queryFn: () => apiFetch("/api/positions"),
    refetchInterval: 30000,
  });
}

export function useTrades(filters: TradeFilter) {
  const params = new URLSearchParams();
  if (filters.symbol) params.set("symbol", filters.symbol);
  if (filters.strategy) params.set("strategy", filters.strategy);
  if (filters.start_date) params.set("start_date", filters.start_date);
  if (filters.end_date) params.set("end_date", filters.end_date);
  if (filters.page) params.set("page", String(filters.page));
  if (filters.per_page) params.set("per_page", String(filters.per_page));
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.order) params.set("order", filters.order);

  const queryString = params.toString();
  return useQuery<TradeListResponse>({
    queryKey: ["trades", filters],
    queryFn: () =>
      apiFetch(`/api/trades${queryString ? `?${queryString}` : ""}`),
  });
}

export function useStrategies() {
  return useQuery<StrategyInfo[]>({
    queryKey: ["strategies"],
    queryFn: () => apiFetch("/api/strategies"),
  });
}

export function useStrategyDetail(name: string) {
  return useQuery<StrategyDetail>({
    queryKey: ["strategy", name],
    queryFn: () => apiFetch(`/api/strategies/${name}`),
    enabled: !!name,
  });
}

export function useBacktest() {
  return useMutation<BacktestResponse, Error, BacktestRequest>({
    mutationFn: (data) =>
      apiFetch("/api/backtest", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  });
}

export function useConfig() {
  return useQuery<ConfigInfo>({
    queryKey: ["config"],
    queryFn: () => apiFetch("/api/config"),
  });
}
