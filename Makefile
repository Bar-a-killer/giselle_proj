.PHONY: help install backend-install frontend-install init-db \
	backend-dev frontend-dev dev test lint scrape embeddings clean

QUERY ?= coffee in Capitol Hill Seattle
DEPTH ?= 5

help: ## Show this help
	@echo "Usage: make <target> [QUERY=\"...\"] [DEPTH=N]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: backend-install frontend-install ## Install backend + frontend dependencies

backend-install: ## Install backend dependencies (uv sync)
	cd backend && uv sync

frontend-install: ## Install frontend dependencies (npm install)
	cd frontend && npm install

init-db: ## Create the SQLite schema (one-time, or after wiping the DB)
	cd backend && uv run python scripts/init_db.py

backend-dev: ## Run the backend dev server (port 8001)
	cd backend && uv run uvicorn app.main:app --reload --port 8001

frontend-dev: ## Run the frontend dev server (Next.js)
	cd frontend && npm run dev

dev: ## Run backend + frontend together (Ctrl-C stops both)
	@trap 'kill 0' INT TERM EXIT; \
	( cd backend && uv run uvicorn app.main:app --reload --port 8001 ) & \
	( cd frontend && npm run dev ) & \
	wait

test: ## Run backend tests (pytest)
	cd backend && uv run pytest

lint: ## Lint the frontend
	cd frontend && npm run lint

scrape: ## Scrape venues: make scrape QUERY="..." DEPTH=5
	cd backend && uv run python scripts/run_scrape.py --query "$(QUERY)" --depth $(DEPTH)

embeddings: ## Build venue embeddings after scraping
	cd backend && uv run python scripts/build_embeddings.py

clean: ## Remove build/cache artifacts (not the DB, not node_modules/.venv)
	rm -rf frontend/.next backend/.pytest_cache
