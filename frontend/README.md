# Aegis Flow – React Frontend

React (Vite + Tailwind) UI for the Aegis Flow patient location dashboard. Talks to the FastAPI backend for patients, tracked people, enrollment, and video feed.

## Run

```bash
npm install
npm run dev
```

Open http://localhost:5173. Ensure the backend is running:

```bash
uvicorn aegis_flow.api:app --reload --port 8000
```

(from the repo root, with `aegis_flow` dependencies installed)

## Structure

- `src/App.jsx` – main layout, API vs mock data toggle
- `src/components/` – StatsBar, FloorMap, PatientList, CriticalAlert, Sidebar, VideoFeed
- `src/hooks/useAegisData.js` – polling and API calls
- `src/api/client.js` – fetch wrappers for `http://localhost:8000/api`
- `src/data/mockData.js` – fallback when backend is offline

## Scripts

- `npm run dev` – dev server (Vite)
- `npm run build` – production build
- `npm run preview` – preview production build
