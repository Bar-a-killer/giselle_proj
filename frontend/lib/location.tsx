"use client";

import { createContext, useCallback, useContext, useEffect, useState, ReactNode } from "react";

export type Coords = { lat: number; lon: number };
export type LocationStatus = "idle" | "requesting" | "granted" | "denied" | "unavailable";

type LocationContextValue = {
  coords: Coords | null;
  status: LocationStatus;
  requestLocation: () => void;
};

const LocationContext = createContext<LocationContextValue | null>(null);

/**
 * Asks for the browser's geolocation once when the app loads. If the user denies it (or the
 * browser doesn't support it), we just don't show distance anywhere - never nag or retry
 * automatically, only via the explicit retry the UI offers.
 */
export function LocationProvider({ children }: { children: ReactNode }) {
  const [coords, setCoords] = useState<Coords | null>(null);
  const [status, setStatus] = useState<LocationStatus>("idle");

  const requestLocation = useCallback(() => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      setStatus("unavailable");
      return;
    }
    setStatus("requesting");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCoords({ lat: position.coords.latitude, lon: position.coords.longitude });
        setStatus("granted");
      },
      () => {
        setCoords(null);
        setStatus("denied");
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 5 * 60_000 }
    );
  }, []);

  useEffect(() => {
    requestLocation();
  }, [requestLocation]);

  return (
    <LocationContext.Provider value={{ coords, status, requestLocation }}>{children}</LocationContext.Provider>
  );
}

export function useLocation(): LocationContextValue {
  const ctx = useContext(LocationContext);
  if (!ctx) throw new Error("useLocation must be used within a LocationProvider");
  return ctx;
}
