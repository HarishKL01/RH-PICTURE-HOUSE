import { useEffect, useState } from "react";
import { listGenres } from "../api";

export default function GenrePicker({ genre, onSelect }) {
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    listGenres()
      .then((data) => setGenres(data.genres))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="bg-surface rounded-xl p-5 border border-white/5">
      <p className="text-xs uppercase tracking-wider text-muted mb-3">
        Pick a genre to browse
      </p>
      {error && <p className="text-sm text-danger mb-2">Couldn't load genres: {error}</p>}
      {loading ? (
        <p className="text-sm text-muted">Loading genres…</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {genres.map((g) => {
            const active = genre === g;
            return (
              <button
                key={g}
                onClick={() => onSelect(g)}
                aria-pressed={active}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors cursor-pointer border ${
                  active
                    ? "bg-amber text-ink border-amber"
                    : "bg-surface-raised text-paper/80 border-white/10 hover:border-amber/50"
                }`}
              >
                {g}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
