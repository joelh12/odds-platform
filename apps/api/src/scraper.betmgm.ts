import type { MatchOdds } from "@portfolio/shared";
import type { OddsScraper } from "./types.js";

const BETMGM_URL = "https://www.betmgm.se/api/lmbas";
const PERSISTED_QUERY_HASH = "2880618e832c9648047bd384237a25ca0711ac5d8a171476bf565b2a6b115472";

interface BetMgmOptions {
  market: string;
  lang: string;
  offering: string;
  upcomingDays: number;
}

interface BetMgmOutcome {
  odds?: number;
  status?: string;
  label?: string;
  englishLabel?: string;
  participant?: string;
  type?: string;
}

interface BetMgmOffer {
  criterion?: {
    label?: string;
    englishLabel?: string;
  };
  outcomes?: BetMgmOutcome[];
}

interface BetMgmParticipant {
  name?: string;
  home?: boolean;
}

interface BetMgmEvent {
  id?: string | number;
  start?: string | number;
  homeName?: string;
  awayName?: string;
  participants?: BetMgmParticipant[];
  betOffers?: BetMgmOffer[];
}

interface BetMgmLeague {
  name?: string;
  events?: BetMgmEvent[];
}

interface BetMgmGroup {
  groups?: BetMgmLeague[];
}

interface BetMgmResponse {
  data?: {
    viewer?: {
      sports?: {
        sportsEvents?: {
          groups?: BetMgmGroup[];
        };
      };
    };
  };
}

function normalized(input: string | undefined): string {
  return (input ?? "").toLowerCase().trim();
}

function oddsThousandthsToDecimal(odds: number): number {
  return Number((odds / 1000).toFixed(3));
}

function parseStartTime(start: string | number | undefined): string {
  if (typeof start === "number") {
    const millis = start > 1_000_000_000_000 ? start : start * 1000;
    return new Date(millis).toISOString();
  }

  if (typeof start === "string") {
    const asNumber = Number(start);
    if (!Number.isNaN(asNumber)) {
      const millis = asNumber > 1_000_000_000_000 ? asNumber : asNumber * 1000;
      return new Date(millis).toISOString();
    }

    const parsed = new Date(start);
    if (!Number.isNaN(parsed.valueOf())) {
      return parsed.toISOString();
    }
  }

  return new Date().toISOString();
}

