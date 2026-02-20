import type { MatchOdds } from "@portfolio/shared";
import type { OddsScraper } from "./types.js";

interface RemotePayload {
  matches: Array<{
    id: string;
    bookmaker: MatchOdds["bookmaker"];
    league: string;
    startTimeIso: string;
    teams: [string, string];
    outcomes: [
      { team: string; decimalOdds: number },
      { team: string; decimalOdds: number }
    ];
  }>;
}

export class HttpScraper implements OddsScraper {
  public readonly source = "http-source";

  public constructor(private readonly url: string) {}

  public async scrape(): Promise<MatchOdds[]> {
    const response = await fetch(this.url, {
      headers: { Accept: "application/json" }
    });

    if (!response.ok) {
      throw new Error(`Upstream scraper source failed: ${response.status}`);
    }

    const body = (await response.json()) as RemotePayload;
    const now = new Date().toISOString();

    return body.matches.map((match) => ({
      id: match.id,
      bookmaker: match.bookmaker,
      league: match.league,
      startTimeIso: match.startTimeIso,
      teams: match.teams,
      market: "match_winner",
      outcomes: match.outcomes,
      scrapedAtIso: now
    }));
  }
}
