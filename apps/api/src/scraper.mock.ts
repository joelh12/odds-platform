import type { MatchOdds } from "@portfolio/shared";
import type { OddsScraper } from "./types.js";

function hoursFromNow(hours: number): string {
  return new Date(Date.now() + hours * 60 * 60 * 1000).toISOString();
}

export class MockScraper implements OddsScraper {
  public readonly source = "mockbook";

  public async scrape(): Promise<MatchOdds[]> {
    const now = new Date().toISOString();

    return [
      {
        id: "cs2-blast-001",
        bookmaker: "mockbook",
        league: "BLAST Premier",
        startTimeIso: hoursFromNow(2),
        teams: ["Natus Vincere", "FaZe Clan"],
        market: "match_winner",
        outcomes: [
          { team: "Natus Vincere", decimalOdds: 1.88 },
          { team: "FaZe Clan", decimalOdds: 2.04 }
        ],
        scrapedAtIso: now
      },
      {
        id: "cs2-iem-002",
        bookmaker: "mockbook",
        league: "IEM Katowice",
        startTimeIso: hoursFromNow(5),
        teams: ["Vitality", "MOUZ"],
        market: "match_winner",
        outcomes: [
          { team: "Vitality", decimalOdds: 1.64 },
          { team: "MOUZ", decimalOdds: 2.38 }
        ],
        scrapedAtIso: now
      }
    ];
  }
}
