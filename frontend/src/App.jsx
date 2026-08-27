import { useState } from "react";
import MarqueeHeader from "./components/MarqueeHeader";
import ModeTabs from "./components/ModeTabs";
import GenrePicker from "./components/GenrePicker";
import TopRatedPanel from "./components/TopRatedPanel";
import MovieSearchPicker from "./components/MovieSearchPicker";
import TicketCard from "./components/TicketCard";
import {
  getRecommendations,
  recommendByGenre,
  recommendTopRated,
  API_URL,
} from "./api";

export default function App() {
  const [mode, setMode] = useState("genre");
  const [genre, setGenre] = useState(null);
  const [liked, setLiked] = useState([]);
  const [recs, setRecs] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const canFetch =
    mode === "ratings" ||
    (mode === "genre" && genre != null) ||
    (mode === "cold" && liked.length > 0);

  async function handleGetRecommendations() {
    setLoading(true);
    setError(null);
    setRecs(null);
    try {
      let data;
      if (mode === "genre") {
        data = await recommendByGenre(genre, 10);
      } else if (mode === "ratings") {
        data = await recommendTopRated(10);
      } else {
        data = await getRecommendations({
          likedMovieIds: liked.map((m) => m.movie_id),
          topN: 10,
        });
      }
      setRecs(data);
    } catch (e) {
      setError(
        e.message.includes("Failed to fetch")
          ? `Can't reach the recommendation service at ${API_URL}. Is the backend running?`
          : e.message
      );
    } finally {
      setLoading(false);
    }
  }

  function handleModeChange(next) {
    setMode(next);
    setRecs(null);
    setError(null);
  }

  return (
    <div className="min-h-screen">
      <div className="max-w-5xl mx-auto px-6">
        <MarqueeHeader />

        <ModeTabs mode={mode} onChange={handleModeChange} />

        <div className="mt-6">
          {mode === "genre" && <GenrePicker genre={genre} onSelect={setGenre} />}
          {mode === "ratings" && <TopRatedPanel />}
          {mode === "cold" && <MovieSearchPicker liked={liked} onChange={setLiked} />}
        </div>

        <div className="mt-6 flex items-center gap-4">
          <button
            onClick={handleGetRecommendations}
            disabled={!canFetch || loading}
            className="font-display text-lg tracking-wide bg-amber text-ink px-6 py-3 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed hover:bg-amber-dim transition-colors cursor-pointer"
          >
            {loading ? "Pulling tickets…" : "Get Recommendations"}
          </button>
          {!canFetch && (
            <span className="text-xs text-muted">
              {mode === "genre" && "Pick a genre first"}
              {mode === "cold" && "Add at least one movie you like"}
            </span>
          )}
        </div>

        {error && (
          <p className="mt-6 text-sm text-danger bg-danger/10 border border-danger/30 rounded-lg px-4 py-3">
            {error}
          </p>
        )}

        {recs && (
          <div className="mt-10 pb-16">
            <div className="bulb-strip mb-6" aria-hidden="true">
              {Array.from({ length: 16 }).map((_, i) => (
                <span key={i} />
              ))}
            </div>
            <p className="text-xs uppercase tracking-wider text-muted mb-4">
              Mode: <span className="text-teal">{recs.mode.replaceAll("_", " ")}</span>
              {" · "}
              {recs.results.length} tickets issued
            </p>
            <div className="grid sm:grid-cols-2 gap-x-6 gap-y-10">
              {recs.results.map((rec, i) => (
                <TicketCard key={rec.movie_id} rec={rec} rank={i + 1} />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
