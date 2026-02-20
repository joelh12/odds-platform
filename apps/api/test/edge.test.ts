import test from "node:test";
import assert from "node:assert/strict";
import type { MatchOdds } from "@portfolio/shared";
import { computeValueSignals } from "../src/edge.js";

test("computeValueSignals returns positive edge opportunities", () => {
  const matches: MatchOdds[] = [
    {
      id: "1",
      bookmaker: "pinnacle",
      league: "Test League",
      startTimeIso: new Date().toISOString(),
      teams: ["A", "B"],
      market: "match_winner",
      outcomes: [
        { team: "A", decimalOdds: 1.9 },
        { team: "B", decimalOdds: 1.9 }
      ],
      scrapedAtIso: new Date().toISOString()
    },
    {
      id: "2",
      bookmaker: "betmgm",
      league: "Test League",
      startTimeIso: new Date().toISOString(),
      teams: ["A", "B"],
      market: "match_winner",
      outcomes: [
        { team: "A", decimalOdds: 2.2 },
        { team: "B", decimalOdds: 1.7 }
      ],
      scrapedAtIso: new Date().toISOString()
    }
  ];

  const signals = computeValueSignals(matches, 1);
  assert.ok(signals.length > 0);
  assert.equal(signals[0]?.team, "A");
  assert.ok(signals[0]?.edgePercent && signals[0].edgePercent > 1);
});
