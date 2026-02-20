package edge

import "math"

type Candidate struct {
	Bookmaker string  `json:"bookmaker"`
	Team      string  `json:"team"`
	Offered   float64 `json:"offered"`
}

type MatchInput struct {
	ID         string      `json:"id"`
	Candidates []Candidate `json:"candidates"`
}

type Signal struct {
	MatchID     string  `json:"matchId"`
	Bookmaker   string  `json:"bookmaker"`
	Team        string  `json:"team"`
	Offered     float64 `json:"offered"`
	Fair        float64 `json:"fair"`
	EdgePercent float64 `json:"edgePercent"`
}

func round(v float64, precision int) float64 {
	pow := math.Pow(10, float64(precision))
	return math.Round(v*pow) / pow
}

func Compute(match MatchInput, threshold float64) []Signal {
	if len(match.Candidates) == 0 {
		return nil
	}

	sum := 0.0
	for _, c := range match.Candidates {
		sum += c.Offered
	}
	fair := sum / float64(len(match.Candidates))

	var out []Signal
	for _, c := range match.Candidates {
		edge := ((c.Offered / fair) - 1) * 100
		if edge >= threshold {
			out = append(out, Signal{
				MatchID:     match.ID,
				Bookmaker:   c.Bookmaker,
				Team:        c.Team,
				Offered:     c.Offered,
				Fair:        round(fair, 3),
				EdgePercent: round(edge, 2),
			})
		}
	}

	return out
}
