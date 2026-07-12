"use client";

import type { CSSProperties } from "react";
import type { Hackathon } from "@/lib/types";
import { calendarUrl } from "@/lib/api";
import { SOURCE_META, STATUS_META } from "@/lib/constants";
import { getUrgency, URGENCY_STYLE } from "@/lib/dates";

function formatDate(dateStr: string | null): string {
  if (!dateStr) return "TBD";
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function stripHtml(str: string): string {
  return str.replace(/<[^>]*>/g, "").trim();
}

export function HackathonCard({ hackathon }: { hackathon: Hackathon }) {
  const src = SOURCE_META[hackathon.source];
  const sts = STATUS_META[hackathon.status] ?? STATUS_META.past;
  const urgency = getUrgency(hackathon);

  const cleanPrize = hackathon.prize ? stripHtml(hackathon.prize) : null;

  const fallbackBg = `linear-gradient(135deg, ${src.color}22 0%, ${src.color}08 100%)`;

  return (
    <article
      style={{ borderColor: "rgba(63,63,70,0.6)" }}
      className="group flex flex-col rounded-xl border bg-zinc-900 overflow-hidden transition-all duration-200 hover:-translate-y-0.5 hover:shadow-xl hover:shadow-black/40"
    >
      {/* Cover image / gradient header */}
      <div
        className="relative h-36 w-full flex-shrink-0 overflow-hidden flex items-center justify-center"
        style={{ background: fallbackBg }}
      >
        {hackathon.image_url ? (
          <img
            src={hackathon.image_url}
            alt={hackathon.title}
            className="absolute inset-0 w-full h-full object-cover"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : (
          /* No image — show a branded placeholder instead of a bare gradient */
          <div className="flex flex-col items-center gap-1.5 select-none">
            <span
              className="flex items-center justify-center w-11 h-11 rounded-xl text-lg font-bold"
              style={{ color: src.color, backgroundColor: src.bg, border: `1px solid ${src.color}30` }}
            >
              {hackathon.title.trim().charAt(0).toUpperCase() || "?"}
            </span>
            <span className="text-[11px] font-medium tracking-wide" style={{ color: `${src.color}cc` }}>
              {src.label}
            </span>
          </div>
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-zinc-900/70 to-transparent pointer-events-none" />

        {/* Urgency badge top-left */}
        {urgency && (
          <span
            className="absolute top-3 left-3 text-[11px] font-semibold px-2 py-0.5 rounded-full"
            style={{
              color: URGENCY_STYLE[urgency.tone].color,
              backgroundColor: URGENCY_STYLE[urgency.tone].bg,
              border: `1px solid ${URGENCY_STYLE[urgency.tone].color}40`,
            }}
          >
            {urgency.text}
          </span>
        )}

        {/* Status badge top-right */}
        <span
          className="absolute top-3 right-3 text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full"
          style={{ color: sts.color, backgroundColor: sts.bg, border: `1px solid ${sts.color}30` }}
        >
          {sts.label}
        </span>
      </div>

      {/* Body */}
      <div className="flex flex-col flex-1 p-4 gap-3">
        {/* Source badge */}
        <div className="flex items-center gap-2">
          <span
            className="text-[11px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-md"
            style={{ color: src.color, backgroundColor: src.bg, border: `1px solid ${src.color}25` }}
          >
            {src.label}
          </span>
          {cleanPrize && cleanPrize !== "0" && cleanPrize !== "$0" && (
            <span className="text-[11px] font-medium px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
              {cleanPrize.length > 20 ? cleanPrize.slice(0, 20) + "…" : cleanPrize}
            </span>
          )}
        </div>

        {/* Title */}
        <h3 className="text-[15px] font-semibold text-zinc-100 leading-snug line-clamp-2 group-hover:text-white transition-colors">
          {hackathon.title}
        </h3>

        {/* Description */}
        {hackathon.description && (
          <p className="text-xs text-zinc-500 leading-relaxed line-clamp-2">
            {stripHtml(hackathon.description)}
          </p>
        )}

        {/* Dates */}
        <div className="flex items-center gap-1 text-xs text-zinc-500 mt-auto">
          <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25m-18 0A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75m-18 0v-7.5A2.25 2.25 0 0 1 5.25 9h13.5A2.25 2.25 0 0 1 21 11.25v7.5" />
          </svg>
          <span>
            {formatDate(hackathon.start_date)}
            {hackathon.end_date ? ` → ${formatDate(hackathon.end_date)}` : ""}
          </span>
        </div>

        {/* Register button — hover handled purely in CSS via .src-btn */}
        <div className="flex items-stretch gap-1.5 mt-1">
          <a
            href={hackathon.url}
            target="_blank"
            rel="noopener noreferrer"
            className="src-btn flex-1 text-center text-xs font-medium py-1.5 px-3 rounded-lg duration-150 active:scale-[0.98]"
            style={
              {
                "--src": src.color,
                "--src-bg": `${src.color}18`,
                "--src-bg-hover": `${src.color}30`,
                "--src-border": `${src.color}30`,
              } as CSSProperties
            }
          >
            View &amp; Register →
          </a>
          {hackathon.start_date && (
            <a
              href={calendarUrl(hackathon.id)}
              title="Add to calendar (.ics)"
              aria-label="Add to calendar"
              className="flex items-center justify-center px-2.5 rounded-lg border border-zinc-700/60 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/60 transition-colors active:scale-[0.98]"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 0 1 2.25-2.25h13.5A2.25 2.25 0 0 1 21 7.5v11.25A2.25 2.25 0 0 1 18.75 21H5.25A2.25 2.25 0 0 1 3 18.75Z" />
              </svg>
            </a>
          )}
        </div>
      </div>
    </article>
  );
}
