
import os
import re
import urllib.request
import zipfile
from pathlib import Path

import pandas as pd
import numpy as np

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# "ml-latest-small" (~100K ratings, updated periodically, recommended by
# GroupLens for dev/education) or "ml-latest" (full dataset, continuously
# updated, currently tens of millions of ratings -- large).
DATASET_NAME = os.environ.get("MOVIELENS_DATASET", "ml-latest-small")
DATASET_URL = f"https://files.grouplens.org/datasets/movielens/{DATASET_NAME}.zip"
DATASET_DIR = DATA_DIR / DATASET_NAME

# Genres as they appear in movies.csv's pipe-separated "genres" column,
# minus the "(no genres listed)" sentinel (handled separately below).
GENRE_COLS = [
    "Action", "Adventure", "Animation", "Children", "Comedy", "Crime",
    "Documentary", "Drama", "Fantasy", "Film-Noir", "Horror", "IMAX",
    "Musical", "Mystery", "Romance", "Sci-Fi", "Thriller", "War", "Western",
]

NO_GENRES = "(no genres listed)"


def _ensure_dataset() -> None:
    """Download and extract the dataset zip into DATA_DIR on first use.

    Idempotent: if movies.csv already exists locally, does nothing.
    """
    movies_csv = DATASET_DIR / "movies.csv"
    if movies_csv.exists():
        return

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = DATA_DIR / f"{DATASET_NAME}.zip"

    try:
        print(f"Downloading {DATASET_NAME} from {DATASET_URL} ...")
        urllib.request.urlretrieve(DATASET_URL, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(DATA_DIR)
    except Exception as e:
        raise RuntimeError(
            f"Failed to download/extract MovieLens dataset '{DATASET_NAME}' "
            f"from {DATASET_URL}. Check network access, or manually download "
            f"the zip and extract it to {DATASET_DIR}."
        ) from e
    finally:
        if zip_path.exists():
            zip_path.unlink()

    if not movies_csv.exists():
        raise RuntimeError(
            f"Extracted {DATASET_NAME} but movies.csv was not found under "
            f"{DATASET_DIR}. The archive layout may have changed."
        )


def load_movies() -> pd.DataFrame:
    _ensure_dataset()
    df = pd.read_csv(DATASET_DIR / "movies.csv")
    df = df.rename(columns={"movieId": "movie_id"})

    # Clean year out of title, e.g. "Toy Story (1995)" -> year=1995
    df["year"] = df["title"].str.extract(r"\((\d{4})\)").astype("float")

    # genres.csv packs genres as "Action|Adventure|Sci-Fi" (or the
    # "(no genres listed)" sentinel for unclassified titles).
    df["genres"] = df["genres"].apply(
        lambda s: [] if s == NO_GENRES else s.split("|")
    )
    df["genres_str"] = df["genres"].apply(lambda gs: " ".join(gs))

    # Rebuild one-hot genre columns for the downstream feature matrix
    # (content_based.py indexes self.movies[GENRE_COLS] directly).
    genre_sets = df["genres"].apply(set)
    for g in GENRE_COLS:
        df[g] = genre_sets.apply(lambda gs, g=g: int(g in gs))

    return df


def load_ratings() -> pd.DataFrame:
    _ensure_dataset()
    df = pd.read_csv(DATASET_DIR / "ratings.csv")
    df = df.rename(columns={"userId": "user_id", "movieId": "movie_id"})
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    return df


def load_users() -> pd.DataFrame:
    """No demographic data (age/sex/occupation/zip) ships with the
    ml-latest(-small) datasets -- unlike the old 100K release, users are
    anonymous ids only. Returns the distinct user ids seen in ratings.csv
    for callers that just need the known-user set."""
    ratings = load_ratings()
    return pd.DataFrame({"user_id": sorted(ratings["user_id"].unique())})


def rating_stats(ratings: pd.DataFrame) -> pd.DataFrame:
    """Per-movie rating count and average, used for popularity fallback."""
    stats = ratings.groupby("movie_id")["rating"].agg(["count", "mean"]).reset_index()
    stats.columns = ["movie_id", "rating_count", "rating_mean"]
    return stats


if __name__ == "__main__":
    print(f"Dataset: {DATASET_NAME} ({DATASET_URL})")
    movies = load_movies()
    ratings = load_ratings()
    users = load_users()
    print(f"Movies: {len(movies)}  Ratings: {len(ratings)}  Users: {len(users)}")
    print(movies[["movie_id", "title", "year", "genres_str"]].head())