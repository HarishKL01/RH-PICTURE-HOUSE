"""
Hybrid recommender.

Strategy:
- Known user (has rating history) -> primarily collaborative filtering,
  re-ranked with a small content-based boost so results aren't purely
  popularity-driven.
- Cold-start user (no ratings, but has told us a few movies they like)
  -> pure content-based, since CF has no signal for them at all.
- Cold-start user with nothing at all -> popularity fallback (most-rated,
  highest-average movies). This is the documented "hardest" failure case.

Each recommendation carries a `reason` and `strategy` field so the API/
UI can show *why* something was recommended -- required by the
assignment brief.
"""
import pandas as pd
from data_loader import load_movies, load_ratings, rating_stats
from content_based import ContentBasedRecommender
from collaborative import CollaborativeRecommender


class HybridRecommender:
    def __init__(self):
        self.movies = load_movies()
        self.ratings = load_ratings()
        self.movies_by_id = self.movies.set_index("movie_id")
        self.stats = rating_stats(self.ratings).set_index("movie_id")

        self.cb = ContentBasedRecommender(self.movies)
        self.cf = CollaborativeRecommender(self.ratings).fit()

    def _popularity_fallback(
        self, top_n: int, min_ratings: int = 50, cold_start: bool = False
    ) -> list[dict]:
        pop = self.stats[self.stats["rating_count"] >= min_ratings].copy()
        pop = pop.sort_values(["rating_mean", "rating_count"], ascending=False)
        results = []
        for mid, row in pop.head(top_n).iterrows():
            reason = (
                f"Highly rated overall ({row['rating_mean']:.1f}/5 avg "
                f"across {int(row['rating_count'])} ratings)"
            )
            if cold_start:
                reason += " -- shown because we don't have enough signal about you yet."
            else:
                reason += "."
            results.append(
                {
                    "movie_id": int(mid),
                    "score": float(row["rating_mean"]),
                    "strategy": "popularity",
                    "reason": reason,
                }
            )
        return results

    def list_genres(self) -> list[str]:
        from data_loader import GENRE_COLS
        return [g for g in GENRE_COLS if g != "unknown"]

    def recommend_by_genre(
        self, genre: str, top_n: int = 10, min_ratings: int = 20
    ) -> list[dict]:
        """
        Browse the highest-rated movies within a single genre. Pure
        content-metadata + popularity, no rating-history needed -- this
        is a deliberately simple, transparent strategy: the 'reason' is
        just the genre match plus the aggregate rating, nothing hidden.
        """
        in_genre = self.movies[
            self.movies["genres"].apply(lambda gs: genre in gs)
        ]
        merged = in_genre.join(self.stats, on="movie_id")
        merged = merged[merged["rating_count"].fillna(0) >= min_ratings]
        merged = merged.sort_values(
            ["rating_mean", "rating_count"], ascending=False
        )

        results = []
        for _, row in merged.head(top_n).iterrows():
            results.append(
                {
                    "movie_id": int(row["movie_id"]),
                    "score": float(row["rating_mean"]),
                    "strategy": "genre_popularity",
                    "reason": (
                        f"Top-rated {genre} title -- {row['rating_mean']:.1f}/5 "
                        f"average across {int(row['rating_count'])} ratings."
                    ),
                }
            )
        return self._attach_titles(results)

    def recommend_top_rated(
        self, top_n: int = 10, min_ratings: int = 50
    ) -> list[dict]:
        """Public wrapper around the popularity fallback, exposed as its
        own browsable mode rather than only a cold-start fallback."""
        return self._attach_titles(
            self._popularity_fallback(top_n, min_ratings=min_ratings)
        )

    def recommend(
        self,
        user_id: int | None = None,
        liked_movie_ids: list[int] | None = None,
        top_n: int = 10,
    ) -> dict:
        liked_movie_ids = liked_movie_ids or []

        # Case 1: known user in the CF training data -> CF-led, content-boosted
        if user_id is not None and self.cf.is_known_user(user_id):
            cf_results = self.cf.recommend_for_user(user_id, top_n=top_n * 3)
            liked_high = self.ratings[
                (self.ratings["user_id"] == user_id) & (self.ratings["rating"] >= 4)
            ]["movie_id"].tolist()

            reranked = []
            for r in cf_results:
                boost = 0.0
                if liked_high:
                    sims = self.cb.similar_to(r["movie_id"], top_n=len(self.movies))
                    sim_map = {s["movie_id"]: s["score"] for s in sims}
                    boost = max(
                        (sim_map.get(m, 0.0) for m in liked_high), default=0.0
                    ) * 0.3
                reranked.append(
                    {
                        "movie_id": r["movie_id"],
                        "score": r["score"] + boost,
                        "strategy": "collaborative_filtering",
                        "reason": (
                            f"Predicted rating {r['score']:.1f}/5 based on patterns "
                            f"from users with similar taste to you."
                        ),
                    }
                )
            reranked.sort(key=lambda x: -x["score"])
            return {
                "mode": "known_user",
                "results": self._attach_titles(reranked[:top_n]),
            }

        # Case 2: cold-start but user told us what they like -> content-based
        if liked_movie_ids:
            cb_results = self.cb.recommend_for_profile(liked_movie_ids, top_n=top_n)
            liked_titles = [
                self.movies_by_id.loc[m, "title"]
                for m in liked_movie_ids
                if m in self.movies_by_id.index
            ]
            for r in cb_results:
                r["strategy"] = "content_based"
                r["reason"] = (
                    f"Similar genre/style to movies you liked "
                    f"({', '.join(liked_titles[:2])})."
                )
            return {
                "mode": "cold_start_with_preferences",
                "results": self._attach_titles(cb_results),
            }

        # Case 3: total cold start -> popularity fallback
        return {
            "mode": "cold_start_no_signal",
            "results": self._attach_titles(
                self._popularity_fallback(top_n, cold_start=True)
            ),
        }

    def _attach_titles(self, results: list[dict]) -> list[dict]:
        for r in results:
            row = self.movies_by_id.loc[r["movie_id"]]
            r["title"] = row["title"]
            r["genres"] = row["genres"]
            r["year"] = None if pd.isna(row["year"]) else int(row["year"])
        return results


if __name__ == "__main__":
    hybrid = HybridRecommender()

    print("=== Known user (id=196) ===")
    out = hybrid.recommend(user_id=196, top_n=5)
    print("mode:", out["mode"])
    for r in out["results"]:
        print(f"  {r['title']:40s} [{r['strategy']}] {r['reason']}")

    print("\n=== Cold-start with stated preference (likes Toy Story) ===")
    toy_story_id = int(
        hybrid.movies[hybrid.movies["title"].str.contains("Toy Story")]["movie_id"].iloc[0]
    )
    out = hybrid.recommend(liked_movie_ids=[toy_story_id], top_n=5)
    print("mode:", out["mode"])
    for r in out["results"]:
        print(f"  {r['title']:40s} [{r['strategy']}]")

    print("\n=== Total cold start (new user, no data at all) ===")
    out = hybrid.recommend(top_n=5)
    print("mode:", out["mode"])
    for r in out["results"]:
        print(f"  {r['title']:40s} [{r['strategy']}]")
