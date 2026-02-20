import test from "node:test";
import assert from "node:assert/strict";
import { parseBetMgmSportsEvents } from "../src/scraper.betmgm.js";

test("parseBetMgmSportsEvents extracts match winner market", () => {
  const payload = {
    data: {
      viewer: {
        sports: {
          sportsEvents: {
            groups: [
              {
                groups: [
                  {
                    name: "BLAST Premier",
                    events: [
                      {
                        id: "evt-1",
                        start: 1_740_000_000_000,
                        homeName: "Natus Vincere",
                        awayName: "FaZe Clan",
                        betOffers: [
                          {
                            criterion: { englishLabel: "Match Winner" },
                            outcomes: [
                              { status: "OPEN", odds: 1900, participant: "home" },
                              { status: "OPEN", odds: 2050, participant: "away" }
                            ]
                          }
                        ]
                      }
                    ]
                  }
                ]
              }
            ]
          }
        }
      }
    }
  };

  const matches = parseBetMgmSportsEvents(payload);
  assert.equal(matches.length, 1);
  assert.equal(matches[0]?.bookmaker, "betmgm");
  assert.equal(matches[0]?.league, "BLAST Premier");
  assert.equal(matches[0]?.outcomes[0].decimalOdds, 1.9);
  assert.equal(matches[0]?.outcomes[1].decimalOdds, 2.05);
  assert.equal(matches[0]?.outcomes[0].team, "Natus Vincere");
  assert.equal(matches[0]?.outcomes[1].team, "FaZe Clan");
});

test("parseBetMgmSportsEvents skips malformed events", () => {
  const payload = {
    data: {
      viewer: {
        sports: {
          sportsEvents: {
            groups: [
              {
                groups: [
                  {
                    name: "Broken League",
                    events: [
                      {
                        id: "evt-bad",
                        participants: [{ name: "Only One" }],
                        betOffers: []
                      }
                    ]
                  }
                ]
              }
            ]
          }
        }
      }
    }
  };

  const matches = parseBetMgmSportsEvents(payload);
  assert.equal(matches.length, 0);
});
