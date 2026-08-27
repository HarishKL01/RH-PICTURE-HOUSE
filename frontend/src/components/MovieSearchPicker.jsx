import { useEffect, useState } from "react";
import { searchMovies } from "../api";

export default function MovieSearchPicker({ liked, onChange }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    const handle = setTimeout(() => {
      if (!query.trim()) {
        setResults([]);
        return;
      }
      setSearching(true);
      searchMovies(query)
        .then((data) => setResults(data.results))
        .finally(() => setSearching(false));
    }, 300);
    return () => clearTimeout(handle);
  }, [query]);

  function addMovie(movie) {
    if (liked.some((m) => m.movie_id === movie.movie_id)) return;
    onChange([...liked, movie]);
    setQuery("");
    setResults([]);
  }

  function removeMovie(movieId) {
    onChange(liked.filter((m) => m.movie_id !== movieId));
  }

  return (
    <div className="bg-surface rounded-xl p-5 border border-white/5">
      <label htmlFor="movie-search" className="block text-xs uppercase tracking-wider text-muted mb-2">
        Search for movies you like
      </label>
      <input
        id="movie-search"
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Try “Star Wars”, “Toy Story”, “Godfather”…"
        className="w-full bg-surface-raised border border-white/10 rounded-lg px-3 py-2.5 text-paper placeholder:text-muted/60 text-sm focus:border-amber outline-none"
      />

      {searching && <p className="text-xs text-muted mt-2">Searching the reel archive…</p>}

      {results.length > 0 && (
        <ul className="mt-2 border border-white/10 rounded-lg overflow-hidden divide-y divide-white/5">
          {results.map((m) => (
            <li key={m.movie_id}>
              <button
                onClick={() => addMovie(m)}
                className="w-full text-left px-3 py-2 text-sm hover:bg-surface-raised transition-colors cursor-pointer flex justify-between gap-2"
              >
                <span className="truncate">{m.title}</span>
                <span className="text-muted text-xs shrink-0 self-center">
                  {m.genres?.slice(0, 2).join(", ")}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      {liked.length > 0 && (
        <div className="mt-4">
          <p className="text-xs uppercase tracking-wider text-muted mb-2">
            Your picks ({liked.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {liked.map((m) => (
              <span
                key={m.movie_id}
                className="inline-flex items-center gap-1.5 bg-surface-raised border border-amber/30 text-amber text-xs rounded-full pl-3 pr-1.5 py-1"
              >
                {m.title}
                <button
                  onClick={() => removeMovie(m.movie_id)}
                  aria-label={`Remove ${m.title}`}
                  className="w-4 h-4 rounded-full hover:bg-amber/20 flex items-center justify-center cursor-pointer"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
