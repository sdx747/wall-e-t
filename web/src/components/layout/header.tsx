"use client";

import { usePathname } from "next/navigation";
import { Activity } from "lucide-react";
import { cn } from "@/lib/utils";

const pageTitles: Record<string, string> = {
  "/": "Dashboard",
  "/positions": "Positions",
  "/trades": "Trades",
  "/backtest": "Backtest",
  "/strategies": "Strategies",
};

function getMarketStatus(): { label: string; open: boolean } {
  const now = new Date();
  // Convert to IST (UTC+5:30)
  const istOffset = 5.5 * 60 * 60 * 1000;
  const ist = new Date(now.getTime() + istOffset + now.getTimezoneOffset() * 60 * 1000);
  const hours = ist.getHours();
  const minutes = ist.getMinutes();
  const day = ist.getDay();

  // Market open: Mon-Fri, 9:15 AM - 3:30 PM IST
  const timeInMinutes = hours * 60 + minutes;
  const marketOpen = 9 * 60 + 15;
  const marketClose = 15 * 60 + 30;

  if (day >= 1 && day <= 5 && timeInMinutes >= marketOpen && timeInMinutes < marketClose) {
    return { label: "Market Open", open: true };
  }
  return { label: "Market Closed", open: false };
}

export function Header() {
  const pathname = usePathname();
  const title = pageTitles[pathname] || "Dashboard";
  const market = getMarketStatus();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-zinc-800 bg-zinc-950/50 backdrop-blur-sm px-6 lg:px-8">
      {/* Left: page title (with left padding on mobile for hamburger) */}
      <h1 className="text-lg font-semibold text-zinc-100 pl-10 lg:pl-0">
        {title}
      </h1>

      {/* Right: market status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          <Activity
            className={cn(
              "h-3.5 w-3.5",
              market.open ? "text-profit" : "text-zinc-500"
            )}
          />
          <span
            className={cn(
              market.open ? "text-profit" : "text-zinc-500"
            )}
          >
            {market.label}
          </span>
        </div>
      </div>
    </header>
  );
}
