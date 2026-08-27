# Now Recommending — Frontend

React + Vite + Tailwind UI for the hybrid movie recommender. Cinema
box-office theme: pick a mode, get recommendations rendered as ticket
stubs, each showing which strategy produced it and why.

## Run locally

```bash
npm install
cp .env.example .env.development   # point at your backend if not localhost:8000
npm run dev
```

Requires the backend (`../backend`) running at the URL in `VITE_API_URL`
(defaults to `http://localhost:8000`).

## Modes

- **Regular Patron** — pick a known MovieLens user ID, get CF-driven
  recommendations re-ranked with a content-based boost.
- **New Here** — search and select a few movies you like; recommendations
  come from content-based similarity (no rating history needed).
- **Surprise Me** — no input at all; falls back to popularity-based picks.
  This is the system's weakest case by design, included to demonstrate
  graceful degradation rather than failure.

## Build & deploy (Vercel)

```bash
npm run build
```

On Vercel: import the repo, set **root directory** to `frontend`, and add
an environment variable `VITE_API_URL` pointing at your deployed backend
URL. Vercel auto-detects the Vite build command and output directory.
