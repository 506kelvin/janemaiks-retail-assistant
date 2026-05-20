# JaneMaiks Retail Assistant — Deployment Guide

## Overview

Deploy the JaneMaiks Retail Assistant for **free** on:
- **Frontend:** Vercel or Netlify (React + Vite SPA)
- **Backend:** Render or Railway (FastAPI)
- **Database:** SQLite (dev) or PostgreSQL (production via Render/Railway)

---

## Architecture

```
Phone/Tablet Browser
       |
       | HTTPS
       |
  ┌────┴────┐        ┌──────────────┐
  │ Vercel  │  API   │   Render     │
  │ Frontend├───────>│   Backend    │
  │ (React) │        │  (FastAPI)   │
  └─────────┘        └──────┬───────┘
                            │
                     ┌──────┴───────┐
                     │  PostgreSQL  │
                     │  (optional)  │
                     └──────────────┘
```

The frontend reverse-proxies `/api/*` requests to the backend URL via `VITE_API_BASE_URL`.

---

## 1. Environment Variables

### Frontend (`frontend/.env.production`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_BASE_URL` | Yes | `/api` | Backend API URL — set to your Render/Railway URL in production, e.g. `https://janemaiks-api.onrender.com/api` |
| `VITE_API_TIMEOUT` | No | `15000` | API request timeout in milliseconds |

### Backend (`backend/.env`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | `sqlite:///./retail_assistant.db` | PostgreSQL connection string for production |
| `SECRET_KEY` | Yes | (change me) | Random secret for JWT signing — generate with `openssl rand -hex 32` |
| `CORS_ORIGINS` | Yes | `http://localhost:5173` | Comma-separated allowed CORS origins (your Vercel/Netlify URL) |
| `DEBUG` | No | `False` | Set to `False` in production |
| `DEFAULT_PASSWORD` | No | `admin123` | Initial admin password (change immediately) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `1440` | JWT expiry (24 hours default) |
| `DEFAULT_PROFIT_MARGIN` | No | `15` | Default profit margin percentage |
| `EMBEDDING_MODEL` | No | `all-MiniLM-L6-v2` | Sentence transformer model |
| `CHROMA_PERSIST_DIR` | No | `./chroma_db` | ChromaDB storage path |

---

## 2. Backend Deployment (Render)

