# RH PICTURE HOUSE - Now Recommending
A full-stack movie recommender combining **collaborative filtering** (SVD)
and **content-based filtering** (genre + title TF-IDF), served by a FastAPI
backend and a React/Vite frontend styled like a cinema box office.

Every recommendation comes with a `strategy` and `reason` field explaining
*why* it was suggested — collaborative filtering for known users,
content-based similarity for cold-start users who've told us what they
like, or a popularity fallback for total cold start.

## Project structure

```
recommendation-system/
├── backend/          FastAPI service (recommendation engine + API)
├── frontend/          React + Vite + Tailwind UI
├── data/              MovieLens dataset (auto-downloaded, not committed)
└── render.yaml         Render.com deployment config for the backend
```

## Dataset

The backend trains on the current [MovieLens](https://grouplens.org/datasets/movielens/)
dataset — `ml-latest-small` by default. It is **downloaded and cached
automatically** the first time the backend runs; there's no dataset to
download or commit manually.

To use the full, larger `ml-latest` release instead of the small one, set:

```bash
export MOVIELENS_DATASET=ml-latest
```

Note: `ml-latest(-small)` includes only anonymous user ids — no
demographic data (age/sex/occupation), unlike the older MovieLens 100K/1M
releases.

## Quickstart

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The first request after a fresh clone will pause briefly while the
dataset downloads and the models fit; subsequent requests are fast.

API docs: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install
cp .env.example .env.development   # point VITE_API_URL at the backend if not localhost:8000
npm run dev
```

## How recommendations work

Three browsable recommendation modes, each built on a different signal:

| Mode                          | Endpoint                | Signal used                          | How it ranks results                                          |
|--------------------------------|--------------------------|----------------------------------------|-----------------------------------------------------------------|
| **Top Rated**                  | `/recommend/top-rated`   | Aggregate rating across all users     | Highest-average, most-rated movies overall (popularity)         |
| **By Genre**                   | `/recommend/genre`       | Genre + aggregate rating              | Highest-rated movies within the chosen genre                    |
| **Favorites** (cold-start)     | `/recommend` (with `liked_movie_ids`) | A user's stated favorite movies | Content-based similarity — genre/title match to those favorites |

On top of these, `/recommend` with a known `user_id` also runs
**collaborative filtering** (SVD) over the full ratings matrix, re-ranked
with a content-based boost from that user's own highly-rated movies. This
is the path used once someone has enough rating history for CF to have
signal — Top Rated, By Genre, and Favorites all cover the cases where it
doesn't (browsing, or a brand-new user).

See `backend/hybrid.py` for the full logic and `backend/evaluate.py` for
offline evaluation (RMSE/MAE, Precision@K/Recall@K, coverage, diversity,
novelty, latency).

## Deployment

- **Backend:** `render.yaml` is set up for [Render](https://render.com)
  (free tier). Railway also works via the included `Procfile`. See
  `backend/README.md` for details.
- **Frontend:** deploys cleanly to [Vercel](https://vercel.com) — set root
  directory to `frontend` and add a `VITE_API_URL` env var pointing at the
  deployed backend. See `frontend/README.md` for details.

## Tech stack

- **Backend:** FastAPI, pandas, scikit-learn, scikit-surprise (SVD)
- **Frontend:** React, Vite, Tailwind CSS
- **Data:** MovieLens (`ml-latest-small` / `ml-latest`)



- 
