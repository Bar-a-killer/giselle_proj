"use client";

import { useEffect } from "react";
import { Circle, MapContainer, Marker, Popup, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { Coords, ScoredVenue } from "@/lib/api";

// Leaflet's default marker icons reference image paths that don't survive bundling - point them
// at the CDN copies instead (same version as the installed leaflet package).
const venueIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const userIcon = new L.DivIcon({
  className: "",
  html: '<div style="width:16px;height:16px;border-radius:50%;background:#2563eb;border:3px solid white;box-shadow:0 0 4px rgba(0,0,0,0.5);"></div>',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

function Recenter({ coords }: { coords: Coords }) {
  const map = useMap();
  useEffect(() => {
    map.setView([coords.lat, coords.lon]);
  }, [coords, map]);
  return null;
}

export function VenueMap({ userCoords, venues }: { userCoords: Coords; venues: ScoredVenue[] }) {
  return (
    <MapContainer
      center={[userCoords.lat, userCoords.lon]}
      zoom={15}
      scrollWheelZoom={false}
      className="h-80 w-full rounded-lg"
    >
      <Recenter coords={userCoords} />
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <Circle
        center={[userCoords.lat, userCoords.lon]}
        radius={1000}
        pathOptions={{ color: "#2563eb", fillOpacity: 0.05 }}
      />
      <Marker position={[userCoords.lat, userCoords.lon]} icon={userIcon}>
        <Popup>You are here</Popup>
      </Marker>
      {venues.map(
        (venue) =>
          venue.latitude != null &&
          venue.longitude != null && (
            <Marker key={venue.id} position={[venue.latitude, venue.longitude]} icon={venueIcon}>
              <Popup>
                <div className="font-medium">{venue.title}</div>
                <div>{venue.category}</div>
                {venue.score != null && <div>Score: {venue.score}</div>}
                {venue.distance_km != null && (
                  <div>{Math.round(venue.distance_km * 1000)} m away</div>
                )}
              </Popup>
            </Marker>
          )
      )}
    </MapContainer>
  );
}
