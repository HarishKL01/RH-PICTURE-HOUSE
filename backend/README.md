# Movie Recommendation API — Backend

FastAPI service serving a hybrid (collaborative filtering + content-based)
movie recommender trained on MovieLens 100K.

## Run locally

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs (Swagger UI).

## Endpoints

| Method | Path                       | Description                                  |
|--------|----------------------------|-----------------------------------------------|
| GET    | `/health`                  | Liveness check                                |
| GET    | `/movies?limit=&offset=`   | Paginated movie list                          |
| GET    | `/movies/search?q=`        | Title search                                  |
| GET    | `/users?limit=`            | Sample of known user IDs (for demo purposes)  |
| GET    | `/users/{user_id}/ratings` | A user's rating history                       |
| POST   | `/recommend`                | Get recommendations (see below)               |

### `POST /recommend`

```json
{
  "user_id": 196,          // optional — known MovieLens user
  "liked_movie_ids": [1],  // optional — for cold-start users
  "top_n": 10
}
```

Response includes a `mode` field (`known_user`, `cold_start_with_preferences`,
or `cold_start_no_signal`) and per-item `strategy` + `reason` fields explaining
why each movie was recommended.

## Deploying on Render (free tier)

1. Push this repo to GitHub.
2. On [render.com](https://render.com), click **New → Web Service**, connect
   the repo.
3. Render will detect `render.yaml` at the repo root automatically. If not,
   set manually:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Deploy. First build takes a few minutes (compiles `scikit-surprise`).
5. Note the deployed URL — the frontend's `.env` needs it as `VITE_API_URL`.

## Deploying on Railway

1. Push to GitHub, create a new Railway project from the repo.
2. In service settings, set **Root Directory** to `backend`.
3. Railway auto-detects the `Procfile`. No extra config needed.
4. Add a public domain from the service's Networking tab.

## Notes

- The model (SVD + TF-IDF) is fit in-memory at process startup from the
  bundled CSV data — no separate training step or database required.
- Cold start takes a few seconds on first request after a deploy/restart
  (model fitting), then responses are fast.
