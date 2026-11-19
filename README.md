# Forsyth Connect

A bilingual (English/Spanish) directory of 102 community resources in Forsyth County, Georgia. Built for the Congressional App Challenge.

**Live demo:** https://forsyth-connect.onrender.com (free hosting, so the first load can take up to a minute while it wakes up)

People looking for help with food, health care, housing, transportation, or a crisis often don't know what exists near them. Forsyth Connect puts the county's resources in one place, sorts them by distance, and tells you whether a place is likely open right now.

## Features

- **102 resources** across food, health, housing, family, youth, senior, transportation, education, and crisis categories
- **English and Spanish** for every listing and the whole interface
- **Distance sorting** using your location, which never leaves your browser
- **Open / closed / call first labels**: if a listing's hours are too vague to read, it says "call first" instead of guessing
- **Built-in assistant** that searches the directory and opens matching listings. It runs locally with no external AI API.
- **Personalized action plan** that suggests resources based on what you need
- **Accessibility controls** for text size and contrast
- **Community corrections**: anyone can report outdated info, and reports are saved on the server
- **Works offline**: if the backend is down, the page falls back to an embedded copy of all 102 resources
- No account, no tracking

## Run it locally

You only need Python 3.9 or newer. There's nothing to install.

```bash
git clone https://github.com/ucanmailabeersharma-sketch/forsyth-connect.git
cd forsyth-connect
python3 backend/server.py
```

Then open http://127.0.0.1:8000.

On a Mac you can also double-click `START_FORSYTH_CONNECT.command`.

Options:

```bash
python3 backend/server.py --host 0.0.0.0 --port 8000 --workers 128
```

## Run with Docker

```bash
docker build -t forsyth-connect .
docker run -p 8000:8000 -v forsyth-data:/data forsyth-connect
```

## API

| Endpoint | What it does |
|---|---|
| `GET /api/health` | Health check |
| `GET /api/resources?category=&q=&lang=en` | Resource list, with optional category filter, search, and language (`en` or `es`) |
| `POST /api/feedback` | Submit a correction: `{"resourceName": "...", "message": "...", "contact": "optional email"}` |

## How it's built

- **Frontend:** a single HTML/CSS/JS file (`frontend/index.html`), with no framework
- **Backend:** Python standard library only (`backend/server.py`). It uses a thread-pool HTTP server and stores feedback in SQLite with WAL mode, so concurrent writes are safe.
- **Data:** `data/resources.json` is the source of truth for all listings

```
backend/server.py      API + serves the frontend
frontend/index.html    the whole web app
data/resources.json    resource directory (EN + ES)
Dockerfile             container deploy (reads $PORT, stores data in /data)
```

## Deploying

The Dockerfile works on Railway, Render, Fly.io, or any host that runs containers. It listens on the host's `PORT` variable. Mount a persistent volume at `/data` so community feedback isn't lost when you redeploy, and set the health check path to `/api/health`.

## Updating resources

Edit `data/resources.json`. The server picks up changes automatically, so you don't need to restart it.
