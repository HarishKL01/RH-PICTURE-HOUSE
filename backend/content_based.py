"""
Content-based recommender.

Builds a feature vector per movie from its genres (weighted heavily) and
title tokens, then recommends movies most similar to ones a user has
rated highly. This is the fallback path for cold-start users who have
no rating history yet -- it only needs item metadata.
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from data_loader import load_movies, GENRE_COLS


class ContentBasedRecommender:
    def __init__(self, movies: pd.DataFrame = None):
        self.movies = movies if movies is not None else load_movies()
        self._build_features()

    def _build_features(self):
        # Genre one-hot block (excluding the 'unknown' bucket)
        genre_cols = [g for g in GENRE_COLS if g != "unknown"]
        genre_matrix = self.movies[genre_cols].values.astype(float)

        # Title text as a light secondary signal (helps sequels/series cluster)
        tfidf = TfidfVectorizer(stop_words="english", max_features=500)
        title_matrix = tfidf.fit_transform(self.movies["title"]).toarray()

        # Weight genres much more heavily than title text -- genre is the
        # actual semantic signal here, title similarity is a weak proxy.
        genre_weight, title_weight = 3.0, 0.3
        self.feature_matrix = np.hstack(
            [genre_matrix * genre_weight, title_matrix * title_weight]
        )
        self.movie_id_to_idx = {
            mid: i for i, mid in enumerate(self.movies["movie_id"])
        }
        self.idx_to_movie_id = {i: mid for mid, i in self.movie_id_to_idx.items()}

    def similar_to(self, movie_id: int, top_n: int = 10) -> list[dict]:
        """Movies most similar to a single given movie."""
        if movie_id not in self.movie_id_to_idx:
            return []
        idx = self.movie_id_to_idx[movie_id]
        sims = cosine_similarity(
            self.feature_matrix[idx : idx + 1], self.feature_matrix
        )[0]
        order = np.argsort(-sims)
        results = []
        for i in order:
            mid = self.idx_to_movie_id[i]
            if mid == movie_id:
                continue
            results.append({"movie_id": int(mid), "score": float(sims[i])})
            if len(results) >= top_n:
                break
        return results

    def recommend_for_profile(
        self, liked_movie_ids: list[int], top_n: int = 10
    ) -> list[dict]:
        """
        Cold-start / profile-based recommendation: average the feature
        vectors of movies the user says they like, then rank all other
        movies by similarity to that centroid.
        """
        idxs = [
            self.movie_id_to_idx[m] for m in liked_movie_ids if m in self.movie_id_to_idx
        ]
        if not idxs:
            return []
        centroid = self.feature_matrix[idxs].mean(axis=0, keepdims=True)
        sims = cosine_similarity(centroid, self.feature_matrix)[0]
        order = np.argsort(-sims)
        results = []
        liked_set = set(liked_movie_ids)
        for i in order:
            mid = self.idx_to_movie_id[i]
            if mid in liked_set:
                continue
            results.append({"movie_id": int(mid), "score": float(sims[i])})
            if len(results) >= top_n:
                break
        return results


if __name__ == "__main__":
    cb = ContentBasedRecommender()
    movies = cb.movies.set_index("movie_id")
    toy_story_id = movies[movies["title"].str.contains("Toy Story")].index[0]
    print(f"Similar to: {movies.loc[toy_story_id, 'title']}")
    for r in cb.similar_to(toy_story_id, top_n=5):
        print(f"  {movies.loc[r['movie_id'], 'title']:40s} score={r['score']:.3f}")
