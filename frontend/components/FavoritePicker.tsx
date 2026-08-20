"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Venue } from "@/lib/api";
import { VenueCard } from "./VenueCard";
import { SearchBar } from "./SearchBar";

export function FavoritePicker({
  venues,
  likedIds,
  onToggle,
}: {
  venues: Venue[];
  likedIds: Set<string>;
  onToggle: (venueId: string) => void;
}) {
  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    if (!query.trim()) return venues;
    const q = query.toLowerCase();
    return venues.filter(
      (v) => v.title.toLowerCase().includes(q) || (v.category ?? "").toLowerCase().includes(q)
    );
  }, [venues, query]);

  return (
    <div className="flex flex-col gap-4">
      <SearchBar value={query} onChange={setQuery} placeholder="Search for places you already love..." />
      <div className="flex flex-col gap-3">
        {filtered.map((venue) => (
          <VenueCard
            key={venue.id}
            venue={venue}
            liked={likedIds.has(venue.id)}
            onToggleLike={() => onToggle(venue.id)}
          />
        ))}
        {filtered.length === 0 && query.trim() && (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No venues match &ldquo;{query}&rdquo;.{" "}
            <Link href="/add-data" className="underline">
              Add data for it
            </Link>
            .
          </p>
        )}
      </div>
    </div>
  );
}
