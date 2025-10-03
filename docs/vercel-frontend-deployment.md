# Frontend Deployment Guide — Vercel + Railway Backend

This guide walks through verifying the existing Railway backend service and publishing the Vite/React frontend (`frontend/`) as a static site on Vercel that talks to the deployed API.

---

## 1. Confirm backend readiness on Railway

Your backend is containerised for Railway via `backend/Dockerfile.railway`. It already:

- Installs dependencies from `backend/requirements.railway.txt`
- Runs `wait_for_services.sh` to block until Redis (and optional services) are reachable
- Exposes port `8080` (Railway maps the container to the platform-assigned `$PORT`)
- Provides a `/health` endpoint for the built-in health check
- Enables enhanced CORS via `app/core/middleware.py`

### 1.1 Required environment variables

Set these in the Railway service (values depend on your stack):

| Variable                                           | Purpose                                                                                                                                |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `PORT` _(Railway managed)_                         | Railway injects this automatically; do not hard-code.                                                                                  |
| `DISABLE_OLLAMA_DISCOVERY=1`                       | Prevents startup delays if Ollama is not reachable from the container.                                                                 |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`       | Point to your Redis instance; Railway add-on values work.                                                                              |
| `REDIS_URL` _(optional)_                           | Only needed if you prefer a single connection string.                                                                                  |
| `MONGODB_URL`                                      | MongoDB connection string (Railway add-on or external cluster).                                                                        |
| `CHROMA_HOST`, `CHROMA_PORT` _(optional)_          | Needed only if you run Chroma externally. Keep defaults to use the embedded DB.                                                        |
| `CORS_ORIGINS`                                     | Comma-separated list of allowed frontend origins. Include your Vercel domain(s) before going live, e.g. `https://your-app.vercel.app`. |
| `SECRET_KEY` _(recommended)_                       | Override the development secret for token signing.                                                                                     |
| `LOG_LEVEL`, `DEBUG` _(optional)_                  | Set production logging preferences (`INFO` / `WARNING`, `DEBUG=false`).                                                                |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` _(optional)_ | Only if you are enabling cloud AI models.                                                                                              |

> Tip: use Railway “Variables” to manage secrets and create separate environments (production vs staging) with their own values.

### 1.2 Health check & logs

- Ensure Railways health check path remains `/health` (configured in the Dockerfile). The service should report healthy within a few seconds after boot.
- Check service logs after each deploy for warnings about missing dependencies (Redis, MongoDB, Chroma). If a dependency is intentionally unused, you can safely ignore the warning or remove the wait logic from `wait_for_services.sh`.

### 1.3 Testing locally (optional)

```bash
# At the repo root
pnpm install
cd backend
pip install -r requirements.railway.txt
uvicorn app.main:app --reload --port 8080
# Visit http://localhost:8080/health to confirm the API responds
```

---

## 2. Prepare the frontend for static hosting

The frontend is a Vite + React 19 app located in `frontend/`. The production build is a static bundle output to `frontend/dist` via `pnpm build`.

Key configuration files:

- `.env` – default dev API base (`http://localhost:8080`).
- `src/config/environment.ts` – picks the API URL from `VITE_API_BASE_URL` or falls back to `https://backend-production-712a.up.railway.app`.
- `vite.config.ts` – development proxy for `/api` requests.

Before deploying to Vercel, decide which backend URL you want the site to use (e.g. your Railway production domain).

### 2.1 Build command

Inside Vercel you'll set the root directory to `frontend/` and run:

```
pnpm install
pnpm build
```

Vercel auto-detects PNPM from `packageManager`. The build output directory is `frontend/dist`.

### 2.2 Required environment variable

Add the following to Vercel **Environment Variables** (Production and Preview, as needed):

| Key                 | Value                                                                                                  |
| ------------------- | ------------------------------------------------------------------------------------------------------ |
| `VITE_API_BASE_URL` | `https://backend-production-712a.up.railway.app` _(replace with your Railway domain or custom domain)_ |

Using an explicit value avoids reliance on the hard-coded fallback and allows per-environment overrides (e.g. staging backend for preview deployments).

> If you later add custom domains, update both Vercel and the Railway `CORS_ORIGINS` variable accordingly.

---

## 3. Deploying the static site on Vercel

1. **Create the project**

   - In Vercel dashboard, click **Add New 0 Project** and import your Git repository.
   - When prompted for the root directory, choose `frontend/`.

2. **Configure build settings**

   - _Framework Preset_: Vite
   - _Build Command_: `pnpm build`
   - _Install Command_: `pnpm install`
   - _Output Directory_: `dist`

3. **Environment variables**

   - Add `VITE_API_BASE_URL` as noted above.
   - (Optional) Add `SENTRY_DSN`, analytics keys, etc., if the frontend consumes them.

4. **Trigger the first deploy**

   - Click **Deploy**. Vercel installs dependencies, runs the build, and uploads the static `dist/` artifacts.
   - Once finished, Vercel assigns a preview URL, e.g. `https://your-app-git-main-user.vercel.app`.

5. **Verify connectivity**

   - Visit the deployed site and perform an action that calls the backend (e.g. load repositories).
   - Inspect the browser console/network tab to confirm requests hit `https://backend-production-712a.up.railway.app` (or your configured URL) and receive `200` responses.

6. **Promote to production**

   - Assign a production domain (default `https://your-app.vercel.app` or a custom domain).
   - Update Railway `CORS_ORIGINS` to include the production domain, separated by commas if multiple origins.

7. **Set up previews (optional)**
   - On Vercel, configure preview deployments to use a staging backend by setting `VITE_API_BASE_URL` under _Preview Environment_. Update `CORS_ORIGINS` with the preview domain if you need to test authenticated flows.

---

## 4. Post-deploy checklist

- ✅ `https://backend-production-712a.up.railway.app/health` returns `200`.
- ✅ Frontend loads without CORS errors (check browser console).
- ✅ Secrets are stored in Railway/Vercel env settings, not committed to Git.
- ✅ (Optional) analytics, monitoring, or logging integrations are enabled as needed.
- ✅ Document future maintainers: link this guide (`docs/vercel-frontend-deployment.md`) in your project README.

---

## 5. Troubleshooting tips

| Issue                                      | Resolution                                                                                                                   |
| ------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `FetchError: TypeError: Failed to fetch`   | Ensure `VITE_API_BASE_URL` points to a reachable HTTPS endpoint and `CORS_ORIGINS` on the backend include the Vercel origin. |
| `503` or `connection refused` from backend | Confirm Railway service is running, dependencies (Redis/Mongo) are awake, and network policies allow outbound traffic.       |
| `CORS` preflight failures                  | Add the Vercel domain to `CORS_ORIGINS` and redeploy the backend.                                                            |
| Environment variable not applied           | Redeploy the Vercel project; Vite inlines variables at build time.                                                           |
| Mixed content warnings                     | Always use HTTPS for the API base URL when serving over HTTPS.                                                               |

Happy shipping! 🎉
