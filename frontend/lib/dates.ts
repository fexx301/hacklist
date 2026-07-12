import type { Hackathon } from "./types";

const DAY_MS = 1000 * 60 * 60 * 24;

function parseDate(s: string | null): Date | null {
  if (!s) return null;
  const d = new Date(s);
  return isNaN(d.getTime()) ? null : d;
}

/** Whole days from now until `d` (negative = in the past). */
function daysUntil(d: Date): number {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const target = new Date(d);
  target.setHours(0, 0, 0, 0);
  return Math.round((target.getTime() - today.getTime()) / DAY_MS);
}

export type UrgencyTone = "hot" | "soon" | "live";

export interface Urgency {
  text: string;
  tone: UrgencyTone;
}

/**
 * A short, actionable deadline label for a card — e.g. "Ends tomorrow",
 * "Starts in 5 days", "Live now". Returns null when nothing useful applies.
 */
export function getUrgency(h: Hackathon): Urgency | null {
  const start = parseDate(h.start_date);
  const end = parseDate(h.end_date);

  if (h.status === "ongoing") {
    if (end) {
      const d = daysUntil(end);
      if (d < 0) return null;
      if (d === 0) return { text: "Ends today", tone: "hot" };
      if (d === 1) return { text: "Ends tomorrow", tone: "hot" };
      if (d <= 7) return { text: `Ends in ${d} days`, tone: "soon" };
    }
    return { text: "Live now", tone: "live" };
  }

  if (h.status === "upcoming" && start) {
    const d = daysUntil(start);
    if (d < 0) return null;
    if (d === 0) return { text: "Starts today", tone: "hot" };
    if (d === 1) return { text: "Starts tomorrow", tone: "hot" };
    if (d <= 3) return { text: `Starts in ${d} days`, tone: "hot" };
    if (d <= 14) return { text: `Starts in ${d} days`, tone: "soon" };
  }

  return null;
}

export const URGENCY_STYLE: Record<UrgencyTone, { color: string; bg: string }> = {
  hot:  { color: "#fb7185", bg: "rgba(251,113,133,0.14)" },
  soon: { color: "#fbbf24", bg: "rgba(251,191,36,0.14)" },
  live: { color: "#38bdf8", bg: "rgba(56,189,248,0.14)" },
};
