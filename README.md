# Maintenance Wizard — Render Deployment Guide

AI-powered industrial maintenance platform for steel manufacturing plants.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | FastAPI · SQLite · ChromaDB · scikit-learn · XGBoost |
| AI / LLM | Groq LLaMA 3.3 70B |
| Frontend | React 18 · Vite · Tailwind CSS |
| Hosting | Render (backend Web Service + frontend Static Site) |

---

## Deploying to Render — Step by Step

### Step 1 — Push to GitHub

Make sure your project is in a GitHub repository (public or private).

```bash
cd "New folder (3)"
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/maintenance-wizard.git
git push -u origin main
```

> The `.gitignore` already excludes `.env`, `.db`, `node_modules`, `chroma_db`, and `models/`.

---

### Step 2 — Deploy the Backend

1. Go to [https://dashboard.render.com](https://dashboard.render.com) → **New → Web Service**
2. Connect your GitHub repo
3. Fill in:
   - **Name:** `maintenance-wizard-backend`
   - **Root Directory:** `backend`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free (or Starter for always-on)
4. Under **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `GROQ_API_KEY` | your Groq API key |
   | `LLM_PROVIDER` | `groq` |
   | `LLM_MODEL` | `llama-3.3-70b-versatile` |
   | `DATABASE_URL` | `sqlite+aiosqlite:///./maintenance_wizard.db` |
   | `DEBUG` | `false` |
5. Click **Create Web Service**
6. Wait for the build to complete. Copy the URL shown — it will look like:
   `https://maintenance-wizard-backend.onrender.com`

---

### Step 3 — Deploy the Frontend

1. Go to Render → **New → Static Site**
2. Connect the same GitHub repo
3. Fill in:
   - **Name:** `maintenance-wizard-frontend`
   - **Root Directory:** `frontend`
   - **Build Command:** `npm install && npm run build`
   - **Publish Directory:** `dist`
4. Under **Environment Variables**, add:
   | Key | Value |
   |---|---|
   | `VITE_API_URL` | the backend URL from Step 2 e.g. `https://maintenance-wizard-backend.onrender.com` |
5. Under **Redirects/Rewrites**, add:
   - Source: `/*`  →  Destination: `/index.html`  →  Type: `Rewrite`
6. Click **Create Static Site**

---

### Step 4 — Verify

- Backend health check: `https://maintenance-wizard-backend.onrender.com/health`
- Frontend: open your static site URL — it should load and connect to the backend

---

## Environment Variables Reference

### Backend

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Your Groq API key — get one free at console.groq.com |
| `LLM_PROVIDER` | ✅ | `groq` (default) |
| `LLM_MODEL` | optional | `llama-3.3-70b-versatile` (default) |
| `DATABASE_URL` | optional | SQLite URL (default: `sqlite+aiosqlite:///./maintenance_wizard.db`) |
| `DEBUG` | optional | `false` in production |
| `OPENAI_API_KEY` | optional | Only if switching to OpenAI |

### Frontend

| Variable | Required | Description |
|---|---|---|
| `VITE_API_URL` | ✅ | Full URL of the deployed backend (no trailing slash) |

---

## Using `render.yaml` (Blueprint Deploy — optional)

If you want Render to auto-configure both services at once:

1. Push `render.yaml` to your repo root (already done)
2. Go to Render → **New → Blueprint**
3. Connect your repo — Render will detect `render.yaml` and create both services
4. Manually set `GROQ_API_KEY` and `VITE_API_URL` in each service's environment settings after creation

---

## Notes

- **SQLite on Render Free tier:** The database resets on each deploy (ephemeral disk). Use the seed scripts to repopulate, or upgrade to a paid plan with a persistent disk.
- **Startup time:** The Free tier spins down after 15 minutes of inactivity. First request after spin-down takes ~30 seconds.
- **ML models:** Retrain automatically on every startup (handled in `main.py` lifespan).
- **ChromaDB:** Stored in `./chroma_db` relative to the backend working directory. Regenerated on deploy.
