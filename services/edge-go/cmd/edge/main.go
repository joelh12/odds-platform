package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"strconv"

	"github.com/joelhogelin/odds-platform-portfolio/services/edge-go/internal/edge"
)

type requestBody struct {
	Match edge.MatchInput `json:"match"`
}

type responseBody struct {
	Signals []edge.Signal `json:"signals"`
}

func main() {
	threshold := 2.0
	if val := os.Getenv("EDGE_THRESHOLD"); val != "" {
		if parsed, err := strconv.ParseFloat(val, 64); err == nil {
			threshold = parsed
		}
	}

	http.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"status":"ok","service":"edge-go"}`))
	})

	http.HandleFunc("/compute", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		var req requestBody
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "bad json", http.StatusBadRequest)
			return
		}

		resp := responseBody{Signals: edge.Compute(req.Match, threshold)}
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(resp)
	})

	addr := ":8082"
	log.Printf("edge-go listening on %s", addr)
	log.Fatal(http.ListenAndServe(addr, nil))
}
