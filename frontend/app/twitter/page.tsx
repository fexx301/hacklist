"use client";

import { useState, useEffect, useCallback, useRef, useMemo, Suspense } from "react";
import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { FilterSidebar } from "@/components/filter-sidebar";
import { fetchHackathons, fetchStats, triggerRefresh, fetchScrapeStatus } from "@/lib/api";
import type { Hackathon, Filters, DashboardData } from "@/lib/types";
import { STATUS_META } from "@/lib/constants";
import { useDebounce } from "@/lib/use-debounce";
import { SORT_OPTIONS, sortHackathons, type SortKey } from "@/lib/sort";
import { encodeFilters, decodeFilters } from "@/lib/url-filters";

const DEFAULT_FILTERS: Filters = {
  sources: ["twitter"],
  statuses: ["upcoming", "ongoing"],
  search: "",
  has_prize: false,
};

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function domain(url: string): string {
  try { return new URL(url).hostname.replace("www.", ""); } catch { return url; }
}

function TwitterCard({ h }: { h: Hackathon }) {
  const sts = STATUS_META[h.status] ?? STATUS_META.past;

  return (
    <a
      href={h.url}
      target="_blank"
      rel="noopener noreferrer"
      className="group flex flex-col gap-3 p-4 rounded-xl border transition-all duration-150 hover:bg-zinc-800/40 active:scale-[0.995]"
      style={{ borderColor: "rgba(63,63,70,0.55)", backgroundColor: "rgba(24,24,27,0.6)" }}
    >
      {/* Top row: status + date */}
      <div className="flex items-center justify-between gap-2">
        <span
          className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"
          style={{ color: sts.color, backgroundColor: sts.bg, border: `1px solid ${sts.color}30` }}
        >
          {sts.label}
        </span>
        {(h.start_date || h.end_date) && (
          <span className="text-[11px] text-zinc-500 flex items-center gap-1">
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
            </svg>
            {formatDate(h.start_date)}{h.end_date ? ` → ${formatDate(h.end_date)}` : ""}
          </span>
        )}
      </div>

      {/* Title */}
      <h3 className="text-sm font-semibold text-zinc-100 leading-snug group-hover:text-white transition-colors line-clamp-2">
        {h.title}
      </h3>

      {/* Description / tweet body */}
      {h.description && (
        <p className="text-xs text-zinc-500 leading-relaxed line-clamp-3">
          {h.description.replace(/<[^>]*>/g, "").trim()}
        </p>
      )}

      {/* URL chip */}
      <div className="flex items-center gap-1.5 mt-auto">
        <svg className="w-3 h-3 text-zinc-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.75}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13.19 8.688a4.5 4.5 0 0 1 1.242 7.244l-4.5 4.5a4.5 4.5 0 0 1-6.364-6.364l1.757-1.757m13.35-.622 1.757-1.757a4.5 4.5 0 0 0-6.364-6.364l-4.5 4.5a4.5 4.5 0 0 0 1.242 7.244" />
        </svg>
        <span className="text-[11px] text-zinc-600 truncate">{domain(h.url)}</span>
        <svg className="w-2.5 h-2.5 text-zinc-700 flex-shrink-0 ml-auto group-hover:text-zinc-500 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
        </svg>
      </div>
    </a>
  );
}

export default function TwitterPage() {
  // useSearchParams requires a Suspense boundary above it for static builds.
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#09090b]" />}>
      <TwitterFeed />
    </Suspense>
  );
}

