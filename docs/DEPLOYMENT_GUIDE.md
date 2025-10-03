# Code Evolution Tracker - Deployment Guide

## Overview

This guide covers the user authentication system, API key management, and repository access controls implemented for the demo deployment.

## Features Implemented

### 1. User Authentication System

- **User Registration**: Users can create accounts with username, email, and password
- **User Login**: Secure JWT-based authentication
- **Guest Access**: Temporary guest users for trying the system without registration
- **Session Management**: JWT tokens with proper expiration handling

### 2. API Key Management

- **Per-User API Keys**: Registered users can store encrypted API keys for OpenAI, Anthropic, and Gemini
- **Guest API Keys**: Guest users can provide API keys for one-time use (stored temporarily in cache)
- **Encryption**: All API keys are encrypted using Fernet before storage
- **Usage Tracking**: Track when and how often API keys are used

### 3. Repository Management

- **Global Repository Table**: All analyzed repositories are stored in a global table for browsing
- **User-Specific Repositories**: Registered users have their own repository collections
- **Access Control**: Repositories can be public (visible to all) or private (user-only)
- **Repository Stats**: Track analysis count and unique users per repository

## Backend Implementation

### Database Models

#### User Models

```python
# MongoDB Models
class User(Model):
    username: str
    email: str
    full_name: Optional[str]
    hashed_password: str
    is_active: bool = True
    is_guest: bool = False
    created_at: datetime
    last_login: Optional[datetime]

class APIKey(Model):
    user_id: ObjectId
    provider: str  # openai, anthropic, gemini
    key_name: Optional[str]
    encrypted_key: str  # Fernet encrypted
    created_at: datetime
    last_used: Optional[datetime]
    is_active: bool = True
    usage_count: int = 0

class UserRepository(Model):
    user_id: ObjectId
    repository_id: ObjectId
    access_type: str = "owner"  # owner, viewer, contributor
    created_at: datetime
    last_accessed: Optional[datetime]
```

#### Enhanced Repository Model

```python
class Repository(Model):
    url: str
    name: str
    default_branch: str = "main"
    status: str = "pending"
    total_commits: int = 0
    created_at: datetime
    last_analyzed: Optional[datetime]

    # New fields for global/user management
    is_public: bool = True
    created_by_user: Optional[ObjectId]
    analysis_count: int = 0  # popularity tracking
    unique_users: int = 0   # unique users who analyzed it
    tags: List[str] = []    # searchable tags
    description: Optional[str]
    primary_language: Optional[str]
```

### API Endpoints

#### Authentication Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/guest` - Create guest session
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/api-keys` - Add/update API key
- `GET /api/auth/api-keys` - Get user's API keys
- `DELETE /api/auth/api-keys/{key_id}` - Delete API key

#### Guest API Key Endpoints

- `POST /api/auth/guest/api-keys` - Set temporary API keys for guest
- `GET /api/auth/guest/api-keys` - Get guest's available API keys

#### Repository Endpoints

**User-Specific:**

- `GET /api/repositories/user/my-repositories` - Get user's repositories
- `POST /api/repositories/user/add-repository` - Add repository to user's collection
- `DELETE /api/repositories/user/repositories/{repo_id}` - Remove repository from user

**Global:**

- `GET /api/repositories/global` - Browse public repositories with pagination
- `GET /api/repositories/global/popular` - Get most analyzed repositories
- `GET /api/repositories/global/recent` - Get recently added repositories

### Security Features

1. **Password Hashing**: Uses bcrypt for secure password storage
2. **API Key Encryption**: Fernet symmetric encryption for API keys
3. **JWT Tokens**: Secure session management with expiration
4. **Environment Variables**: Encryption keys and secrets stored in environment
5. **Input Validation**: Pydantic models for request validation

## Frontend Implementation

### Components Created

1. **AuthProvider**: Context provider for authentication state
2. **LoginForm**: User login interface
3. **RegisterForm**: User registration interface
4. **AuthModal**: Modal container for login/register forms
5. **UserMenu**: Dropdown menu with user actions
6. **APIKeyManager**: Interface for managing API keys (both user and guest)

### Authentication Hook

```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isGuest: boolean;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (data: RegisterData) => Promise<void>;
  loginAsGuest: () => Promise<void>;
  logout: () => void;
}
```

## Environment Setup

### Required Environment Variables

```bash
# Backend (.env file)
SECRET_KEY=your-jwt-secret-key-here
ENCRYPTION_KEY=your-fernet-encryption-key-here
MONGODB_URL=your-mongodb-connection-string
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Dependencies Added

