"""
Collaborative filtering recommender using SVD (matrix factorization).

Learns latent factors for users and items purely from the user-item
rating matrix -- no metadata involved. This captures "people who rated
like you also liked..." patterns that content-based similarity can't
see (e.g. two movies in different genres that the same audience loves).

Cold-start limitation: a user/item with zero ratings has no learned
factors, so SVD falls back to the global mean. This is intentional --
it's documented as a known failure mode and handled by blending with
the content-based model in hybrid.py.
"""
import pandas as pd
from surprise import Dataset, Reader, SVD
from surprise.model_selection import train_test_split
from surprise import accuracy

from data_loader import load_ratings


class CollaborativeRecommender:
    def __init__(self, ratings: pd.DataFrame = None, n_factors: int = 50, random_state: int = 42):
        self.ratings = ratings if ratings is not None else load_ratings()
        self.n_factors = n_factors
        self.random_state = random_state
        self.model = None
        self.known_users = set()
        self.known_items = set()

    def fit(self):
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(
            self.ratings[["user_id", "movie_id", "rating"]], reader
        )
        trainset = data.build_full_trainset()
        self.model = SVD(n_factors=self.n_factors, random_state=self.random_state)
        self.model.fit(trainset)
        self.known_users = set(self.ratings["user_id"].unique())
        self.known_items = set(self.ratings["movie_id"].unique())
        return self

    def evaluate(self, test_size: float = 0.2) -> dict:
        """Held-out RMSE/MAE -- reported in documentation as the offline
        accuracy metric for the CF component."""
        reader = Reader(rating_scale=(1, 5))
        data = Dataset.load_from_df(
            self.ratings[["user_id", "movie_id", "rating"]], reader
        )
        trainset, testset = train_test_split(
            data, test_size=test_size, random_state=self.random_state
        )
        model = SVD(n_factors=self.n_factors, random_state=self.random_state)
        model.fit(trainset)
        preds = model.test(testset)
        return {
            "rmse": accuracy.rmse(preds, verbose=False),
            "mae": accuracy.mae(preds, verbose=False),
        }

    def is_known_user(self, user_id: int) -> bool:
        return user_id in self.known_users

    def predict_score(self, user_id: int, movie_id: int) -> float:
        return self.model.predict(user_id, movie_id).est

    def recommend_for_user(
        self, user_id: int, top_n: int = 10, exclude_rated: bool = True
    ) -> list[dict]:
        if self.model is None:
            raise RuntimeError("Call fit() first")
        rated = set()
        if exclude_rated:
            rated = set(
                self.ratings[self.ratings["user_id"] == user_id]["movie_id"]
            )
        all_items = self.known_items
        candidates = [m for m in all_items if m not in rated]
        preds = [
            (m, self.model.predict(user_id, m).est) for m in candidates
        ]
        preds.sort(key=lambda x: -x[1])
        return [
            {"movie_id": int(m), "score": float(s)} for m, s in preds[:top_n]
        ]


if __name__ == "__main__":
    cf = CollaborativeRecommender().fit()
    metrics = cf.evaluate()
    print(f"Held-out RMSE: {metrics['rmse']:.4f}  MAE: {metrics['mae']:.4f}")

    from data_loader import load_movies
    movies = load_movies().set_index("movie_id")
    uid = 196
    print(f"\nTop picks for user {uid} (known user, {len(cf.ratings[cf.ratings.user_id==uid])} ratings):")
    for r in cf.recommend_for_user(uid, top_n=5):
        print(f"  {movies.loc[r['movie_id'], 'title']:40s} predicted={r['score']:.2f}")
