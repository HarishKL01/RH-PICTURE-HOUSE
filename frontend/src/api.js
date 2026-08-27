const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`API error ${res.status}: ${detail}`);
  }
  return res.json();
}

export function listGenres() {
  return request("/genres");
}

export function recommendByGenre(genre, topN = 10) {
  return request(`/recommend/genre?genre=${encodeURIComponent(genre)}&top_n=${topN}`);
}

export function recommendTopRated(topN = 10, minRatings = 50) {
  return request(`/recommend/top-rated?top_n=${topN}&min_ratings=${minRatings}`);
}

export function searchMovies(query, limit = 12) {
  if (!query.trim()) return Promise.resolve({ results: [] });
  return request(`/movies/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

export function getRecommendations({ likedMovieIds, topN = 10 }) {
  return request("/recommend", {
    method: "POST",
    body: JSON.stringify({
      user_id: null,
      liked_movie_ids: likedMovieIds ?? null,
      top_n: topN,
    }),
  });
}

export { API_URL };
