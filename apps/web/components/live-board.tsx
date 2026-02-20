"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import type { FeedSnapshot } from "@portfolio/shared";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:4000";

function useClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return now;
}

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function truncate(str: string, len: number) {
  return str.length > len ? str.slice(0, len) + "…" : str;
}

export function LiveBoard() {
  const [snapshot, setSnapshot] = useState<FeedSnapshot | null>(null);
  const [connected, setConnected] = useState(false);
  const clock = useClock();

  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/api/stream`);

    eventSource.addEventListener("snapshot", (event) => {
      const parsed = JSON.parse(
        (event as MessageEvent<string>).data
      ) as FeedSnapshot;
      setSnapshot(parsed);
      setConnected(true);
    });

    eventSource.onerror = () => {
      setConnected(false);
    };

    return () => eventSource.close();
  }, []);

  const topSignals = useMemo(
    () => snapshot?.valueSignals.slice(0, 8) ?? [],
    [snapshot]
  );
  const matches = snapshot?.matches ?? [];
  const sourceCount = useMemo(
    () => new Set(matches.map((m) => m.bookmaker)).size,
    [matches]
  );
  const averageEdge = useMemo(() => {
    if (topSignals.length === 0) return 0;
    return (
      topSignals.reduce((s, sig) => s + sig.edgePercent, 0) / topSignals.length
    );
  }, [topSignals]);
  const strongest = topSignals[0];

  return (
    <main className="terminal">
      {/* ── TOP BAR ── */}
      <header className="topbar">
        <div className="topbar-brand">
          <div className="topbar-logo">
            ODDS<span>TERM</span>
          </div>
          <span className="topbar-tag">Live</span>
        </div>
        <div className="topbar-right">
          <span className="topbar-clock">
            {clock.toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </span>
          <span
            className={`topbar-status ${connected ? "topbar-status--ok" : "topbar-status--down"}`}
          >
            <span
              className={`status-dot ${connected ? "status-dot--ok" : "status-dot--down"}`}
            />
            {connected ? "Connected" : "Offline"}
          </span>
        </div>
      </header>

      {/* ── STATS RIBBON ── */}
      <section className="stats-ribbon">
        <div className="stat-cell">
          <div className="stat-label">Matches</div>
          <div className="stat-value">{matches.length}</div>
        </div>
        <div className="stat-cell">
          <div className="stat-label">Signals</div>
          <div className="stat-value stat-value--green">{topSignals.length}</div>
        </div>
        <div className="stat-cell">
          <div className="stat-label">Sources</div>
          <div className="stat-value">{sourceCount}</div>
        </div>
        <div className="stat-cell">
          <div className="stat-label">Avg Edge</div>
          <div className="stat-value stat-value--edge">
            {averageEdge.toFixed(2)}%
          </div>
        </div>
      </section>

      {/* ── CONTENT GRID ── */}
      <div className="content">
        {/* LEFT: Match Board */}
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Match Board</span>
            <span className="panel-badge">{matches.length} rows</span>
          </div>
          <div className="panel-body">
            {matches.length === 0 ? (
              <div className="empty-state">
                {snapshot ? "No active matches" : "Awaiting data feed"}
              </div>
            ) : (
              <table className="match-table">
                <thead>
                  <tr>
                    <th>League</th>
                    <th>Match</th>
                    <th className="col-odds">Odds</th>
                    <th>Book</th>
                    <th style={{ textAlign: "right" }}>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {matches.map((match, i) => (
                    <tr
                      key={`${match.bookmaker}-${match.id}`}
                      className="match-row"
                      style={{ animationDelay: `${i * 0.03}s` }}
                    >
                      <td>
                        <span className="match-league">
                          {truncate(match.league, 18)}
                        </span>
                      </td>
                      <td>
                        <span className="match-teams">
                          {truncate(match.teams[0], 14)}
                          <span>vs</span>
                          {truncate(match.teams[1], 14)}
                        </span>
                      </td>
                      <td>
                        <div className="odds-cell">
                          <div className="odds-btn">
                            <span className="odds-btn-label">
                              {truncate(match.outcomes[0].team, 8)}
                            </span>
                            <span className="odds-btn-value">
                              {match.outcomes[0].decimalOdds.toFixed(2)}
                            </span>
                          </div>
                          <div className="odds-btn">
                            <span className="odds-btn-label">
                              {truncate(match.outcomes[1].team, 8)}
                            </span>
                            <span className="odds-btn-value">
                              {match.outcomes[1].decimalOdds.toFixed(2)}
                            </span>
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="match-book">{match.bookmaker}</span>
                      </td>
                      <td>
                        <span className="match-time">
                          {formatTime(match.startTimeIso)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </section>

        {/* RIGHT: Signal Ladder */}
        <section className="panel">
          <div className="panel-header">
            <span className="panel-title">Edge Signals</span>
            <span className="panel-badge">
              {topSignals.length} opportunities
            </span>
          </div>
          <div className="panel-body">
            {topSignals.length === 0 ? (
              <div className="empty-state">No edge above threshold</div>
            ) : (
              topSignals.map((signal, i) => {
                const isHot = signal.edgePercent >= 5;
                const barWidth = Math.min(signal.edgePercent * 8, 100);
                return (
                  <div
                    key={`${signal.matchId}-${signal.bookmaker}-${signal.team}`}
                    className="signal-row"
                    style={{ animationDelay: `${i * 0.04}s` }}
                  >
                    <div
                      className={`signal-rank ${isHot ? "signal-rank--hot" : "signal-rank--warm"}`}
                    />
                    <div className="signal-info">
                      <div className="signal-team">
                        {truncate(signal.team, 20)}
                      </div>
                      <div className="signal-meta">
                        <span className="signal-book">{signal.bookmaker}</span>
                        <span className="signal-odds">
                          {signal.offeredOdds.toFixed(2)}{" "}
                          <span className="fair">
                            / {signal.fairOdds.toFixed(2)} fair
                          </span>
                        </span>
                      </div>
                    </div>
                    <div className="signal-edge">
                      <div
                        className={`signal-edge-value ${isHot ? "signal-edge-value--high" : "signal-edge-value--med"}`}
                      >
                        +{signal.edgePercent.toFixed(2)}%
                      </div>
                      <div className="edge-bar-track">
                        <div
                          className={`edge-bar-fill ${isHot ? "edge-bar-fill--high" : "edge-bar-fill--med"}`}
                          style={{ width: `${barWidth}%` }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </section>
      </div>

      {/* ── BOTTOM TICKER ── */}
      <div className="ticker">
        <span className="ticker-label">
          <span className="ticker-dot" />
          Feed
        </span>
        <span className="ticker-content">
          {strongest ? (
            <>
              Top edge: <strong>{truncate(strongest.team, 16)}</strong> @{" "}
              {strongest.bookmaker}{" "}
              <strong>+{strongest.edgePercent.toFixed(2)}%</strong>
              <span className="ticker-sep">|</span>
              Offered {strongest.offeredOdds.toFixed(2)} vs fair{" "}
              {strongest.fairOdds.toFixed(2)}
            </>
          ) : (
            "Scanning for value opportunities…"
          )}
        </span>
        <span className="ticker-ts">
          {snapshot
            ? `UPD ${formatTime(snapshot.receivedAtIso)}`
            : "—"}
        </span>
      </div>
    </main>
  );
}
