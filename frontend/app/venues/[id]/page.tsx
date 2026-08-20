"use client";

import { use, useCallback, useEffect, useState } from "react";
import { api, VenueDetail } from "@/lib/api";
import { useCurrentUser } from "@/lib/currentUser";
import { useLocation } from "@/lib/location";
import { ScoreBadge } from "@/components/ScoreBadge";
import { ConfidenceIndicator } from "@/components/ConfidenceIndicator";
import { formatDistance } from "@/components/VenueCard";

export default function VenueDetailPage({ params }: PageProps<"/venues/[id]">) {
  const { id } = use(params);
  const venueId = decodeURIComponent(id);
  const { currentUserId } = useCurrentUser();
  const { coords } = useLocation();

  const [venue, setVenue] = useState<VenueDetail | null>(null);
  const [liked, setLiked] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const detail = await api.getVenue(venueId, coords);
    setVenue(detail);

    if (currentUserId) {
      const [likes, ranking] = await Promise.all([
        api.listLikes(currentUserId),
        api.getRanking(currentUserId, coords),
      ]);
      setLiked(likes.some((v) => v.id === venueId));
      const scored = ranking.venues.find((v) => v.id === venueId);
      setScore(ranking.personalized ? (scored?.score ?? null) : null);
    }
    setLoading(false);
  }, [venueId, currentUserId, coords]);

  useEffect(() => {
    load();
  }, [load]);

  const toggleLike = async () => {
    if (!currentUserId) return;
    if (liked) {
      await api.unlikeVenue(currentUserId, venueId);
    } else {
      await api.likeVenue(currentUserId, venueId);
    }
    load();
  };

  if (loading || !venue) {
    return <div className="mx-auto w-full max-w-2xl px-6 py-8 text-sm text-zinc-400">Loading...</div>;
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6 px-6 py-8">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">{venue.title}</h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            {venue.category ?? "Uncategorized"}
            {venue.address ? ` · ${venue.address}` : ""}
          </p>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            {venue.google_rating != null && (
              <>
                ★ {venue.google_rating.toFixed(1)} ({venue.google_review_count ?? 0} on Google)
              </>
            )}
            {venue.distance_km != null && <> · {formatDistance(venue.distance_km)}</>}
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <ScoreBadge score={score} />
          <ConfidenceIndicator confidence={venue.embedding_confidence} />
          <button
            onClick={toggleLike}
            className={`rounded-full border px-3 py-1 text-xs font-medium transition-colors ${
              liked
                ? "border-rose-500 bg-rose-500 text-white"
                : "border-zinc-300 text-zinc-600 hover:border-rose-400 hover:text-rose-500 dark:border-zinc-700 dark:text-zinc-300"
            }`}
          >
            {liked ? "♥ Liked" : "♡ Like"}
          </button>
        </div>
      </div>

      <div>
        <h2 className="mb-2 text-sm font-semibold text-zinc-700 dark:text-zinc-300">
          Reviews ({venue.review_count_used} used for scoring)
        </h2>
        <div className="flex flex-col gap-3">
          {venue.reviews.map((review, i) => (
            <div key={i} className="rounded-lg border border-zinc-200 p-3 text-sm dark:border-zinc-800">
              <div className="mb-1 flex items-center justify-between text-zinc-500 dark:text-zinc-400">
                <span>{review.author_name ?? "Anonymous"}</span>
                {review.rating != null && <span>★ {review.rating}</span>}
              </div>
              <p>{review.text}</p>
            </div>
          ))}
          {venue.reviews.length === 0 && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">No reviews scraped yet.</p>
          )}
        </div>
      </div>
    </div>
  );
}