### Prerequisites
- A [Render](https://render.com) account (free tier)
- Your code pushed to a Git repository (GitHub/GitLab)

### Steps

1. **Create a new Web Service** on Render
   - Connect your Git repo
   - Select the `backend/` directory as root
   - Set:
     - **Name:** `janemaiks-api`
     - **Runtime:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

2. **Add Environment Variables** in Render dashboard:
   ```
   DATABASE_URL=postgresql://... (your Render PostgreSQL URL)
   SECRET_KEY=<random-hex-string>
   CORS_ORIGINS=https://janemaiks.vercel.app
   DEBUG=False
   DEFAULT_PASSWORD=<strong-password>
   ```

3. **Optional — Add PostgreSQL** via Render's PostgreSQL add-on

4. **Deploy** — Render auto-deploys on push

### Alternative: Railway

1. Create a new project on [Railway](https://railway.app)
2. Connect your repo, select the `backend/` directory
3. Railway auto-detects Python + requirements.txt
4. Add environment variables as above
5. Railway provides PostgreSQL with one click

---

## 3. Frontend Deployment (Vercel)

### Steps

1. Push code to GitHub/GitLab

2. **Import project** in Vercel
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend/`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`

3. **Environment Variables** in Vercel:
   ```
   VITE_API_BASE_URL=https://janemaiks-api.onrender.com/api
   ```

   > **Important:** If you leave `VITE_API_BASE_URL` as `/api`, the frontend will proxy through Vercel. In that case, you need to configure a **rewrite rule** in `vercel.json`. The included `vercel.json` rewrites all routes to `index.html` for SPA support.

4. **Deploy** — Vercel auto-deploys on push

### Alternative: Netlify

1. Import from Git in Netlify
   - **Base directory:** `frontend/`
   - **Build command:** `npm run build`
   - **Publish directory:** `dist`

2. Add environment variable: `VITE_API_BASE_URL=https://janemaiks-api.onrender.com/api`

3. The included `_redirects` file handles SPA routing for Netlify.

---

## 4. Mobile Testing

1. Open the deployed URL on your phone
2. **Sign in** with the admin credentials
3. The app is fully responsive — Dashboard, Products, AI Assistant, Analytics all work on mobile
4. **Install to Home Screen:**
   - **iPhone (Safari):** Tap Share > Add to Home Screen
   - **Android (Chrome):** Tap menu > Add to Home Screen

---

## 5. Production Build Commands

### Frontend
```bash
cd frontend
npm install
npm run build     # outputs to dist/
npm run preview   # preview production build locally
```

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 6. Security Checklist

- [x] JWT-based authentication with bcrypt password hashing
- [x] Login page blocks unauthorized access
- [x] Security headers: X-Content-Type-Options, X-Frame-Options, HSTS
- [x] CORS restricted to specific origins
- [x] Debug mode disabled in production
- [x] API docs disabled in production (no `/docs`, no `/redoc`)
- [x] Global exception handler (no stack traces leaked)

### Post-Deployment
1. Change the `DEFAULT_PASSWORD` via environment variable
2. Set a strong `SECRET_KEY` (use `openssl rand -hex 32`)
3. Verify `DEBUG=False` in production
4. Ensure `CORS_ORIGINS` contains only your frontend URL(s)

---

## 7. Authentication

The app uses a single **family-shared admin account**:

- **Username:** `admin`
- **Default Password:** `admin123` (change via `DEFAULT_PASSWORD` env var)

After login, a JWT token is stored in the browser's localStorage. The token auto-expires after 24 hours (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).

**Login flow:**
1. Visit the app URL — redirects to `/login`
2. Enter username + password
3. On success, redirect to dashboard
4. On failure, error message shown

---

## 8. PWA Support

The app is installable as a Progressive Web App:
- **manifest.json** — defines app name, icons, theme color
- **Service Worker** (`sw.js`) — caches static assets for offline support
- **Offline** — the app shell loads from cache when offline
- **Install prompt** — mobile browsers prompt to install to home screen

---

## 9. Database

### SQLite (Development)
No configuration needed — runs out of the box.

### PostgreSQL (Production)
1. Provision PostgreSQL via Render/Railway
2. Set `DATABASE_URL` to the connection string:
   ```
   DATABASE_URL=postgresql://user:pass@host:5432/dbname
   ```
3. The app auto-adapts — SQLite gets `check_same_thread`, PostgreSQL gets connection pooling

---

## 10. Cost Breakdown

| Service | Tier | Cost | Notes |
|---------|------|------|-------|
| Vercel | Hobby | Free | 100 GB bandwidth, automatic SSL |
| Netlify | Free | Free | 100 GB bandwidth, automatic SSL |
| Render | Free | Free | 512 MB RAM, sleeps after 15 min idle |
| Railway | Free | $5 credit | No sleep, needs credit card |
| **Total** | | **$0/month** | With Render + Vercel free tiers |

> **Render free tier note:** The backend sleeps after 15 minutes of inactivity. First request after idle takes ~30 seconds to wake up. For always-on, upgrade to Render Starter ($7/month) or use Railway.

---

## 11. Quick Deploy (One-Liner)

### Backend (Render)
```
# In Render dashboard:
Build Command: pip install -r backend/requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Frontend (Vercel)
```
# Import project, framework=Vite, root=frontend/
# Env: VITE_API_BASE_URL=https://your-app.onrender.com/api
```

---

## 12. Troubleshooting

### "Network Error" on login
- Ensure `VITE_API_BASE_URL` points to the correct backend URL
- Check CORS settings — the backend `CORS_ORIGINS` must include the frontend URL
- Verify the backend is running: visit `https://your-backend.onrender.com/api/health`

### Blank page after login
- Check browser console for errors
- Ensure the JWT token is being sent with API requests
- Clear localStorage and try again

### Database errors
- For PostgreSQL: verify the connection string is correct
- For SQLite: ensure the `retail_assistant.db` path is writable

### Service worker not registering
- The app must be served over HTTPS (Vercel/Render provide this automatically)
- Ensure the `sw.js` file is in the `public/` directory
- Check browser DevTools > Application > Service Workers
