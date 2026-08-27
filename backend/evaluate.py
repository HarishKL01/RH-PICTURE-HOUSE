"""
Offline evaluation for the hybrid recommendation system.

Metrics reported (and why each was chosen -- see documentation for the
full justification):

- RMSE / MAE           : rating-prediction accuracy of the CF component.
- Precision@K, Recall@K: how many of the top-K recommendations for a
                         user turn out to be items they actually rated
                         highly in held-out data.
- Coverage             : fraction of the movie catalog the system is
                         *capable* of recommending at all (guards
                         against a model that only ever suggests the
                         same 20 popular titles).
- Diversity            : average pairwise dissimilarity (1 - genre
                         cosine similarity) within a single user's
                         top-K list -- a model can be accurate but
                         boring (all top picks being near-duplicates).
- Novelty              : average "unpopularity" of recommended items
                         (-log2 of how often they were rated), so we
                         can tell whether the system leans on
                         obvious blockbusters vs. surfacing the
                         long tail.
- Latency              : wall-clock time per recommendation call --
                         matters for the "deployed UI must feel
                         responsive" requirement.

Run with: python3 evaluate.py
"""
import time
import math
from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split as sk_split

from data_loader import load_ratings, load_movies, rating_stats
from content_based import ContentBasedRecommender
from collaborative import CollaborativeRecommender

RELEVANCE_THRESHOLD = 4  # a held-out rating >= 4 counts as "the user liked it"
TOP_K = 10


def precision_recall_at_k(cf: CollaborativeRecommender, test_df: pd.DataFrame, k: int = TOP_K):
    """
    For each user in the test split, take the items they rated >= threshold
    as 'relevant', ask the (already-trained) CF model for its top-K
    predictions restricted to the candidate pool of items that user
    actually rated in the test set, and measure overlap.

    Note: this is evaluated over each user's *test-set* items only
    (the standard approach for offline top-K eval on an explicit-rating
    dataset like MovieLens, where we don't have unrated-item labels).
    """
    precisions, recalls = [], []
    grouped = test_df.groupby("user_id")

    for user_id, group in grouped:
        if not cf.is_known_user(user_id):
            continue
        relevant = set(group[group["rating"] >= RELEVANCE_THRESHOLD]["movie_id"])
        if not relevant:
            continue

        candidates = group["movie_id"].tolist()
        preds = [(mid, cf.predict_score(user_id, mid)) for mid in candidates]
        preds.sort(key=lambda x: -x[1])
        top_k_items = {mid for mid, _ in preds[:k]}

        hits = len(top_k_items & relevant)
        precisions.append(hits / min(k, len(top_k_items)) if top_k_items else 0.0)
        recalls.append(hits / len(relevant))

    return {
        "precision_at_k": float(np.mean(precisions)) if precisions else 0.0,
        "recall_at_k": float(np.mean(recalls)) if recalls else 0.0,
        "num_users_evaluated": len(precisions),
    }


def coverage(cf: CollaborativeRecommender, cb: ContentBasedRecommender, sample_users, movies_df, k: int = TOP_K):
    """Fraction of the catalog that appears in at least one sampled
    user's top-K list."""
    recommended = set()
    for uid in sample_users:
        if cf.is_known_user(uid):
            for r in cf.recommend_for_user(uid, top_n=k):
                recommended.add(r["movie_id"])
    return len(recommended) / len(movies_df)


def diversity(cb: ContentBasedRecommender, item_lists: list[list[int]]) -> float:
    """Average (1 - pairwise genre-similarity) within each recommended
    list, averaged across lists. Higher = more varied recommendations."""
    scores = []
    for items in item_lists:
        if len(items) < 2:
            continue
        idxs = [cb.movie_id_to_idx[m] for m in items if m in cb.movie_id_to_idx]
        if len(idxs) < 2:
            continue
        vecs = cb.feature_matrix[idxs]
        norm = vecs / (np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-9)
        sim_matrix = norm @ norm.T
        n = len(idxs)
        upper_tri_sum = (sim_matrix.sum() - np.trace(sim_matrix)) / 2
        pair_count = n * (n - 1) / 2
        avg_sim = upper_tri_sum / pair_count
        scores.append(1 - avg_sim)
    return float(np.mean(scores)) if scores else 0.0


