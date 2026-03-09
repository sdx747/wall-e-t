"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  Bot,
  LayoutDashboard,
  Briefcase,
  History,
  FlaskConical,
  Blocks,
  Menu,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useConfig } from "@/lib/queries";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/positions", label: "Positions", icon: Briefcase },
  { href: "/trades", label: "Trades", icon: History },
  { href: "/backtest", label: "Backtest", icon: FlaskConical },
  { href: "/strategies", label: "Strategies", icon: Blocks },
];

export function Sidebar() {
  const pathname = usePathname();
  const { data: config } = useConfig();
  const [mobileOpen, setMobileOpen] = useState(false);

  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* Logo */}
      <div className="flex h-14 items-center gap-3 border-b border-zinc-800 px-6">
        <Bot className="h-6 w-6 text-amber-500" />
        <span className="text-lg font-bold tracking-tight text-zinc-100">
          Wall-E-T
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive =
            pathname === item.href ||
            (item.href !== "/" && pathname.startsWith(item.href));
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={() => setMobileOpen(false)}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-amber-500/10 text-amber-500"
                  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100"
              )}
            >
              <item.icon className="h-4 w-4" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Bottom section */}
      <div className="border-t border-zinc-800 px-4 py-4 space-y-3">
        {config && (
          <div className="flex items-center justify-between">
            <span
              className={cn(
                "inline-flex items-center rounded-md px-2 py-1 text-xs font-semibold ring-1 ring-inset",
                config.mode === "LIVE"
                  ? "bg-red-500/10 text-red-400 ring-red-500/20"
                  : "bg-amber-500/10 text-amber-400 ring-amber-500/20"
              )}
            >
              {config.mode}
            </span>
            <span className="text-xs text-zinc-600">v{config.version}</span>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile hamburger button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="fixed left-4 top-3.5 z-50 rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100 lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Mobile sidebar */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-60 bg-zinc-950 border-r border-zinc-800 transform transition-transform duration-200 lg:hidden",
          mobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <button
          onClick={() => setMobileOpen(false)}
          className="absolute right-3 top-3.5 rounded-lg p-1.5 text-zinc-400 hover:bg-zinc-800 hover:text-zinc-100"
        >
          <X className="h-4 w-4" />
        </button>
        {sidebarContent}
      </aside>

      {/* Desktop sidebar */}
      <aside className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:flex lg:w-60 lg:flex-col bg-zinc-950 border-r border-zinc-800">
        {sidebarContent}
      </aside>
    </>
  );
}
