import type { Hackathon, DashboardData, Filters } from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchHackathons(filters: Filters): Promise<Hackathon[]> {
  const params = new URLSearchParams();

  filters.sources.forEach((s) => params.append("sources", s));
  filters.statuses.forEach((s) => params.append("statuses", s));
  if (filters.search) params.set("search", filters.search);
  if (filters.has_prize) params.set("has_prize", "true");

  const res = await fetch(`${BASE}/api/hackathons?${params}`);
  if (!res.ok) throw new Error("Failed to fetch hackathons");
  return res.json();
}

export async function fetchStats(): Promise<DashboardData> {
  const res = await fetch(`${BASE}/api/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function triggerRefresh(): Promise<{ status: string }> {
  const res = await fetch(`${BASE}/api/refresh`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger refresh");
  return res.json();
}

export async function fetchScrapeStatus(): Promise<{ scraping: boolean }> {
  const res = await fetch(`${BASE}/api/status`);
  if (!res.ok) throw new Error("Failed to fetch status");
  return res.json();
}
