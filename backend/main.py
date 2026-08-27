"""
FastAPI backend for the hybrid movie recommendation system.

Run with: uvicorn main:app --reload --port 8000
"""
from functools import lru_cache
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from hybrid import HybridRecommender
from data_loader import load_movies

app = FastAPI(title="Movie Recommendation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # relax for demo/eval purposes
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache(maxsize=1)
def get_engine() -> HybridRecommender:
    # Model fitting takes a couple seconds; cache it as a singleton so
    # it only happens once per process, not per request.
    return HybridRecommender()


class RecommendRequest(BaseModel):
    user_id: Optional[int] = None
    liked_movie_ids: Optional[list[int]] = None
    top_n: int = 10


@app.get("/")
def root():
    return {
        "service": "Movie Recommendation API",
        "endpoints": ["/movies", "/movies/search", "/users/{user_id}/ratings", "/recommend"],
    }


@app.get("/movies")
def list_movies(limit: int = Query(50, le=500), offset: int = 0):
    movies = get_engine().movies
    subset = movies.iloc[offset : offset + limit]
    return {
        "total": len(movies),
        "movies": [
            {
                "movie_id": int(r.movie_id),
                "title": r.title,
                "genres": r.genres,
                "year": None if r.year != r.year else int(r.year),
            }
            for r in subset.itertuples()
        ],
    }


@app.get("/movies/search")
def search_movies(q: str = Query(..., min_length=1), limit: int = 20):
    movies = get_engine().movies
    matches = movies[movies["title"].str.contains(q, case=False, na=False)]
    return {
        "results": [
            {"movie_id": int(r.movie_id), "title": r.title, "genres": r.genres}
            for r in matches.head(limit).itertuples()
        ]
    }


@app.get("/genres")
def list_genres():
    return {"genres": get_engine().list_genres()}


@app.get("/recommend/genre")
def recommend_by_genre(
    genre: str,
    top_n: int = Query(10, le=50),
    min_ratings: int = Query(20, ge=0),
):
    engine = get_engine()
    if genre not in engine.list_genres():
        raise HTTPException(status_code=400, detail=f"Unknown genre: {genre}")
    return {
        "mode": "genre",
        "genre": genre,
        "results": engine.recommend_by_genre(genre, top_n=top_n, min_ratings=min_ratings),
    }


@app.get("/recommend/top-rated")
def recommend_top_rated(
    top_n: int = Query(10, le=50),
    min_ratings: int = Query(50, ge=0),
):
    engine = get_engine()
    return {
        "mode": "top_rated",
        "results": engine.recommend_top_rated(top_n=top_n, min_ratings=min_ratings),
    }


@app.get("/users")
def list_known_users(limit: int = 50):
    """A handful of real user IDs from the dataset, for demoing the
    'known user' recommendation path without requiring sign-up."""
    engine = get_engine()
    ids = sorted(engine.cf.known_users)[:limit]
    counts = engine.ratings["user_id"].value_counts()
    return {
        "users": [
            {"user_id": int(uid), "num_ratings": int(counts.get(uid, 0))}
            for uid in ids
        ]
    }


@app.get("/users/{user_id}/ratings")
def user_ratings(user_id: int, limit: int = 20):
    engine = get_engine()
    rated = engine.ratings[engine.ratings["user_id"] == user_id].sort_values(
        "rating", ascending=False
    )
    if rated.empty:
        raise HTTPException(status_code=404, detail="Unknown user_id")
    merged = rated.merge(engine.movies[["movie_id", "title"]], on="movie_id")
    return {
        "user_id": user_id,
        "ratings": [
            {"movie_id": int(r.movie_id), "title": r.title, "rating": int(r.rating)}
            for r in merged.head(limit).itertuples()
        ],
    }


@app.post("/recommend")
def recommend(req: RecommendRequest):
    engine = get_engine()
    if req.user_id is not None and req.user_id not in engine.cf.known_users:
        # Not an error -- just tells the caller we'll treat them as cold-start
        pass
    try:
        return engine.recommend(
            user_id=req.user_id,
            liked_movie_ids=req.liked_movie_ids,
            top_n=req.top_n,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
