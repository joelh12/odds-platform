# Production Hardening Checklist

## Reliability
- Retry with exponential backoff per source.
- Circuit-breaker behavior for unstable bookmakers.
- Dead-letter queue for malformed payloads.

## Data quality
- Match canonicalization service (team aliases, tournament aliases).
- Timestamp drift checks and stale snapshot alarms.
- Unit tests for normalization + property tests for edge math.

## Platform
- Structured logs with request and trace IDs.
- Metrics: scrape success rate, latency, signal volume, queue lag.
- SLOs with alerting (on stale feed and high error rates).

## Security
- Move all secrets to environment/secret manager.
- Per-source user agent and rate-limit compliance rules.
- Input validation on every ingress boundary.
