import Link from "next/link";
import { Confidence, Venue } from "@/lib/api";
import { ScoreBadge } from "./ScoreBadge";
import { ConfidenceIndicator } from "./ConfidenceIndicator";

export function formatDistance(km: number): string {
  return km < 1 ? `${Math.round(km * 1000)} m away` : `${km.toFixed(1)} km away`;
}

export function VenueCard({
  venue,
  score,
  confidence,
  liked,
  onToggleLike,
}: {
  venue: Venue;
  score?: number | null;
  confidence?: Confidence;
  liked?: boolean;
  onToggleLike?: () => void;
}) {
  return (
    <div className="flex items-start justify-between gap-4 rounded-lg border border-zinc-200 p-4 dark:border-zinc-800">
      <div className="min-w-0 flex-1">
        <Link href={`/venues/${encodeURIComponent(venue.id)}`} className="font-medium hover:underline">
          {venue.title}
        </Link>
        <div className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          {venue.category ?? "Uncategorized"}
          {venue.address ? ` · ${venue.address}` : ""}
        </div>
        <div className="mt-1 flex items-center gap-2 text-sm text-zinc-500 dark:text-zinc-400">
          {venue.google_rating != null && (
            <span>
              ★ {venue.google_rating.toFixed(1)} ({venue.google_review_count ?? 0})
            </span>
          )}
          {venue.distance_km != null && <span>{formatDistance(venue.distance_km)}</span>}
          {confidence && <ConfidenceIndicator confidence={confidence} />}
        </div>
      </div>
      <div className="flex flex-col items-end gap-2">
        {score !== undefined && <ScoreBadge score={score} />}
        {onToggleLike && (
          <button
            onClick={onToggleLike}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              liked
                ? "border-rose-500 bg-rose-500 text-white"
                : "border-zinc-300 text-zinc-600 hover:border-rose-400 hover:text-rose-500 dark:border-zinc-700 dark:text-zinc-300"
            }`}
          >
            {liked ? "♥ Liked" : "♡ Like"}
          </button>
        )}
      </div>
    </div>
  );
}
