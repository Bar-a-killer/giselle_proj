"use client";

import { useLocation } from "@/lib/location";

export function LocationStatus() {
  const { status, requestLocation } = useLocation();

  if (status === "granted") {
    return <span className="text-xs text-zinc-400" title="Distances are relative to your location">📍 on</span>;
  }
  if (status === "requesting" || status === "idle") {
    return <span className="text-xs text-zinc-400">📍 asking...</span>;
  }
  // denied or unavailable
  return (
    <button
      onClick={requestLocation}
      className="text-xs text-zinc-400 hover:underline"
      title="Location off - distances won't be shown. Click to try again."
    >
      📍 off (retry)
    </button>
  );
}
