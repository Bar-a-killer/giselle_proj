# Giselle — Personalized Google Maps Review Recommender (prototype)

Gives you a personalized "would you like this place" score for restaurants/venues, based on
their scraped Google Maps reviews and a handful of places you tell it you already like.

This is an early prototype for a couple of people, not a deployable product: no auth, no
hosting, no ToS-hardening. It's meant to be run on one machine by one or two people.

## How it works

1. **Scrape**: [`gosom/google-maps-scraper`](https://github.com/gosom/google-maps-scraper)
   pulls venues + reviews for a search query (e.g. "coffee in Capitol Hill Seattle"), using
   `-extra-reviews` to get well past the ~5 reviews Google's own Places API exposes.
2. **Ingest**: scraped JSON gets parsed into a local SQLite database (venues, reviews).
3. **Embed**: each venue's reviews are turned into a single vector with a local
   `sentence-transformers` model (mean-pooled, L2-normalized). No paid LLM calls.
4. **Personalize**: you pick a handful of venues you already like; your preference vector is
   the centroid of their embeddings. Every venue is scored by cosine similarity to your vector.
5. When there isn't much data yet (few liked venues, few reviews for a venue), the UI says so
   instead of pretending the score is meaningful.

The embedding/scoring pieces sit behind small interfaces (`VenueEmbedder`, `UserEmbedder`) so
a real trained two-tower recommender can be swapped in later once there's enough usage data —
see `backend/app/services/embeddings.py` and `user_vector.py`.

## Running it locally

Two processes, no Docker required.

### Backend

```bash
cd backend
uv sync
uv run python scripts/init_db.py        # create the SQLite schema (once)
uv run uvicorn app.main:app --reload --port 8001
```

Bind this to `127.0.0.1` only (the default) unless you have a specific reason not to — the
frontend proxies all API calls through itself (see below), so the backend never needs to be
reachable from the LAN or internet directly.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The browser only ever talks to the frontend's own origin. `next.config.ts`'s `rewrites()` proxies
`/api/*` server-side to `http://localhost:8001/api/*`, so there's one URL to reach and (if you set
one up) one place to put auth in front of. `next dev` listens on all interfaces by default and
prints a `Network:` URL for LAN access — no env var pointing at a LAN IP needed anymore.

### Password-protecting it

`frontend/proxy.ts` does simple HTTP Basic Auth in front of every route (pages and the `/api/*`
proxy alike), gated by `BASIC_AUTH_USER`/`BASIC_AUTH_PASS` in `frontend/.env.local` (gitignored -
not committed). If those aren't set, auth is skipped entirely (so local dev isn't locked out by
accident) - set both before exposing this beyond your own machine. Restart the server after
changing them.

### Exposing it publicly (Cloudflare Tunnel)

Set up once, against a domain you manage in Cloudflare (replace `<your-domain>` below):

```bash
cloudflared tunnel login                                   # authorizes a zone in your Cloudflare account
cloudflared tunnel create giselle                           # writes credentials to ~/.cloudflared/<id>.json
cloudflared tunnel route dns giselle giselle.<your-domain>
# ~/.cloudflared/config.yml points hostname giselle.<your-domain> -> http://localhost:3000
cloudflared tunnel --config ~/.cloudflared/config.yml run giselle
```

Unlike a quick tunnel (`cloudflared tunnel --url ...`, which gets a random throwaway
`trycloudflare.com` URL each run), this is a stable hostname that keeps working across restarts —
just re-run the last command. It isn't a systemd service yet, so it won't survive a reboot on its
own; ask if you want that wired up.

Make sure `BASIC_AUTH_USER`/`BASIC_AUTH_PASS` are set before running this — the tunnel makes the
app reachable by anyone with the URL.

### Getting data in

One-time setup: download a `gosom/google-maps-scraper` release binary for your platform from
https://github.com/gosom/google-maps-scraper/releases and place it at `backend/bin/gmaps-scraper`
(`chmod +x`).

Then, from `backend/`:

```bash
uv run python scripts/run_scrape.py --query "coffee in Capitol Hill Seattle" --depth 5
uv run python scripts/build_embeddings.py
```

Keep `--concurrency` low (default 1) and don't crank `--depth` way up — going slow avoids
getting blocked, and there's no ToS/legal review behind this prototype so it's worth being
conservative on your own.

## Tests

```bash
cd backend
uv run pytest
```

Tests use fixtures and synthetic vectors — no network access or model download required.
