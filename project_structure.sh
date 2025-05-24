# Create complete backend structure
mkdir -p backend/{app/{core,api,models,services,schemas,agents},tests,alembic/versions}

# Create __init__.py files
touch backend/app/__init__.py
touch backend/app/core/__init__.py
touch backend/app/api/__init__.py
touch backend/app/models/__init__.py
touch backend/app/services/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/agents/__init__.py

# Project structure:
# backend/
# ├── app/
# │   ├── core/          # Config, database, security
# │   ├── api/           # API endpoints
# │   ├── models/        # SQLAlchemy models
# │   ├── services/      # Business logic
# │   ├── schemas/       # Pydantic schemas
# │   ├── agents/        # AI agents
# │   └── main.py        # FastAPI app
# ├── tests/
# ├── alembic/           # Database migrations
# └── requirements.txt