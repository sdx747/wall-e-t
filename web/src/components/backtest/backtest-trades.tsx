import type { BacktestTrade } from "@/lib/types";
import { formatINR, formatPercent, pnlColor, cn } from "@/lib/utils";
import { format, parseISO } from "date-fns";

interface BacktestTradesProps {
  trades: BacktestTrade[];
}

export function BacktestTrades({ trades }: BacktestTradesProps) {
  const formatDate = (dateStr: string) => {
    try {
      return format(parseISO(dateStr), "dd MMM yy HH:mm");
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900">
      <div className="p-4 border-b border-zinc-800">
        <h3 className="text-sm font-medium text-zinc-400">
          Backtest Trades ({trades.length})
        </h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-zinc-800">
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Symbol
              </th>
              <th className="px-4 py-3 text-left text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Side
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Entry
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Exit
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Qty
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                P&L
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                P&L%
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Entry Time
              </th>
              <th className="px-4 py-3 text-right text-xs uppercase tracking-wider text-zinc-500 font-medium">
                Exit Time
              </th>
            </tr>
          </thead>
          <tbody>
            {trades.length === 0 ? (
              <tr>
                <td colSpan={9} className="py-16 text-center text-zinc-500">
                  No trades in backtest
                </td>
              </tr>
            ) : (
              trades.map((trade, idx) => (
                <tr
                  key={idx}
                  className="border-b border-zinc-800/50 hover:bg-zinc-800/50 transition-colors"
                >
                  <td className="px-4 py-3 text-zinc-100 font-medium">
                    {trade.symbol}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={cn(
                        "inline-flex items-center rounded px-1.5 py-0.5 text-xs font-semibold",
                        trade.side === "BUY"
                          ? "bg-green-500/10 text-green-400"
                          : "bg-red-500/10 text-red-400"
                      )}
                    >
                      {trade.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                    {formatINR(trade.entry_price)}
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                    {formatINR(trade.exit_price)}
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-300 font-mono tabular-nums">
                    {trade.qty}
                  </td>
                  <td
                    className={cn(
                      "px-4 py-3 text-right font-mono tabular-nums",
                      pnlColor(trade.pnl)
                    )}
                  >
                    {formatINR(trade.pnl)}
                  </td>
                  <td
                    className={cn(
                      "px-4 py-3 text-right font-mono tabular-nums",
                      pnlColor(trade.pnl_pct)
                    )}
                  >
                    {formatPercent(trade.pnl_pct)}
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-400 whitespace-nowrap">
                    {formatDate(trade.entry_time)}
                  </td>
                  <td className="px-4 py-3 text-right text-zinc-400 whitespace-nowrap">
                    {formatDate(trade.exit_time)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
