from fastapi import FastAPI

from app.routers import scores, scrape, users, venues

app = FastAPI(title="Giselle personalized venue recommender")

# No CORS middleware: the frontend proxies /api/* through its own Next.js server
# (see frontend/next.config.ts rewrites), so the browser never calls this API directly -
# only server-to-server requests from the same machine. Keep this bound to localhost only.

app.include_router(venues.router)
app.include_router(users.router)
app.include_router(scores.router)
app.include_router(scrape.router)


@app.get("/health")
def health():
    return {"status": "ok"}