function TwitterFeed() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  // Seed initial state from the URL (sources are fixed to twitter on this page).
  const [initial] = useState(() =>
    decodeFilters(new URLSearchParams(searchParams.toString()), DEFAULT_FILTERS, {
      includeSources: false,
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
    try { setDashData(await fetchStats()); } catch { /* non-critical */ }
  }, []);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await Promise.all([loadHackathons(initial.filters), loadStats()]);
      setLoading(false);
    })();
  }, [initial, loadHackathons, loadStats]);

  const isFirstMount = useRef(true);
  useEffect(() => {
    if (isFirstMount.current) { isFirstMount.current = false; return; }
    loadHackathons({ ...debouncedFilters, sources: ["twitter"] });
  }, [debouncedFilters, loadHackathons]);

  // Keep the URL in sync with the active view so it's shareable/refresh-safe.
  useEffect(() => {
    const qs = encodeFilters(debouncedFilters, sort, DEFAULT_FILTERS, { includeSources: false });
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }, [debouncedFilters, sort, router, pathname]);

  useEffect(() => {
    if (!scraping) return;
    pollRef.current = setInterval(async () => {
      try {
        const { scraping: s } = await fetchScrapeStatus();
        if (!s) {
          setScraping(false);
          await Promise.all([loadHackathons({ ...filters, sources: ["twitter"] }), loadStats()]);
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
    } catch { setError("Failed to trigger refresh."); }
  }

  const sorted = useMemo(() => sortHackathons(hackathons, sort), [hackathons, sort]);
  const twitterTotal = dashData?.stats.by_source["twitter"] ?? hackathons.length;

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
        onChange={(f) => setFilters({ ...f, sources: ["twitter"] })}
        data={dashData}
        scraping={scraping}
        onRefresh={handleRefresh}
        total={twitterTotal}
        filtered={hackathons.length}
        visibleSources={["twitter"]}
        mobileOpen={menuOpen}
        onClose={() => setMenuOpen(false)}
      />

      <main className="flex-1 min-w-0 py-6 px-4 sm:py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-8">
          <div className="flex items-start gap-3 min-w-0">
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
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <svg className="w-5 h-5 text-zinc-400" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
              <h2 className="text-lg font-semibold text-zinc-100">Twitter Sources</h2>
            </div>
            <p className="text-xs text-zinc-500">
              Hackathons discovered from X / Twitter — {hackathons.length} result{hackathons.length !== 1 ? "s" : ""}
              {filters.statuses.length < 3 ? ` · ${filters.statuses.join(", ")}` : ""}
              {filters.search ? ` · "${filters.search}"` : ""}
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
                Scraping…
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

        {/* Twitter note */}
        <div
          className="mb-6 flex items-start gap-3 px-4 py-3 rounded-xl text-xs text-zinc-500 leading-relaxed"
          style={{ backgroundColor: "rgba(148,163,184,0.06)", border: "1px solid rgba(148,163,184,0.12)" }}
        >
          <svg className="w-3.5 h-3.5 mt-0.5 flex-shrink-0 text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
          </svg>
          These results come from X/Twitter searches for hackathon announcements.
          Dates and prize info may be missing or approximate — always verify on the linked page.
        </div>

        {error && (
          <div className="mb-6 px-4 py-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* Loading skeletons */}
        {loading && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-xl bg-zinc-900/60 border border-zinc-800/50 p-4 flex flex-col gap-3 animate-pulse">
                <div className="flex justify-between">
                  <div className="h-4 w-16 rounded-full bg-zinc-800" />
                  <div className="h-3 w-24 rounded bg-zinc-800" />
                </div>
                <div className="h-4 w-full rounded bg-zinc-800" />
                <div className="h-3 w-4/5 rounded bg-zinc-800" />
                <div className="h-3 w-3/5 rounded bg-zinc-800" />
                <div className="h-3 w-2/5 rounded bg-zinc-800 mt-1" />
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && hackathons.length === 0 && !error && (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
              style={{ backgroundColor: "rgba(148,163,184,0.08)", border: "1px solid rgba(148,163,184,0.15)" }}
            >
              <svg className="w-7 h-7 text-zinc-600" fill="currentColor" viewBox="0 0 24 24">
                <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
              </svg>
            </div>
            <p className="text-zinc-400 text-sm font-medium">No Twitter results</p>
            <p className="text-zinc-600 text-xs mt-1 max-w-xs">
              Try adjusting filters or hit &ldquo;Refresh now&rdquo; to re-scrape Twitter.
            </p>
          </div>
        )}

        {/* Feed grid */}
        {!loading && sorted.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {sorted.map((h) => (
              <TwitterCard key={h.id} h={h} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
