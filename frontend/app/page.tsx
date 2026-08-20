"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { api, Ranking } from "@/lib/api";
import { useCurrentUser } from "@/lib/currentUser";
import { useLocation } from "@/lib/location";
import { VenueCard } from "@/components/VenueCard";

// Leaflet touches `window` at import time, so it can only ever run in the browser.
const VenueMap = dynamic(() => import("@/components/VenueMap").then((m) => m.VenueMap), {
  ssr: false,
});

const NEARBY_RADIUS_KM = 1;

export default function RecommendedPage() {
  const { currentUserId } = useCurrentUser();
  const { coords } = useLocation();
  const [ranking, setRanking] = useState<Ranking | null>(null);
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!currentUserId) return;
    setLoading(true);
    const [rankingResult, likes] = await Promise.all([
      api.getRanking(currentUserId, coords),
      api.listLikes(currentUserId),
    ]);
    setRanking(rankingResult);
    setLikedIds(new Set(likes.map((v) => v.id)));
    setLoading(false);
  }, [currentUserId, coords]);

  useEffect(() => {
    load();
  }, [load]);

  const nearbyVenues = (ranking?.venues ?? []).filter(
    (v) => v.distance_km != null && v.distance_km <= NEARBY_RADIUS_KM
  );

  const toggleLike = async (venueId: string) => {
    if (!currentUserId) return;
    if (likedIds.has(venueId)) {
      await api.unlikeVenue(currentUserId, venueId);
    } else {
      await api.likeVenue(currentUserId, venueId);
    }
    load();
  };

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4 px-6 py-8">
      <h1 className="text-xl font-semibold">Recommended for you</h1>

      {loading && <p className="text-sm text-zinc-400">Loading...</p>}

      {!loading && ranking && !ranking.personalized && (
        <div className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          {ranking.reason ?? "Not enough data yet for a personalized ranking."}{" "}
          <Link href="/favorites" className="font-medium underline">
            Pick some favorites
          </Link>
          . Showing venues by Google rating in the meantime.
        </div>
      )}

      {!loading && ranking && ranking.venues.length === 0 && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          No venues yet. Go to{" "}
          <Link href="/favorites" className="underline">
            Pick favorites
          </Link>{" "}
          to search for and add some.
        </p>
      )}

      {!loading && (
        <div className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold text-zinc-700 dark:text-zinc-300">
            Nearby (within {NEARBY_RADIUS_KM} km)
          </h2>
          {!coords && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Share your location (see the 📍 status in the nav bar) to see nearby recommendations on a map.
            </p>
          )}
          {coords && nearbyVenues.length === 0 && (
            <p className="text-sm text-zinc-500 dark:text-zinc-400">
              Nothing scraped within {NEARBY_RADIUS_KM} km of you yet.
            </p>
          )}
          {coords && nearbyVenues.length > 0 && <VenueMap userCoords={coords} venues={nearbyVenues} />}
        </div>
      )}

      <div className="flex flex-col gap-3">
        {ranking?.venues.map((venue) => (
          <VenueCard
            key={venue.id}
            venue={venue}
            score={venue.score}
            confidence={venue.confidence}
            liked={likedIds.has(venue.id)}
            onToggleLike={() => toggleLike(venue.id)}
          />
        ))}
      </div>
    </div>
  );
}
