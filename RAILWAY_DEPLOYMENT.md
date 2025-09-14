# Railway Deployment Guide for Code Evolution Tracker

This guide explains how to deploy the Code Evolution Tracker to Railway with proper ChromaDB integration.

## 🚀 Quick Deployment

### Option 1: Using Railway CLI (Recommended)

1. **Install Railway CLI**:
   ```bash
   npm install -g @railway/cli
   # or
   curl -fsSL https://railway.app/install.sh | sh
   ```

2. **Login to Railway**:
   ```bash
   railway login
   ```

3. **Deploy from your project directory**:
   ```bash
   railway deploy
   ```

### Option 2: Using Railway Dashboard

1. Go to [Railway.app](https://railway.app)
2. Create a new project
3. Connect your GitHub repository
4. Railway will automatically detect the `railway.json` configuration

## 🔧 Configuration

### Environment Variables

Set these environment variables in your Railway project:

#### Required
- `PORT` - Railway automatically sets this
- `RAILWAY_ENVIRONMENT=1` - Automatically set by Railway

#### Database
- `DATABASE_URL` - Add a PostgreSQL service in Railway and use its connection string
- `MONGODB_URL` - Add a MongoDB service in Railway and use its connection string

#### Cache
- `REDIS_HOST` - Add a Redis service in Railway
- `REDIS_PORT` - Usually 6379
- `REDIS_PASSWORD` - If your Redis service requires authentication

#### AI Services (Optional)
- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key

#### ChromaDB
- `CHROMA_DB_PATH=/tmp/chroma_db` - Automatically set for embedded mode
- `CHROMA_HOST=localhost` - Automatically set for embedded mode

### Services to Add in Railway

1. **PostgreSQL** - For the main database
2. **MongoDB** - For enhanced document storage
3. **Redis** - For caching (optional but recommended)

## 🐳 Docker Configuration

The deployment uses `backend/Dockerfile.railway` which:

- ✅ Sets up embedded ChromaDB (no external service needed)
- ✅ Creates proper directories with correct permissions
- ✅ Configures Railway environment detection
- ✅ Includes health checks
- ✅ Optimizes for Railway's container environment

## 🔍 ChromaDB Integration

### How it Works

The application automatically detects Railway deployment and switches to **embedded ChromaDB mode**:

1. **Detection**: Checks for `RAILWAY_ENVIRONMENT` or `PORT` environment variables
2. **Embedded Mode**: Uses `chromadb.PersistentClient` with `/tmp/chroma_db` path
3. **No External Service**: No need for separate ChromaDB container
4. **Persistence**: Data persists within the container's filesystem

### Benefits

- ✅ **Simplified Deployment**: Single container, no service orchestration
- ✅ **Cost Effective**: No additional ChromaDB service costs
- ✅ **Railway Optimized**: Works perfectly with Railway's container model
- ✅ **Automatic Fallback**: Falls back to external ChromaDB in local development

## 🚨 Troubleshooting

### Common Issues

1. **ChromaDB Connection Errors**
   - Ensure `RAILWAY_ENVIRONMENT=1` is set
   - Check that `/tmp/chroma_db` directory exists and is writable

2. **Database Connection Issues**
   - Verify `DATABASE_URL` is correctly set
   - Ensure PostgreSQL service is running in Railway

3. **Redis Connection Issues**
   - Check `REDIS_HOST` and `REDIS_PORT` environment variables
   - Verify Redis service is running in Railway

### Health Check

Visit `https://your-app.railway.app/health` to check:
- Database connectivity
- ChromaDB status
- Redis connectivity
- AI service availability

### Logs

Check Railway logs for detailed error information:
```bash
railway logs
```

## 🔄 Local Development vs Production

| Feature | Local Development | Railway Production |
|---------|------------------|-------------------|
| ChromaDB | External service (docker-compose) | Embedded in container |
| Database | SQLite file | PostgreSQL service |
| Redis | Docker service | Railway Redis service |
| Port | 8080 | Railway's PORT env var |
| Environment | `RAILWAY_ENVIRONMENT` not set | `RAILWAY_ENVIRONMENT=1` |

## 📝 Migration Notes

### From Docker Compose to Railway

1. **Remove external ChromaDB service** - Now embedded
2. **Use managed databases** - PostgreSQL and MongoDB services
3. **Update environment variables** - Railway-specific configuration
4. **Single container deployment** - No service orchestration needed

### Data Migration

If you have existing data:

1. **Export from local SQLite**:
   ```bash
   sqlite3 code_evolution.db .dump > backup.sql
   ```

2. **Import to Railway PostgreSQL**:
   ```bash
   psql $DATABASE_URL < backup.sql
   ```

## 🎯 Best Practices

1. **Use Railway's managed services** for databases and Redis
2. **Set proper environment variables** for all services
3. **Monitor health checks** regularly
4. **Use Railway's built-in monitoring** for performance insights
5. **Keep secrets secure** using Railway's environment variable system

## 📞 Support

If you encounter issues:

1. Check the health endpoint: `/health`
2. Review Railway logs
3. Verify environment variables
4. Test locally with Railway environment variables set

---

**Ready to deploy?** Run `railway deploy` from your project directory! 🚀
