# Architecture

## Components
- `apps/api`: TypeScript odds ingestion + normalization + edge scoring + SSE API.
- `apps/web`: Next.js dashboard subscribing to realtime snapshots.
- `packages/shared`: Shared contract types between API and frontend.
- `services/edge-go`: Optional Go microservice for independent edge computation.

## Data flow
1. Scrapers collect raw odds (`MockScraper`, optional `HttpScraper`, optional `BetMgmScraper`, optional `PinnacleScraper`).
2. Pipeline normalizes a two-way market model (`match_winner`).
3. Edge engine estimates fair odds from cross-book probabilities.
4. API publishes snapshots over `/api/snapshot` and `/api/stream` (SSE).
5. Next.js UI renders matches and top edge opportunities in near-realtime.

## Why this fits the role
- TypeScript-first backend and frontend.
- Realtime stream handling and incremental updates.
- Scraper ingestion abstraction to plug in additional bookmakers.
- Bonus Go service for performance-critical scoring paths.
