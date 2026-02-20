import type { FeedSnapshot, MatchOdds } from "@portfolio/shared";
import type { OddsScraper } from "./types.js";
import { computeValueSignals } from "./edge.js";

export class Pipeline {
  private snapshot: FeedSnapshot = {
    receivedAtIso: new Date(0).toISOString(),
    matches: [],
    valueSignals: []
  };

  public constructor(
    private readonly scrapers: OddsScraper[],
    private readonly thresholdPercent: number
  ) {}

  public current(): FeedSnapshot {
    return this.snapshot;
  }

  public async tick(): Promise<FeedSnapshot> {
    const settled = await Promise.allSettled(this.scrapers.map((scraper) => scraper.scrape()));

    const matches: MatchOdds[] = [];

    for (const result of settled) {
      if (result.status === "fulfilled") {
        matches.push(...result.value);
      }
    }

    this.snapshot = {
      receivedAtIso: new Date().toISOString(),
      matches,
      valueSignals: computeValueSignals(matches, this.thresholdPercent)
    };

    return this.snapshot;
  }
}
