# Frontend

Static map frontend for exploring the latest notebook outputs and a shared 250 m custom index.

## Build the frontend data

Run this from the repo root:

```bash
./.venv/bin/python frontend/scripts/build_frontend_data.py
```

## Serve the app

From the repo root:

```bash
python3 -m http.server 8000
```

Then open:

`http://127.0.0.1:8000/frontend/`

Notes:

- The app expects the repo root to be the HTTP server root so it can read `notebooks/...` assets.
- The map UI uses CDN-hosted Leaflet assets and online OSM tiles.
- `frontend/data/index_grid_250m.geojson` is generated and intentionally ignored by git.
