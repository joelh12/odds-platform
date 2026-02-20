# Odds Platform Portfolio (TypeScript + Go)

A rebuild of an odds scraping project

This repository keeps the original Python scripts in `/scrapers` as legacy research artifacts, while the production-style portfolio stack is in:
- `/apps/api` (TypeScript realtime API + pipeline)
- `/apps/web` (Next.js dashboard)
- `/packages/shared` (shared contracts)
- `/services/edge-go` (Go edge-scoring microservice)

## Highlights
- Realtime stream via Server-Sent Events (`/api/stream`)
- Scraper abstraction with pluggable sources (`MockScraper`, `HttpScraper`, `BetMgmScraper`, `PinnacleScraper`)
- Value-bet signal generation from normalized implied probabilities
- Shared types between backend and frontend
- Go bonus service with independent tests and health endpoint
- CI workflow for TS/Next/Go build and tests

## Quick start

### 1) Install dependencies
```bash
npm install
```

### 2) Build shared package
```bash
npm run build -w @portfolio/shared
```

### 3) Run API
```bash
npm run dev -w @portfolio/api
```

### 4) Run frontend (new terminal)
```bash
npm run dev -w @portfolio/web
```

Frontend: `http://localhost:3000`  
API: `http://localhost:4000`

## Environment
Copy `.env.example` to `.env` and adjust values as needed.

Important variables:
- `PORT` (default `4000`)
- `POLL_INTERVAL_MS` (default `4000`)
- `ODDS_SOURCE_URL` (optional upstream JSON source)
- `ALERT_EDGE_THRESHOLD` (default `3`)
- `NEXT_PUBLIC_API_BASE_URL` (default `http://localhost:4000`)
- `BETMGM_ENABLED` (`true/false`)
- `BETMGM_MARKET` / `BETMGM_LANG` / `BETMGM_OFFERING` (defaults `SE` / `sv_SE` / `betmgmse`)
- `BETMGM_UPCOMING_DAYS` (default `2`)
- `PINNACLE_ENABLED` (`true/false`)
- `PINNACLE_API_KEY` / `PINNACLE_DEVICE_UUID` (required when Pinnacle enabled)
- `PINNACLE_LEAGUE_ID` / `PINNACLE_BRAND_ID` (optional, defaults `12` / `0`)

## Real scraper mode (BetMGM and Pinnacle)
1. Set `BETMGM_ENABLED=true` and/or `PINNACLE_ENABLED=true` in `.env`.
2. For Pinnacle, also set `PINNACLE_API_KEY` and `PINNACLE_DEVICE_UUID`.
3. Start the API with `npm run dev -w @portfolio/api`.
4. Check `GET /api/meta` to confirm `betmgm` / `pinnacle` appear in `sources`.

## API endpoints
- `GET /health` - service health
- `GET /api/snapshot` - latest pipeline snapshot
- `GET /api/meta` - current source list and pipeline settings
- `GET /api/stream` - realtime snapshots via SSE

## Tests
```bash
npm run test -w @portfolio/api
go test ./... -C services/edge-go
```

## Smoke Tests
Local smoke test:
```bash
npm run smoke
```

Docker smoke test (requires Docker daemon running):
```bash
npm run smoke:docker
```

## Docker
```bash
docker compose up --build
```

Services:
- API: `http://localhost:4000`
- Web: `http://localhost:3000`
- Go edge service: `http://localhost:8082`

## CI
GitHub Actions workflow:
- `/.github/workflows/ci.yml`
- Runs TS install/build/tests and Go tests on push/PR.

## talking points
- Designed and implemented a realtime odds ingestion and alert pipeline in TypeScript.
- Built a Next.js dashboard consuming SSE updates with resilient reconnect behavior.
- Established shared contracts across services for safer cross-layer evolution.
- Added a Go scoring service to demonstrate polyglot backend capability.
- Treated legacy Python scrapers as source adapters while moving core infra to TS/Go.

## Next upgrades 
1. Add Postgres + Redis for persistence and dedupe.
2. Add queue-based ingestion (NATS/Kafka) for higher volume.
3. Add alert delivery workers (Telegram/Discord/Webhook).
4. Add metrics/tracing (Prometheus/OpenTelemetry).
5. Add CI workflow with lint/typecheck/test gates.
