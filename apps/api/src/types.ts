import type { MatchOdds } from "@portfolio/shared";

export interface OddsScraper {
  source: string;
  scrape(): Promise<MatchOdds[]>;
}
