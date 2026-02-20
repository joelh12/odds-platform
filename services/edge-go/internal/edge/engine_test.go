package edge

import "testing"

func TestComputeReturnsSignals(t *testing.T) {
	match := MatchInput{
		ID: "m1",
		Candidates: []Candidate{
			{Bookmaker: "a", Team: "A", Offered: 1.9},
			{Bookmaker: "b", Team: "A", Offered: 2.2},
		},
	}

	signals := Compute(match, 1)
	if len(signals) == 0 {
		t.Fatalf("expected at least one signal")
	}

	if signals[0].Team != "A" {
		t.Fatalf("unexpected team: %s", signals[0].Team)
	}
}
