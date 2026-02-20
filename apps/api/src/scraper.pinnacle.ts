import type { MatchOdds } from "@portfolio/shared";
import type { OddsScraper } from "./types.js";

const API_BASE = "https://guest.api.arcadia.pinnacle.se";

interface PinnacleScraperOptions {
  apiKey: string;
  deviceUuid: string;
  leagueId: number;
  brandId: number;
}

interface PinnacleParticipant {
  name?: string;
  alignment?: "home" | "away" | string;
}

interface PinnacleMatchup {
  id?: number;
  matchupId?: number;
  startTime?: string;
  participants?: PinnacleParticipant[];
  league?: {
    name?: string;
  };
}

interface PinnaclePrice {
  designation?: "home" | "away" | string;
  price?: number;
}

interface PinnacleMarket {
  type?: string;
  period?: number | string;
  prices?: PinnaclePrice[];
}

export function americanToDecimal(price: number): number {
  if (price > 0) {
    return Number(((price / 100) + 1).toFixed(3));
  }

  return Number(((100 / Math.abs(price)) + 1).toFixed(3));
}

function parseTeams(participants: PinnacleParticipant[] | undefined): [string, string] | null {
  if (!participants || participants.length < 2) {
    return null;
  }

  const home = participants.find((participant) => participant.alignment === "home")?.name;
  const away = participants.find((participant) => participant.alignment === "away")?.name;

  if (home && away) {
    return [home, away];
  }

  const fallbackHome = participants[0]?.name;
  const fallbackAway = participants[1]?.name;
  if (fallbackHome && fallbackAway) {
    return [fallbackHome, fallbackAway];
  }

  return null;
}

export class PinnacleScraper implements OddsScraper {
  public readonly source = "pinnacle";
  private readonly headers: Record<string, string>;

  public constructor(private readonly options: PinnacleScraperOptions) {
    this.headers = {
      "User-Agent": "portfolio-odds-platform/1.0",
      "accept": "application/json",
      "x-api-key": options.apiKey,
      "x-device-uuid": options.deviceUuid
    };
  }

  public async scrape(): Promise<MatchOdds[]> {
    const matchupUrl = `${API_BASE}/0.1/leagues/${this.options.leagueId}/matchups?brandId=${this.options.brandId}`;
    const response = await fetch(matchupUrl, {
      headers: this.headers,
      signal: AbortSignal.timeout(10_000)
    });

    if (response.status === 204) {
      return [];
    }

    if (!response.ok) {
      throw new Error(`Pinnacle matchup fetch failed: ${response.status}`);
    }

    const matchups = (await response.json()) as PinnacleMatchup[];
    const settled = await Promise.allSettled(matchups.map(async (matchup) => this.fetchMatchOdds(matchup)));

    const output: MatchOdds[] = [];
    for (const result of settled) {
      if (result.status === "fulfilled" && result.value) {
        output.push(result.value);
      }
    }

    return output;
  }

  private async fetchMatchOdds(matchup: PinnacleMatchup): Promise<MatchOdds | null> {
    const matchupId = matchup.id ?? matchup.matchupId;
    if (!matchupId) {
      return null;
    }

    const teams = parseTeams(matchup.participants);
    if (!teams) {
      return null;
    }

    const marketsUrl = `${API_BASE}/0.1/matchups/${matchupId}/markets/related/straight`;
    const response = await fetch(marketsUrl, {
      headers: this.headers,
      signal: AbortSignal.timeout(10_000)
    });

    if (!response.ok) {
      return null;
    }

    const markets = (await response.json()) as PinnacleMarket[];
    const moneyline = markets.find((market) =>
      market.type === "moneyline" && Number(market.period) === 0
    );

    if (!moneyline?.prices) {
      return null;
    }

    const homePrice = moneyline.prices.find((price) => price.designation === "home")?.price;
    const awayPrice = moneyline.prices.find((price) => price.designation === "away")?.price;

    if (typeof homePrice !== "number" || typeof awayPrice !== "number") {
      return null;
    }

    const nowIso = new Date().toISOString();

    return {
      id: `pinnacle-${matchupId}`,
      bookmaker: "pinnacle",
      league: matchup.league?.name ?? `Pinnacle League ${this.options.leagueId}`,
      startTimeIso: matchup.startTime ? new Date(matchup.startTime).toISOString() : nowIso,
      teams,
      market: "match_winner",
      outcomes: [
        { team: teams[0], decimalOdds: americanToDecimal(homePrice) },
        { team: teams[1], decimalOdds: americanToDecimal(awayPrice) }
      ],
      scrapedAtIso: nowIso
    };
  }
}
