import type { Filters, Source, Status } from "./types";
import { ALL_SOURCES } from "./constants";
import { SORT_OPTIONS, type SortKey } from "./sort";

const ALL_STATUSES: Status[] = ["upcoming", "ongoing", "past"];

export interface FilterState {
  filters: Filters;
  sort: SortKey;
}

interface Options {
  /** Whether the `sources` param is meaningful (false on the Twitter page). */
  includeSources: boolean;
}

function sameSet<T>(a: T[], b: T[]): boolean {
  return a.length === b.length && a.every((x) => b.includes(x));
}

function isSource(s: string): s is Source {
  return (ALL_SOURCES as string[]).includes(s);
}
function isStatus(s: string): s is Status {
  return (ALL_STATUSES as string[]).includes(s);
}
function isSort(s: string | null): s is SortKey {
  return s !== null && SORT_OPTIONS.some((o) => o.key === s);
}

/** Serialize state to a query string, omitting anything left at its default. */
export function encodeFilters(
  filters: Filters,
  sort: SortKey,
  defaults: Filters,
  { includeSources }: Options,
): string {
  const p = new URLSearchParams();
  if (filters.search) p.set("q", filters.search);
  if (includeSources && !sameSet(filters.sources, defaults.sources)) {
    p.set("sources", filters.sources.join(","));
  }
  if (!sameSet(filters.statuses, defaults.statuses)) {
    // empty string distinguishes "explicitly none" from "default"
    p.set("status", filters.statuses.join(","));
  }
  if (filters.has_prize) p.set("prize", "1");
  if (sort !== "soonest") p.set("sort", sort);
  return p.toString();
}

/** Parse state back from a query string, falling back to `defaults`. */
export function decodeFilters(
  sp: URLSearchParams,
  defaults: Filters,
  { includeSources }: Options,
): FilterState {
  const filters: Filters = {
    ...defaults,
    sources: [...defaults.sources],
    statuses: [...defaults.statuses],
  };

  const q = sp.get("q");
  if (q !== null) filters.search = q;

  if (includeSources) {
    const raw = sp.get("sources");
    if (raw !== null) filters.sources = raw.split(",").filter(isSource);
  }

  const status = sp.get("status");
  if (status !== null) filters.statuses = status.split(",").filter(isStatus);

  filters.has_prize = sp.get("prize") === "1";

  const sort = sp.get("sort");
  return { filters, sort: isSort(sort) ? sort : "soonest" };
}
