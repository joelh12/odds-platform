import type { MatchOdds, ValueSignal } from "@portfolio/shared";

interface ProbabilityPair {
  first: number;
  second: number;
}

function impliedProbability(decimalOdds: number): number {
  return 1 / decimalOdds;
}

function normalizeTwoWayMarket(match: MatchOdds): ProbabilityPair {
  const first = impliedProbability(match.outcomes[0].decimalOdds);
  const second = impliedProbability(match.outcomes[1].decimalOdds);
  const overround = first + second;

  return {
    first: first / overround,
    second: second / overround
  };
}

function fairOdds(probability: number): number {
  return 1 / probability;
}

function edgePercent(offered: number, fair: number): number {
  return ((offered / fair) - 1) * 100;
}

export function computeValueSignals(matches: MatchOdds[], thresholdPercent: number): ValueSignal[] {
  const grouped = new Map<string, MatchOdds[]>();

  for (const match of matches) {
    const key = `${match.teams[0]}::${match.teams[1]}::${match.league}`;
    const bucket = grouped.get(key) ?? [];
    bucket.push(match);
    grouped.set(key, bucket);
  }

  const generatedAtIso = new Date().toISOString();
  const output: ValueSignal[] = [];

  for (const [, books] of grouped) {
    if (books.length === 0) {
      continue;
    }

    const fairSamples = books.map((book) => {
      const normalized = normalizeTwoWayMarket(book);
      const offered: [number, number] = [book.outcomes[0].decimalOdds, book.outcomes[1].decimalOdds];
      const fair: [number, number] = [fairOdds(normalized.first), fairOdds(normalized.second)];
      return {
        matchId: book.id,
        bookmaker: book.bookmaker,
        teams: book.teams,
        offered,
        fair
      };
    });

    const fairOne = fairSamples.reduce((sum, sample) => sum + sample.fair[0], 0) / fairSamples.length;
    const fairTwo = fairSamples.reduce((sum, sample) => sum + sample.fair[1], 0) / fairSamples.length;

    for (const sample of fairSamples) {
      const teamAEdge = edgePercent(sample.offered[0], fairOne);
      const teamBEdge = edgePercent(sample.offered[1], fairTwo);

      if (teamAEdge >= thresholdPercent) {
        output.push({
          matchId: sample.matchId,
          bookmaker: sample.bookmaker,
          team: sample.teams[0],
          offeredOdds: sample.offered[0],
          fairOdds: Number(fairOne.toFixed(3)),
          edgePercent: Number(teamAEdge.toFixed(2)),
          generatedAtIso
        });
      }

      if (teamBEdge >= thresholdPercent) {
        output.push({
          matchId: sample.matchId,
          bookmaker: sample.bookmaker,
          team: sample.teams[1],
          offeredOdds: sample.offered[1],
          fairOdds: Number(fairTwo.toFixed(3)),
          edgePercent: Number(teamBEdge.toFixed(2)),
          generatedAtIso
        });
      }
    }
  }

  return output.sort((a, b) => b.edgePercent - a.edgePercent);
}
