export type Bookmaker = "pinnacle" | "betmgm" | "stake" | "thunderpick" | "mockbook";

export interface OutcomeOdds {
  team: string;
  decimalOdds: number;
}

export interface MatchOdds {
  id: string;
  bookmaker: Bookmaker;
  league: string;
  startTimeIso: string;
  teams: [string, string];
  market: "match_winner";
  outcomes: [OutcomeOdds, OutcomeOdds];
  scrapedAtIso: string;
}

export interface ValueSignal {
  matchId: string;
  bookmaker: Bookmaker;
  team: string;
  offeredOdds: number;
  fairOdds: number;
  edgePercent: number;
  generatedAtIso: string;
}

export interface FeedSnapshot {
  receivedAtIso: string;
  matches: MatchOdds[];
  valueSignals: ValueSignal[];
}
