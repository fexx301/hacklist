import type { Source } from "./types";

export const SOURCE_META: Record<
  Source,
  { label: string; color: string; bg: string }
> = {
  devpost:     { label: "Devpost",      color: "#3b82f6", bg: "rgba(59,130,246,0.15)" },
  mlh:         { label: "MLH",          color: "#ef4444", bg: "rgba(239,68,68,0.15)"  },
  devfolio:    { label: "Devfolio",     color: "#a855f7", bg: "rgba(168,85,247,0.15)" },
  unstop:      { label: "Unstop",       color: "#f97316", bg: "rgba(249,115,22,0.15)" },
  hackerearth: { label: "HackerEarth",  color: "#22c55e", bg: "rgba(34,197,94,0.15)"  },
  twitter:     { label: "Twitter / X",  color: "#94a3b8", bg: "rgba(148,163,184,0.15)"},
};

export const STATUS_META = {
  upcoming: { label: "Upcoming", color: "#10b981", bg: "rgba(16,185,129,0.12)" },
  ongoing:  { label: "Ongoing",  color: "#38bdf8", bg: "rgba(56,189,248,0.12)" },
  past:     { label: "Past",     color: "#71717a", bg: "rgba(113,113,122,0.12)" },
};

export const ALL_SOURCES: Source[] = [
  "devpost",
  "mlh",
  "devfolio",
  "unstop",
  "hackerearth",
  "twitter",
];