function parseTeams(event: BetMgmEvent): [string, string] | null {
  if (event.homeName && event.awayName) {
    return [event.homeName, event.awayName];
  }

  const participants = event.participants ?? [];
  const home = participants.find((participant) => participant.home)?.name;
  const away = participants.find((participant) => participant.home === false)?.name;

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

function resolveOutcomeTeam(
  outcome: BetMgmOutcome,
  teams: [string, string],
  fallbackIndex: 0 | 1
): string {
  const participant = normalized(outcome.participant);
  if (participant === "home") {
    return teams[0];
  }
  if (participant === "away") {
    return teams[1];
  }

  if (participant.includes(normalized(teams[0]))) {
    return teams[0];
  }
  if (participant.includes(normalized(teams[1]))) {
    return teams[1];
  }

  const label = outcome.englishLabel ?? outcome.label;
  const cleanLabel = normalized(label);
  if (cleanLabel.includes(normalized(teams[0]))) {
    return teams[0];
  }
  if (cleanLabel.includes(normalized(teams[1]))) {
    return teams[1];
  }

  return teams[fallbackIndex];
}

function chooseOffer(offers: BetMgmOffer[] | undefined): BetMgmOffer | null {
  if (!offers || offers.length === 0) {
    return null;
  }

  const preferred = offers.find((offer) => {
    const title = normalized(offer.criterion?.englishLabel ?? offer.criterion?.label);
    const outcomeCount = (offer.outcomes ?? []).filter(
      (outcome) => normalized(outcome.status) === "open" && typeof outcome.odds === "number"
    ).length;

    return outcomeCount >= 2 && (
      title.includes("match") ||
      title.includes("winner") ||
      title.includes("matchodds")
    );
  });

  if (preferred) {
    return preferred;
  }

  return (
    offers.find((offer) =>
      (offer.outcomes ?? []).filter(
        (outcome) => normalized(outcome.status) === "open" && typeof outcome.odds === "number"
      ).length >= 2
    ) ?? null
  );
}

export function parseBetMgmSportsEvents(payload: BetMgmResponse): MatchOdds[] {
  const groups = payload.data?.viewer?.sports?.sportsEvents?.groups ?? [];
  const now = new Date().toISOString();
  const matches: MatchOdds[] = [];

  for (const group of groups) {
    for (const league of group.groups ?? []) {
      for (const event of league.events ?? []) {
        const teams = parseTeams(event);
        if (!teams) {
          continue;
        }

        const offer = chooseOffer(event.betOffers);
        if (!offer) {
          continue;
        }

        const openOutcomes = (offer.outcomes ?? []).filter(
          (outcome) => normalized(outcome.status) === "open" && typeof outcome.odds === "number"
        );
        if (openOutcomes.length < 2) {
          continue;
        }

        const first = openOutcomes[0];
        const second = openOutcomes[1];
        if (!first || !second || typeof first.odds !== "number" || typeof second.odds !== "number") {
          continue;
        }

        const id = event.id;
        if (id === undefined || id === null) {
          continue;
        }

        matches.push({
          id: `betmgm-${id}`,
          bookmaker: "betmgm",
          league: league.name ?? "BetMGM Esports",
          startTimeIso: parseStartTime(event.start),
          teams,
          market: "match_winner",
          outcomes: [
            {
              team: resolveOutcomeTeam(first, teams, 0),
              decimalOdds: oddsThousandthsToDecimal(first.odds)
            },
            {
              team: resolveOutcomeTeam(second, teams, 1),
              decimalOdds: oddsThousandthsToDecimal(second.odds)
            }
          ],
          scrapedAtIso: now
        });
      }
    }
  }

  return matches;
}

function buildPayload(options: BetMgmOptions): Record<string, unknown> {
  return {
    operationName: "SportLeaguesQuery",
    variables: {
      market: options.market,
      lang: options.lang,
      offering: options.offering,
      filter: {
        sport: "esports",
        upcomingDays: options.upcomingDays,
        eventType: "MATCH"
      },
      grouping: ["LEAGUE_POPULARITY", "COUNTRY_AZ"],
      first: 10,
      after: "0",
      pageRequest: {
        pageNumber: 0,
        pageSize: 5
      },
      allFilter: {
        sport: "esports",
        upcomingDays: 20,
        eventType: "MATCH"
      },
      allGrouping: ["COUNTRY_AZ", "LEAGUE_POPULARITY"],
      skipAllLeaguesSportsQuery: false,
      skipPopularLeaguesSportsQuery: false,
      skipAllOutrightsSportsQuery: true,
      popularEventsGroup: [],
      variant: "default"
    },
    extensions: {
      persistedQuery: {
        version: 1,
        sha256Hash: PERSISTED_QUERY_HASH
      }
    }
  };
}

export class BetMgmScraper implements OddsScraper {
  public readonly source = "betmgm";

  public constructor(private readonly options: BetMgmOptions) {}

  public async scrape(): Promise<MatchOdds[]> {
    const headers = {
      "User-Agent": "portfolio-odds-platform/1.0",
      "Accept": "*/*",
      "Content-Type": "application/json",
      "Origin": "https://www.betmgm.se",
      "Referer": "https://www.betmgm.se/sport",
      "x-app-id": "sportsbook",
      "x-client-id": "sportsbook"
    };

    const response = await fetch(BETMGM_URL, {
      method: "POST",
      headers,
      body: JSON.stringify(buildPayload(this.options)),
      signal: AbortSignal.timeout(12_000)
    });

    if (!response.ok) {
      throw new Error(`BetMGM fetch failed: ${response.status}`);
    }

    const payload = (await response.json()) as BetMgmResponse;
    return parseBetMgmSportsEvents(payload);
  }
}
