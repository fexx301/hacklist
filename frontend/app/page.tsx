"use client";

import { useState, useEffect, useCallback, useRef, useMemo, Suspense } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { FilterSidebar } from "@/components/filter-sidebar";
import { HackathonCard } from "@/components/hackathon-card";
import { fetchHackathons, fetchStats, triggerRefresh, fetchScrapeStatus } from "@/lib/api";
import type { Hackathon, Filters, DashboardData } from "@/lib/types";
import { ALL_SOURCES, SOURCE_META, STATUS_META } from "@/lib/constants";
import type { Source, Status } from "@/lib/types";
import { SORT_OPTIONS, sortHackathons, type SortKey } from "@/lib/sort";
import { useDebounce } from "@/lib/use-debounce";
import { encodeFilters, decodeFilters } from "@/lib/url-filters";

const MAIN_SOURCES: Source[] = ALL_SOURCES.filter((s) => s !== "twitter");

const DEFAULT_FILTERS: Filters = {
  sources: [...MAIN_SOURCES],
  statuses: ["upcoming", "ongoing"],
  search: "",
  has_prize: false,
};

function isDefaultFilters(f: Filters): boolean {
  return (
    f.search === "" &&
    !f.has_prize &&
    f.sources.length === MAIN_SOURCES.length &&
    f.statuses.length === 2 &&
    f.statuses.includes("upcoming") &&
    f.statuses.includes("ongoing")
  );
}

export default function DashboardPage() {
  // useSearchParams requires a Suspense boundary above it for static builds.
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#09090b]" />}>
      <Dashboard />
    </Suspense>
  );
}

