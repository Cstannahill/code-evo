Deploying backend image to Railway via GHCR

[Publish to GHCR badge]
Replace <OWNER> and <REPO> below with your GitHub owner and repository name to render the badge.

![Publish to GHCR](https://github.com/<OWNER>/<REPO>/actions/workflows/publish-ghcr.yml/badge.svg)

Overview

This repository publishes a production-ready backend image to GitHub Container Registry (GHCR) using the `publish-ghcr.yml` workflow. The workflow builds `backend/Dockerfile.prod`, optionally runs staging migrations, and pushes images to GHCR.

1. CI publishes image

- The GitHub Action `publish-ghcr.yml` builds `backend/Dockerfile.prod` and pushes images to:
  - `ghcr.io/<OWNER>/code-evo-backend:latest`
  - `ghcr.io/<OWNER>/code-evo-backend:<commit-sha>`
- The workflow runs on pushes to `main` and can also be triggered manually via workflow dispatch.

2. Configure Railway to use the image

- In Railway, create a new service and choose "Deploy from Image".
- Set the image to: `ghcr.io/<OWNER>/code-evo-backend:latest` (replace `<OWNER>` with your GitHub org/user).
- Ensure Railway can pull from GHCR:
  - Add registry credentials in Railway that use a PAT with `read:packages` scope, or
  - Make the GHCR package public (not recommended for private repos).

3. GitHub repo settings

- The workflow uses `GITHUB_TOKEN` to authenticate and push to GHCR. Ensure your repository/organization allows `GITHUB_TOKEN` to publish packages.

4. Environment variables (Railway service settings)

- REDIS_HOST, REDIS_PORT (or use Railway Redis add-on)
- CHROMA_HOST, CHROMA_PORT (if using remote Chroma)
- MONGODB_URL (if using MongoDB)
- DATABASE_URL (Postgres connection if using SQL DB)
- DISABLE_OLLAMA_DISCOVERY=1 (recommended unless Ollama is reachable from the runtime)
- DISABLE_OPENAPI=1 (recommended in production)

5. Staging migrations (STAGING_DATABASE_URL)

- To run migrations against a staging database before publishing, set the repository secret `STAGING_DATABASE_URL` to your staging DB connection string (example: `postgresql://user:pass@host:5432/dbname`).
- When `STAGING_DATABASE_URL` is present, the workflow runs `alembic upgrade head` against that DB prior to building and pushing the image.
- Ensure your staging DB accepts connections from GitHub Actions runners (IP allowlists) or run the workflow on a self-hosted runner inside your network.

6. Manual workflow dispatch

- Go to the Actions tab in GitHub, open "Publish Backend Image to GHCR" and click "Run workflow".
- If you want staging migrations to run during manual dispatch, make sure `STAGING_DATABASE_URL` is set in repository secrets.

7. Local quick test commands

```bash
# from repo root
# Build the production image locally
docker build -f backend/Dockerfile.prod -t code-evo-be:latest ./backend

# Run the container (disable Ollama discovery by default)
docker run --rm -e DISABLE_OLLAMA_DISCOVERY=1 -p 8080:8080 code-evo-be:latest \
  sh -c "uvicorn app.main:app --host 0.0.0.0 --port 8080 --app-dir /app/backend"

# Then visit: http://localhost:8080/health
```

Next actions I can take

- Add a Railway deploy workflow that triggers after the GHCR publish (optional).
- Add a workflow badge that shows the published image digest (optional).
- Add a short check that validates the image runs a /health check in the workflow after push (optional).

Which of the above would you like me to add next?
