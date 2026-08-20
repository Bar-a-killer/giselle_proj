"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { api, Venue } from "@/lib/api";
import { useCurrentUser } from "@/lib/currentUser";
import { FavoritePicker } from "@/components/FavoritePicker";

export default function FavoritesPage() {
  const { currentUserId } = useCurrentUser();
  const [venues, setVenues] = useState<Venue[]>([]);
  const [likedIds, setLikedIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (!currentUserId) return;
    setLoading(true);
    const [venueList, likes] = await Promise.all([api.listVenues(), api.listLikes(currentUserId)]);
    setVenues(venueList);
    setLikedIds(new Set(likes.map((v) => v.id)));
    setLoading(false);
  }, [currentUserId]);

  useEffect(() => {
    load();
  }, [load]);

  const toggle = async (venueId: string) => {
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
      <div>
        <h1 className="text-xl font-semibold">Pick your favorites</h1>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Search for a few places you already know you like. Your recommendations are built from
          these — the more you pick (and the more varied), the better they get.
        </p>
      </div>

      <div className="rounded-lg border border-zinc-200 px-4 py-2 text-sm dark:border-zinc-800">
        {likedIds.size} favorite{likedIds.size === 1 ? "" : "s"} picked
        {likedIds.size >= 3 ? (
          <>
            {" "}
            —{" "}
            <Link href="/" className="font-medium underline">
              see your recommendations
            </Link>
          </>
        ) : (
          <> — pick at least 3 for personalized scores</>
        )}
      </div>

      {loading && <p className="text-sm text-zinc-400">Loading...</p>}
      {!loading && venues.length === 0 && (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          No venues yet.{" "}
          <Link href="/add-data" className="underline">
            Add some
          </Link>
          , then come back here.
        </p>
      )}
      {!loading && venues.length > 0 && (
        <FavoritePicker venues={venues} likedIds={likedIds} onToggle={toggle} />
      )}
    </div>
  );
}
