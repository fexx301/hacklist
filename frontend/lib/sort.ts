import type { Hackathon } from "./types";

export type SortKey = "soonest" | "newest" | "prize";

export const SORT_OPTIONS: { key: SortKey; label: string }[] = [
  { key: "soonest", label: "Soonest deadline" },
  { key: "newest", label: "Recently added" },
  { key: "prize", label: "Biggest prize" },
];

/** The date a card is judged by: ongoing → end date, otherwise start date. */
function keyDate(h: Hackathon): number {
  const raw = h.status === "ongoing" ? h.end_date ?? h.start_date : h.start_date;
  if (!raw) return Infinity; // undated entries sink to the bottom
  const t = new Date(raw).getTime();
  return isNaN(t) ? Infinity : t;
}

/** Best-effort numeric value of a prize string ("$10,000", "₹50K", "1.5M"). */
export function parsePrize(prize: string | null): number {
  if (!prize) return 0;
  const m = prize.replace(/,/g, "").match(/(\d+(?:\.\d+)?)\s*([kmKM])?/);
  if (!m) return 0;
  let n = parseFloat(m[1]);
  const suffix = m[2]?.toLowerCase();
  if (suffix === "k") n *= 1_000;
  else if (suffix === "m") n *= 1_000_000;
  return n;
}

export function sortHackathons(list: Hackathon[], key: SortKey): Hackathon[] {
  const sorted = [...list];
  switch (key) {
    case "soonest":
      sorted.sort((a, b) => keyDate(a) - keyDate(b));
      break;
    case "newest":
      sorted.sort(
        (a, b) => new Date(b.scraped_at).getTime() - new Date(a.scraped_at).getTime(),
      );
      break;
    case "prize":
      sorted.sort((a, b) => parsePrize(b.prize) - parsePrize(a.prize));
      break;
  }
  return sorted;
}