Backend dependencies already included in requirements.txt:

- `cryptography` - For API key encryption
- `passlib[bcrypt]` - For password hashing
- `python-jose[cryptography]` - For JWT handling

## Database Setup

1. **MongoDB Collections**: The new models will automatically create collections on first use
2. **Indexes**: Proper indexes are created for performance on user queries
3. **Migration**: Existing repositories will be marked as public by default

## Usage Flow

### For New Users

1. User visits the site
2. Can choose to register, login, or continue as guest
3. If guest: can provide API keys temporarily for analysis
4. If registered: can save API keys permanently and build repository collection

### For Repository Analysis

1. **Guest Users**: Provide API keys → analyze any public repository → results visible but not saved to user account
2. **Registered Users**: Use saved API keys → analyze repositories → save to personal collection → contribute to global repository table

## Security Considerations

1. **API Key Storage**: Keys are encrypted at rest and only decrypted when needed
2. **Guest Sessions**: Temporary keys expire in 24 hours and are cleared from cache
3. **Access Control**: Users can only access their own repository collections
4. **Rate Limiting**: Should be implemented for API endpoints
5. **HTTPS**: Must be used in production for secure token transmission

## Deployment Steps

1. **Environment Setup**: Configure all environment variables
2. **Database Migration**: Ensure MongoDB is running and accessible
3. **Frontend Build**: Build React app with authentication components integrated
4. **Backend Deploy**: Deploy FastAPI application with new auth endpoints
5. **Testing**: Test all authentication flows and API key management
6. **Monitoring**: Set up logging for authentication events and API usage

## Testing Checklist

- [ ] User registration works
- [ ] User login works
- [ ] Guest login works
- [ ] API key addition/deletion works for registered users
- [ ] Guest API key setting works
- [ ] Repository analysis uses correct API keys
- [ ] User repository collections work
- [ ] Global repository browsing works
- [ ] JWT token expiration handling works
- [ ] Logout functionality works

## Future Enhancements

1. **OAuth Integration**: Add GitHub, Google OAuth options
2. **Team Management**: Allow users to share repositories with team members
3. **Usage Analytics**: Track API usage and costs per user
4. **Repository Permissions**: More granular access controls
5. **Notification System**: Alert users when analysis completes
6. **API Rate Limiting**: Implement per-user rate limits
7. **Audit Logging**: Track all user actions for security

This implementation provides a complete authentication and repository management system suitable for a demo deployment while maintaining security best practices.

---

## Deployment & Migrations (additional notes)

### Production Docker image

Use `backend/Dockerfile.prod` to build a multi-stage production image. The runtime image respects the `PORT` environment variable and includes a HEALTHCHECK against `/health`.

Example:

```bash
# build
docker build -t code-evo-backend:prod -f backend/Dockerfile.prod .

# run (set necessary env vars)
docker run -e PORT=8080 -e DATABASE_URL="$DATABASE_URL" -p 8080:8080 code-evo-backend:prod
```

### Required environment variables (summary)

- PORT (default 8080)
- DATABASE_URL (postgres connection string)
- MONGODB_URL
- REDIS_HOST / REDIS_PORT
- CHROMA_HOST / CHROMA_PORT
- OPENAI_API_KEY / ANTHROPIC_API_KEY (optional)
- OLLAMA_HOST / OLLAMA_PORT (optional)
- CORS_ORIGINS: optional comma-separated list overriding default dev origins
- DISABLE_OPENAPI: set to `true` to skip OpenAPI generation at startup

### SQLite → Postgres migration

If migrating from the bundled SQLite DB (`backend/code_evolution.db`) to Postgres, you can use the helper script in `backend/scripts/migrate_sqlite_to_postgres.py` (if present) or a tool like `pgloader`:

```bash
# example using the helper script
python backend/scripts/migrate_sqlite_to_postgres.py --sqlite-file backend/code_evolution.db --database-url "$DATABASE_URL"

# after migration, run alembic migrations if your Postgres schema requires it
export DATABASE_URL="$DATABASE_URL"
alembic upgrade head
```

If the helper script isn't present, consider exporting data via CSV/SQL and importing into Postgres using standard tooling.

### Notes

- `backend/requirements.prod.txt` contains a minimal runtime set of packages. Add additional packages there if your deployment requires optional features (e.g., Ollama/langchain adapters).
- The entrypoint `backend/wait_for_services.sh` waits for dependent services on startup; in some PaaS environments you may prefer to run the server directly and rely on platform health checks instead.
