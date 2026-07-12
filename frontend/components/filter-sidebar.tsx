"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { SOURCE_META, STATUS_META, ALL_SOURCES } from "@/lib/constants";
import type { Filters, Source, DashboardData } from "@/lib/types";

interface Props {
  filters: Filters;
  onChange: (f: Filters) => void;
  data: DashboardData | null;
  scraping: boolean;
  onRefresh: () => void;
  total: number;
  filtered: number;
  visibleSources?: Source[];
  mobileOpen?: boolean;
  onClose?: () => void;
}

const ALL_STATUSES = ["upcoming", "ongoing", "past"] as const;

export function FilterSidebar({
  filters, onChange, data, scraping, onRefresh, total, filtered,
  visibleSources = ALL_SOURCES, mobileOpen = false, onClose,
}: Props) {
  const pathname = usePathname();

  function toggleSource(s: string) {
    const next = filters.sources.includes(s as Source)
      ? filters.sources.filter((x) => x !== s)
      : [...filters.sources, s as Source];
    onChange({ ...filters, sources: next });
  }

  function toggleStatus(s: string) {
    const next = filters.statuses.includes(s as never)
      ? filters.statuses.filter((x) => x !== s)
      : [...filters.statuses, s as never];
    onChange({ ...filters, statuses: next });
  }

  const stats = data?.stats;

  const navItems = [
    {
      href: "/",
      label: "Hackathons",
      icon: (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
        </svg>
      ),
    },
    {
      href: "/twitter",
      label: "Twitter Sources",
      icon: (
        <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
        </svg>
      ),
    },
  ];

  return (
    <aside
      className={`fixed top-0 left-0 h-screen overflow-y-auto flex flex-col gap-5 py-5 px-4 z-40 transition-transform duration-200 lg:translate-x-0 ${
        mobileOpen ? "translate-x-0" : "-translate-x-full"
      }`}
      style={{ width: "var(--sidebar-width, 260px)", borderRight: "1px solid rgba(63,63,70,0.5)", backgroundColor: "#09090b" }}
    >
      {/* Logo / Title */}
      <div className="flex items-start justify-between px-1">
        <div>
          <h1 className="text-base font-semibold text-zinc-100 tracking-tight">Hacklist</h1>
          <p className="text-[11px] text-zinc-500 mt-0.5">Online-only · auto-refreshed daily</p>
        </div>
        {/* Close (mobile only) */}
        <button
          onClick={onClose}
          aria-label="Close menu"
          className="lg:hidden -mr-1 -mt-1 p-1.5 rounded-lg text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/60 transition-colors"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Nav */}
      <nav className="flex flex-col gap-1">
        {navItems.map(({ href, label, icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className="flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-xs font-medium transition-all duration-150"
              style={{
                backgroundColor: active ? "rgba(99,102,241,0.12)" : "transparent",
                color: active ? "#a5b4fc" : "#71717a",
                border: `1px solid ${active ? "rgba(99,102,241,0.25)" : "transparent"}`,
              }}
            >
              {icon}
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Stats row */}
      {stats && (
        <div className="grid grid-cols-3 gap-1.5">
          {(["upcoming", "ongoing", "past"] as const).map((s) => {
            const meta = STATUS_META[s];
            return (
              <div
                key={s}
                className="flex flex-col items-center py-2 rounded-lg"
                style={{ backgroundColor: meta.bg, border: `1px solid ${meta.color}25` }}
              >
                <span className="text-sm font-bold" style={{ color: meta.color }}>
                  {stats.by_status[s] ?? 0}
                </span>
                <span className="text-[10px] text-zinc-500 capitalize">{s}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Search */}
      <div>
        <label className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block mb-2">Search</label>
        <div className="relative">
          <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
          </svg>
          <input
            type="text"
            placeholder="Search hackathons…"
            value={filters.search}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
            className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg bg-zinc-800/60 border border-zinc-700/60 text-zinc-200 placeholder-zinc-600 outline-none focus:border-zinc-500 transition-colors"
          />
        </div>
      </div>

      {/* Source filter */}
      {visibleSources.length > 1 && (
        <div>
          <label className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block mb-2">Sources</label>
          <div className="flex flex-col gap-1.5">
            {visibleSources.map((s) => {
              const meta = SOURCE_META[s];
              const count = stats?.by_source[s] ?? 0;
              const active = filters.sources.includes(s);
              return (
                <button
                  key={s}
                  onClick={() => toggleSource(s)}
                  className="flex items-center justify-between w-full px-2.5 py-1.5 rounded-lg text-xs transition-all duration-150"
                  style={{
                    backgroundColor: active ? `${meta.color}14` : "rgba(39,39,42,0.4)",
                    border: `1px solid ${active ? meta.color + "35" : "rgba(63,63,70,0.5)"}`,
                    color: active ? meta.color : "#a1a1aa",
                  }}
                >
                  <span className="flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ backgroundColor: active ? meta.color : "#52525b" }}
                    />
                    {meta.label}
                  </span>
                  <span className="text-[10px] font-mono" style={{ color: active ? meta.color : "#52525b" }}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Status filter */}
      <div>
        <label className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block mb-2">Status</label>
        <div className="flex flex-col gap-1.5">
          {ALL_STATUSES.map((s) => {
            const meta = STATUS_META[s];
            const active = filters.statuses.includes(s);
            return (
              <button
                key={s}
                onClick={() => toggleStatus(s)}
                className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-lg text-xs transition-all duration-150"
                style={{
                  backgroundColor: active ? `${meta.color}12` : "rgba(39,39,42,0.4)",
                  border: `1px solid ${active ? meta.color + "30" : "rgba(63,63,70,0.5)"}`,
                  color: active ? meta.color : "#a1a1aa",
                }}
              >
                <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: active ? meta.color : "#52525b" }} />
                {meta.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Prize toggle */}
      <div>
        <label className="text-[11px] font-medium text-zinc-400 uppercase tracking-wider block mb-2">Prize</label>
        <button
          onClick={() => onChange({ ...filters, has_prize: !filters.has_prize })}
          className="flex items-center gap-2 w-full px-2.5 py-1.5 rounded-lg text-xs transition-all duration-150"
          style={{
            backgroundColor: filters.has_prize ? "rgba(245,158,11,0.1)" : "rgba(39,39,42,0.4)",
            border: `1px solid ${filters.has_prize ? "rgba(245,158,11,0.3)" : "rgba(63,63,70,0.5)"}`,
            color: filters.has_prize ? "#f59e0b" : "#a1a1aa",
          }}
        >
          <span className="text-base leading-none">{filters.has_prize ? "★" : "☆"}</span>
          Has prize money
        </button>
      </div>

      {/* Result count */}
      <div className="text-[11px] text-zinc-600 px-1">
        Showing {filtered} of {total}
      </div>

      <div className="flex-1" />

      {/* Refresh section */}
      <div className="border-t border-zinc-800/60 pt-4 flex flex-col gap-3">
        {data?.sources && (
          <div className="flex flex-col gap-1">
            {Object.entries(data.sources)
              .filter(([src]) => visibleSources.includes(src as Source))
              .map(([src, info]) => {
                const meta = SOURCE_META[src as Source];
                if (!meta) return null;
                const lastScraped = info.last_scraped
                  ? new Date(info.last_scraped).toLocaleDateString("en-US", { month: "short", day: "numeric" })
                  : "never";
                return (
                  <div key={src} className="flex items-center justify-between text-[10px] text-zinc-600">
                    <span style={{ color: meta.color + "cc" }}>{meta.label}</span>
                    <span>{lastScraped}</span>
                  </div>
                );
              })}
          </div>
        )}
        <button
          onClick={onRefresh}
          disabled={scraping}
          className="flex items-center justify-center gap-2 w-full py-2 rounded-lg text-xs font-medium transition-all duration-150 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            backgroundColor: scraping ? "rgba(99,102,241,0.08)" : "rgba(99,102,241,0.12)",
            border: "1px solid rgba(99,102,241,0.3)",
            color: scraping ? "#818cf8" : "#a5b4fc",
          }}
        >
          {scraping ? (
            <>
              <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Scraping…
            </>
          ) : (
            <>
              <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
              </svg>
              Refresh now
            </>
          )}
        </button>
      </div>
    </aside>
  );
}
