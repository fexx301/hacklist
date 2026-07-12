export type Status = "upcoming" | "ongoing" | "past";

export type Source =
  | "devpost"
  | "mlh"
  | "devfolio"
  | "unstop"
  | "hackerearth"
  | "twitter";

export interface Hackathon {
  id: number;
  title: string;
  url: string;
  source: Source;
  start_date: string | null;
  end_date: string | null;
  prize: string | null;
  description: string | null;
  image_url: string | null;
  status: Status;
  scraped_at: string;
}

export interface Stats {
  total: number;
  by_source: Record<string, number>;
  by_status: Record<string, number>;
}

export interface SourceInfo {
  status: "success" | "error";
  last_scraped: string;
}

export interface DashboardData {
  stats: Stats;
  sources: Record<string, SourceInfo>;
}

export interface Filters {
  sources: Source[];
  statuses: Status[];
  search: string;
  has_prize: boolean;
}
