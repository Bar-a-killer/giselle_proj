// Empty string = same-origin relative fetches (e.g. "/api/venues"), which next.config.ts's
// rewrites() proxies to the backend server-side. The backend is never called directly from
// the browser, so it doesn't need to be reachable from the LAN/internet at all.
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export type Coords = { lat: number; lon: number };

export type Venue = {
  id: string;
  title: string;
  category: string | null;
  address: string | null;
  latitude: number | null;
  longitude: number | null;
  google_rating: number | null;
  google_review_count: number | null;
  distance_km: number | null;
};

export type Review = {
  author_name: string | null;
  rating: number | null;
  text: string | null;
  published_at: string | null;
};

export type Confidence = "low" | "medium" | "high";

export type VenueDetail = Venue & {
  reviews: Review[];
  embedding_confidence: Confidence;
  review_count_used: number;
};

export type ScoredVenue = Venue & {
  score: number | null;
  confidence: Confidence;
};

export type Ranking = {
  personalized: boolean;
  reason: string | null;
  venues: ScoredVenue[];
};

export type User = {
  id: number;
  name: string;
};

export type ScrapeJob = {
  job_id: string;
  status: "pending" | "running" | "done" | "error";
  counts: Record<string, number> | null;
  error: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    let detail = body;
    try {
      detail = JSON.parse(body).detail ?? body;
    } catch {
      // not JSON - use the raw body as-is
    }
    throw new Error(String(detail));
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

function coordsQuery(coords?: Coords | null): string {
  return coords ? `lat=${coords.lat}&lon=${coords.lon}` : "";
}

function withQuery(base: string, ...parts: string[]): string {
  const query = parts.filter(Boolean).join("&");
  return query ? `${base}?${query}` : base;
}

export const api = {
  listVenues: (q?: string, coords?: Coords | null) =>
    request<Venue[]>(withQuery("/api/venues", q ? `q=${encodeURIComponent(q)}` : "", coordsQuery(coords))),
  getVenue: (id: string, coords?: Coords | null) =>
    request<VenueDetail>(withQuery(`/api/venues/${encodeURIComponent(id)}`, coordsQuery(coords))),

  listUsers: () => request<User[]>("/api/users"),
  createUser: (name: string) => request<User>("/api/users", { method: "POST", body: JSON.stringify({ name }) }),

  listLikes: (userId: number) => request<Venue[]>(`/api/users/${userId}/likes`),
  likeVenue: (userId: number, venueId: string) =>
    request<void>(`/api/users/${userId}/likes/${encodeURIComponent(venueId)}`, { method: "POST" }),
  unlikeVenue: (userId: number, venueId: string) =>
    request<void>(`/api/users/${userId}/likes/${encodeURIComponent(venueId)}`, { method: "DELETE" }),

  getRanking: (userId: number, coords?: Coords | null) =>
    request<Ranking>(withQuery(`/api/users/${userId}/ranking`, coordsQuery(coords))),

  startScrape: (queries: string[], opts?: { depth?: number; concurrency?: number }) =>
    request<ScrapeJob>("/api/scrape", {
      method: "POST",
      body: JSON.stringify({
        queries,
        depth: opts?.depth ?? 5,
        concurrency: opts?.concurrency ?? 1,
        extra_reviews: true,
      }),
    }),
  getScrapeStatus: (jobId: string) => request<ScrapeJob>(`/api/scrape/${jobId}`),
};
