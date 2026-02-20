"use client";

import { useEffect, useMemo, useState } from "react";
import type { FeedSnapshot } from "@portfolio/shared";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:4000";

export function LiveBoard() {
  const [snapshot, setSnapshot] = useState<FeedSnapshot | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/api/stream`);

    eventSource.addEventListener("snapshot", (event) => {
      const parsed = JSON.parse((event as MessageEvent<string>).data) as FeedSnapshot;
      setSnapshot(parsed);
      setConnected(true);
    });

    eventSource.onerror = () => {
      setConnected(false);
    };

    return () => eventSource.close();
  }, []);

  const topSignals = useMemo(
    () => snapshot?.valueSignals.slice(0, 5) ?? [],
    [snapshot]
  );

  return (
    <main className="page">
      <section className="hero">
        <p className="eyebrow">Realtime Odds Platform</p>
        <h1>Value betting infrastructure demo</h1>
        <p>
          Built with Next.js and TypeScript. Streaming live snapshots from a scraper
          pipeline with signal generation and alert-ready edge scoring.
        </p>
        <div className="statusRow">
          <span className={connected ? "badge ok" : "badge down"}>
            {connected ? "stream connected" : "reconnecting"}
          </span>
          <span className="small">
            {snapshot ? `last update: ${new Date(snapshot.receivedAtIso).toLocaleTimeString()}` : "waiting for data"}
          </span>
        </div>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Matches</h2>
          {(snapshot?.matches ?? []).map((match) => (
            <div key={`${match.bookmaker}-${match.id}`} className="row">
              <div>
                <strong>{match.teams[0]} vs {match.teams[1]}</strong>
                <p>{match.league} · {match.bookmaker}</p>
              </div>
              <div className="odds">
                <span>{match.outcomes[0].decimalOdds.toFixed(2)}</span>
                <span>{match.outcomes[1].decimalOdds.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </article>

        <article className="panel">
          <h2>Top value signals</h2>
          {topSignals.length === 0 && <p>No edge above threshold right now.</p>}
          {topSignals.map((signal) => (
            <div key={`${signal.matchId}-${signal.bookmaker}-${signal.team}`} className="row">
              <div>
                <strong>{signal.team}</strong>
                <p>{signal.bookmaker}</p>
              </div>
              <div className="signal">
                <span className="edge">+{signal.edgePercent.toFixed(2)}%</span>
                <span>{signal.offeredOdds.toFixed(2)} vs fair {signal.fairOdds.toFixed(2)}</span>
              </div>
            </div>
          ))}
        </article>
      </section>
    </main>
  );
}