function Dashboard() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Seed initial state from the URL (lazy initializer runs once on mount).
  const [initial] = useState(() =>
    decodeFilters(new URLSearchParams(searchParams.toString()), DEFAULT_FILTERS, {
      includeSources: true,
    }),
  );

  const [filters, setFilters] = useState<Filters>(initial.filters);
  const [sort, setSort] = useState<SortKey>(initial.sort);
  const [hackathons, setHackathons] = useState<Hackathon[]>([]);
  const [dashData, setDashData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scraping, setScraping] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Debounce so typing in search / rapid toggles don't spam the API.
  const debouncedFilters = useDebounce(filters, 250);

  const loadHackathons = useCallback(async (f: Filters) => {
    try {
      const data = await fetchHackathons(f);
      setHackathons(data);
      setError(null);
    } catch {
      setError("Could not load hackathons. Is the API running on port 8001?");
    }
  }, []);

  const loadStats = useCallback(async () => {
    try {
      const data = await fetchStats();
      setDashData(data);
    } catch {
      // stats are non-critical
    }
  }, []);

  // Initial load — uses whatever filters the URL seeded.
  useEffect(() => {
    (async () => {
      setLoading(true);
      await Promise.all([loadHackathons(initial.filters), loadStats()]);
      setLoading(false);
    })();
  }, [initial, loadHackathons, loadStats]);

  // Re-fetch hackathons when (debounced) filters change (skip first mount)
  const isFirstMount = useRef(true);
  useEffect(() => {
    if (isFirstMount.current) { isFirstMount.current = false; return; }
    loadHackathons(debouncedFilters);
  }, [debouncedFilters, loadHackathons]);

  // Keep the URL in sync with the active view so it's shareable/refresh-safe.
  useEffect(() => {
    const qs = encodeFilters(debouncedFilters, sort, DEFAULT_FILTERS, { includeSources: true });
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }, [debouncedFilters, sort, router, pathname]);

  // Poll scraping status while scraping
  useEffect(() => {
    if (!scraping) return;
    pollRef.current = setInterval(async () => {
      try {
        const { scraping: s } = await fetchScrapeStatus();
        if (!s) {
          setScraping(false);
          await Promise.all([loadHackathons(filters), loadStats()]);
          clearInterval(pollRef.current!);
        }
      } catch { /* ignore */ }
    }, 3000);
    return () => clearInterval(pollRef.current!);
  }, [scraping, filters, loadHackathons, loadStats]);

  async function handleRefresh() {
    if (scraping) return;
    try {
      const res = await triggerRefresh();
      if (res.status !== "already_running") setScraping(true);
    } catch {
      setError("Failed to trigger refresh.");
    }
  }

  const sorted = useMemo(() => sortHackathons(hackathons, sort), [hackathons, sort]);
  const totalAll = dashData?.stats.total ?? hackathons.length;
  const showChips = !isDefaultFilters(filters);

  function removeSource(s: Source) {
    setFilters((f) => ({ ...f, sources: f.sources.filter((x) => x !== s) }));
  }
  function removeStatus(s: Status) {
    setFilters((f) => ({ ...f, statuses: f.statuses.filter((x) => x !== s) }));
  }

  return (
    <div className="flex min-h-screen lg:pl-[var(--sidebar-width,260px)]">
      {/* Mobile backdrop */}
      {menuOpen && (
        <div
          onClick={() => setMenuOpen(false)}
          className="fixed inset-0 z-30 bg-black/60 lg:hidden"
          aria-hidden
        />
      )}

      <FilterSidebar
        filters={filters}
        onChange={setFilters}
        data={dashData}
        scraping={scraping}
        onRefresh={handleRefresh}
        total={totalAll}
        filtered={hackathons.length}
        visibleSources={MAIN_SOURCES}
        mobileOpen={menuOpen}
        onClose={() => setMenuOpen(false)}
      />

      {/* Main content */}
      <main className="flex-1 min-w-0 py-6 px-4 sm:py-8 sm:px-6 lg:px-8">
        {/* Header bar */}
        <div className="flex items-center justify-between gap-3 mb-6">
          <div className="flex items-center gap-3 min-w-0">
            {/* Hamburger (mobile) */}
            <button
              onClick={() => setMenuOpen(true)}
              aria-label="Open menu"
              className="lg:hidden flex-shrink-0 p-2 -ml-1 rounded-lg text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>
            <div className="min-w-0">
              <h2 className="text-lg font-semibold text-zinc-100 truncate">
                {hackathons.length > 0 ? `${hackathons.length} hackathons` : "Hackathons"}
              </h2>
              <p className="text-xs text-zinc-500 mt-0.5 truncate">
                {filters.statuses.length === 0
                  ? "All statuses"
                  : filters.statuses.map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(", ")}
                {filters.search ? ` · "${filters.search}"` : ""}
                {filters.has_prize ? " · With prize" : ""}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            {scraping && (
              <div className="hidden sm:flex items-center gap-2 text-xs text-indigo-400 bg-indigo-500/10 border border-indigo-500/20 px-3 py-1.5 rounded-lg">
                <svg className="w-3 h-3 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Scraping sources…
              </div>
            )}

            {/* Sort control */}
            <label className="flex items-center gap-2 text-xs text-zinc-500">
              <span className="hidden sm:inline">Sort</span>
              <select
                value={sort}
                onChange={(e) => setSort(e.target.value as SortKey)}
                className="bg-zinc-800/60 border border-zinc-700/60 text-zinc-200 text-xs rounded-lg pl-2.5 pr-7 py-1.5 outline-none focus:border-zinc-500 transition-colors cursor-pointer"
              >
                {SORT_OPTIONS.map((o) => (
                  <option key={o.key} value={o.key}>{o.label}</option>
                ))}
              </select>
            </label>
          </div>
        </div>

        {/* Active filter chips */}
        {showChips && (
          <div className="flex flex-wrap items-center gap-2 mb-6">
            {filters.sources.length < MAIN_SOURCES.length &&
              filters.sources.map((s) => (
                <FilterChip key={`src-${s}`} color={SOURCE_META[s].color} onRemove={() => removeSource(s)}>
                  {SOURCE_META[s].label}
                </FilterChip>
              ))}
            {filters.statuses.map((s) => (
              <FilterChip key={`sts-${s}`} color={STATUS_META[s].color} onRemove={() => removeStatus(s)}>
                {STATUS_META[s].label}
              </FilterChip>
            ))}
            {filters.search && (
              <FilterChip color="#a1a1aa" onRemove={() => setFilters((f) => ({ ...f, search: "" }))}>
                &ldquo;{filters.search}&rdquo;
              </FilterChip>
            )}
            {filters.has_prize && (
              <FilterChip color="#f59e0b" onRemove={() => setFilters((f) => ({ ...f, has_prize: false }))}>
                Has prize
              </FilterChip>
            )}
            <button
              onClick={() => setFilters(DEFAULT_FILTERS)}
              className="text-xs text-zinc-500 hover:text-zinc-200 underline underline-offset-2 transition-colors ml-1"
            >
              Clear all
            </button>
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div className="mb-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Loading skeletons */}
        {loading && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="rounded-xl bg-zinc-900 border border-zinc-800/60 overflow-hidden animate-pulse">
                <div className="h-36 bg-zinc-800/60" />
                <div className="p-4 flex flex-col gap-3">
                  <div className="h-3 w-16 rounded bg-zinc-800" />
                  <div className="h-4 w-full rounded bg-zinc-800" />
                  <div className="h-3 w-4/5 rounded bg-zinc-800" />
                  <div className="h-3 w-2/3 rounded bg-zinc-800 mt-1" />
                  <div className="h-7 w-full rounded-lg bg-zinc-800 mt-1" />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && hackathons.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-16 h-16 rounded-2xl bg-zinc-800/60 border border-zinc-700/40 flex items-center justify-center mb-4">
              <svg className="w-7 h-7 text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" />
              </svg>
            </div>
            <p className="text-zinc-400 text-sm font-medium">No hackathons found</p>
            <p className="text-zinc-600 text-xs mt-1">Try adjusting your filters or refreshing the data.</p>
          </div>
        )}

        {/* Card grid */}
        {!loading && sorted.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {sorted.map((h) => (
              <HackathonCard key={h.id} hackathon={h} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

function FilterChip({
  children, color, onRemove,
}: {
  children: React.ReactNode;
  color: string;
  onRemove: () => void;
}) {
  return (
    <span
      className="inline-flex items-center gap-1.5 text-xs font-medium pl-2.5 pr-1.5 py-1 rounded-full"
      style={{ color, backgroundColor: `${color}14`, border: `1px solid ${color}30` }}
    >
      {children}
      <button
        onClick={onRemove}
        aria-label="Remove filter"
        className="flex items-center justify-center w-4 h-4 rounded-full hover:bg-black/20 transition-colors"
      >
        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
        </svg>
      </button>
    </span>
  );
}