def novelty(item_lists: list[list[int]], stats: pd.DataFrame, n_users: int) -> float:
    """Average self-information of recommended items: rarely-rated
    items score higher. Standard novelty metric from Vargas & Castells."""
    scores = []
    for items in item_lists:
        for mid in items:
            count = stats.loc[mid, "rating_count"] if mid in stats.index else 1
            popularity = count / n_users
            scores.append(-math.log2(popularity + 1e-9))
    return float(np.mean(scores)) if scores else 0.0


def measure_latency(cf: CollaborativeRecommender, sample_users, k: int = TOP_K) -> dict:
    times = []
    for uid in sample_users:
        if not cf.is_known_user(uid):
            continue
        start = time.perf_counter()
        cf.recommend_for_user(uid, top_n=k)
        times.append(time.perf_counter() - start)
    return {
        "avg_latency_ms": float(np.mean(times) * 1000) if times else None,
        "p95_latency_ms": float(np.percentile(times, 95) * 1000) if times else None,
    }


def run_evaluation():
    print("Loading data and fitting models...")
    ratings = load_ratings()
    movies = load_movies()
    stats = rating_stats(ratings).set_index("movie_id")

    train_df, test_df = sk_split(ratings, test_size=0.2, random_state=42)

    cf = CollaborativeRecommender(train_df).fit()
    cb = ContentBasedRecommender(movies)

    print("\n=== Rating Prediction Accuracy ===")
    rmse_mae = cf.evaluate(test_size=0.2)
    print(f"RMSE: {rmse_mae['rmse']:.4f}")
    print(f"MAE:  {rmse_mae['mae']:.4f}")

    print(f"\n=== Top-{TOP_K} Ranking Quality ===")
    pr = precision_recall_at_k(cf, test_df, k=TOP_K)
    print(f"Precision@{TOP_K}: {pr['precision_at_k']:.4f}")
    print(f"Recall@{TOP_K}:    {pr['recall_at_k']:.4f}")
    print(f"(evaluated over {pr['num_users_evaluated']} users with >=1 relevant held-out item)")

    sample_users = sorted(cf.known_users)[:200]

    print(f"\n=== Coverage ===")
    cov = coverage(cf, cb, sample_users, movies, k=TOP_K)
    print(f"Catalog coverage (top-{TOP_K} over {len(sample_users)} users): {cov:.2%}")

    item_lists = [
        [r["movie_id"] for r in cf.recommend_for_user(uid, top_n=TOP_K)]
        for uid in sample_users if cf.is_known_user(uid)
    ]

    print(f"\n=== Diversity ===")
    div = diversity(cb, item_lists)
    print(f"Avg intra-list diversity: {div:.4f}  (0=identical genres, 1=fully distinct)")

    print(f"\n=== Novelty ===")
    nov = novelty(item_lists, stats, n_users=ratings["user_id"].nunique())
    print(f"Avg novelty (self-information, bits): {nov:.4f}  (higher = less mainstream)")

    print(f"\n=== Latency ===")
    lat = measure_latency(cf, sample_users, k=TOP_K)
    print(f"Avg: {lat['avg_latency_ms']:.2f} ms   P95: {lat['p95_latency_ms']:.2f} ms")

    print("\n=== Summary (for documentation) ===")
    summary = {
        "rmse": round(rmse_mae["rmse"], 4),
        "mae": round(rmse_mae["mae"], 4),
        f"precision_at_{TOP_K}": round(pr["precision_at_k"], 4),
        f"recall_at_{TOP_K}": round(pr["recall_at_k"], 4),
        "coverage": round(cov, 4),
        "diversity": round(div, 4),
        "novelty_bits": round(nov, 4),
        "avg_latency_ms": round(lat["avg_latency_ms"], 2),
        "p95_latency_ms": round(lat["p95_latency_ms"], 2),
    }
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return summary


if __name__ == "__main__":
    run_evaluation()
