
# AGENTS.md – Backend Agent Directives for Codex

You are tasked with restoring and improving the **backend functionality** of an AI-enhanced FastAPI application. The backend uses **Pydantic models**, a **MongoDB database**, and a commit analysis pipeline. Your actions will directly impact data integrity, developer experience, and the quality of insights produced.

---

## 🔧 Primary Objectives

1. **Model Restoration**

   - Ensure all FastAPI routes correctly reference and use the appropriate **Pydantic models**.
   - Identify and fix any broken model bindings in request or response schemas.
   - Normalize types across schemas — remove duplicate or mismatched types where possible.

2. **Git Repository Submission**

   - Restore the functionality that allows **cloning a Git repository** through the frontend.
   - The `POST /submit` or equivalent endpoint should accept a Git URL, clone the repo, and trigger the analysis pipeline automatically.

3. **Commit Analysis Pipeline**

   - Refactor and **improve the commit analysis logic**.
     - Ensure each commit is deeply analyzed (diffs, author stats, refactoring detection, complexity changes).
     - Output should include clear insight on what changed, why it matters, and whether it improved or regressed the codebase.
   - Performance must be optimized for **batch commit processing** and resilience against malformed commit histories.

4. **MongoDB Persistence**

   - Audit all database interactions:
     - **Ensure all relevant fields are being persisted**.
     - Identify and restore fields lost in the migration from SQLite to Mongo.
     - Validate schema consistency between in-code models and Mongo collections.

5. **Type Cleanup & Consolidation**
   - Identify duplicated or similar Pydantic models across the codebase.
     - Merge into a single source of truth per entity (`Commit`, `Repository`, `AnalysisResult`, etc.).
     - Apply strict typing using `Literal`, `Annotated`, `Union` where needed to ensure schema contracts are consistent.
   - Apply backend-wide validation rules via Pydantic Config, e.g.:
     ```python
     class Config:
         extra = "forbid"
         validate_assignment = True
     ```

---

## 🧠 Codex Guidance

You are empowered to:

- Traverse all relevant files (routes, models, services, utils).
- Propose clean architectural corrections where needed.
- Automatically generate replacement code for missing or broken handlers.
- Create or update OpenAPI docs from the FastAPI router to reflect updated models.
- Maintain separation of concerns (avoid bloated service layers).

---

## 📦 Expected Structure

Ensure the following modules exist and are wired correctly:

# AGENTS.md – Backend Agent Directives for Codex

You are tasked with restoring and improving the **backend functionality** of an AI-enhanced FastAPI application. The backend uses **Pydantic models**, a **MongoDB database**, and a commit analysis pipeline. Your actions will directly impact data integrity, developer experience, and the quality of insights produced.

---

## 🔧 Primary Objectives

1. **Model Restoration**

   - Ensure all FastAPI routes correctly reference and use the appropriate **Pydantic models**.
   - Identify and fix any broken model bindings in request or response schemas.
   - Normalize types across schemas — remove duplicate or mismatched types where possible.

2. **Git Repository Submission**

   - Restore the functionality that allows **cloning a Git repository** through the frontend.
   - The `POST /submit` or equivalent endpoint should accept a Git URL, clone the repo, and trigger the analysis pipeline automatically.

3. **Commit Analysis Pipeline**

   - Refactor and **improve the commit analysis logic**.
     - Ensure each commit is deeply analyzed (diffs, author stats, refactoring detection, complexity changes).
     - Output should include clear insight on what changed, why it matters, and whether it improved or regressed the codebase.
   - Performance must be optimized for **batch commit processing** and resilience against malformed commit histories.

4. **MongoDB Persistence**

   - Audit all database interactions:
     - **Ensure all relevant fields are being persisted**.
     - Identify and restore fields lost in the migration from SQLite to Mongo.
     - Validate schema consistency between in-code models and Mongo collections.

5. **Type Cleanup & Consolidation**
   - Identify duplicated or similar Pydantic models across the codebase.
     - Merge into a single source of truth per entity (`Commit`, `Repository`, `AnalysisResult`, etc.).
     - Apply strict typing using `Literal`, `Annotated`, `Union` where needed to ensure schema contracts are consistent.
   - Apply backend-wide validation rules via Pydantic Config, e.g.:
     ```python
     class Config:
         extra = "forbid"
         validate_assignment = True
     ```

---

## 🧠 Codex Guidance

You are empowered to:

- Traverse all relevant files (routes, models, services, utils).
- Propose clean architectural corrections where needed.
- Automatically generate replacement code for missing or broken handlers.
- Create or update OpenAPI docs from the FastAPI router to reflect updated models.
- Maintain separation of concerns (avoid bloated service layers).

---

## 📦 Expected Structure

Ensure the following modules exist and are wired correctly:

```plaintext
backend
├── Dockerfile
├── app
│   ├── __init__.py
│   ├── agents
│   │   └── __init__.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── auth.py
│   │   ├── multi_model_analysis.py
│   │   └── repositories.py
│   ├── core
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── middleware.py
│   │   ├── mongodb_config.py
│   │   ├── mongodb_indexes.py
│   │   └── mongodb_monitoring.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   └── repository.py
│   ├── schemas
│   │   ├── __init__.py
│   │   └── repository.py
│   ├── services
│   │   ├── __init__.py
│   │   ├── ai_analysis_service.py
│   │   ├── ai_service.py
│   │   ├── analysis_service.py
│   │   ├── multi_model_ai_service.py
│   │   ├── pattern_service.py
│   │   └── repository_service.py
│   ├── tasks
│   │   └── analysis_tasks.py
│   └── utils
│       ├── __init__.py
│       └── secret_scanner.py
├── chroma_db
│   └── chroma.sqlite3
├── code_evolution.db
├── code_evolution.log
├── complete_migration.py
├── create_db.py
├── migrate_to_enhanced_mongodb.py
├── mongodb_migration_report.json
├── old_requirements.txt
├── requirements-backup.txt
├── requirements-compatible.txt
├── requirements-windows.txt
├── requirements.txt
├── test_mongodb.py

```
=======
# AGENT_REPORT.md - Code Evolution Tracker Repair & Restoration

## ✅ Audit Summary
- Detected **15 FastAPI routes** using `@router.<method>()`
- Detected **36 models** inheriting from `BaseModel` or `Model`

## 🧩 Action Plan
1. **Restore Git Submission Flow**
   - Ensure the `/api/repositories` POST route triggers Git clone and pipeline.
   - Validate repo data (e.g., name, URL, branch) and persist it to MongoDB.

2. **Fix Commit Analysis Pipeline**
   - Ensure `analysis_service.py`, `ai_analysis_service.py`, and related files:
     - Analyze commits deeply (diffs, quality, patterns)
     - Aggregate results by commit, file, and pattern
     - Use async where possible to optimize throughput

3. **Repair MongoDB Persistence**
   - Validate all `Repository`, `Commit`, `PatternOccurrence`, etc., fields are saved.
   - Compare Mongo collections vs. SQL model definitions to detect missing fields.

4. **Audit and Consolidate Models**
   - Review all models listed below and merge redundant or outdated types.
   - Prefer shared schema contracts and use consistent naming.

## 🛠️ Detected FastAPI Routes
- `GET` /status  _(in `app/api/analysis.py`)_
- `POST` /code  _(in `app/api/analysis.py`)_
- `GET` /patterns  _(in `app/api/analysis.py`)_
- `GET` /patterns/{pattern_name}  _(in `app/api/analysis.py`)_
- `GET` /insights/{repository_id}  _(in `app/api/analysis.py`)_
- `GET` /ai-models  _(in `app/api/analysis.py`)_
- `POST` /models/{model_id}/benchmark  _(in `app/api/analysis.py`)_
- `POST` /evolution  _(in `app/api/analysis.py`)_
- `GET` /compare/{repo_id1}/{repo_id2}  _(in `app/api/analysis.py`)_
- `GET` /models/available  _(in `app/api/multi_model_analysis.py`)_
- `POST` /analyze/single  _(in `app/api/multi_model_analysis.py`)_
- `POST` /analyze/compare  _(in `app/api/multi_model_analysis.py`)_
- `POST` /analyze/repository  _(in `app/api/multi_model_analysis.py`)_
- `GET` /comparison/{comparison_id}  _(in `app/api/multi_model_analysis.py`)_
- `GET` /models/{model_name}/stats  _(in `app/api/multi_model_analysis.py`)_

## 🧪 Detected Models

- `Token` inherits `BaseModel`  _(defined in `app/api/auth.py`)_
- `TokenData` inherits `BaseModel`  _(defined in `app/api/auth.py`)_
- `User` inherits `BaseModel`  _(defined in `app/api/auth.py`)_
- `ModelSelectionRequest` inherits `BaseModel`  _(defined in `app/api/multi_model_analysis.py`)_
- `ComparisonAnalysisRequest` inherits `BaseModel`  _(defined in `app/api/multi_model_analysis.py`)_
- `ModelComparisonResponse` inherits `BaseModel`  _(defined in `app/api/multi_model_analysis.py`)_
- `RepositoryCreateWithModel` inherits `BaseModel`  _(defined in `app/api/repositories.py`)_
- `Repository` inherits `Model`  _(defined in `app/models/repository.py`)_
- `Commit` inherits `Model`  _(defined in `app/models/repository.py`)_
- `FileChange` inherits `Model`  _(defined in `app/models/repository.py`)_
- `Technology` inherits `Model`  _(defined in `app/models/repository.py`)_
- `Pattern` inherits `Model`  _(defined in `app/models/repository.py`)_
- `PatternOccurrence` inherits `Model`  _(defined in `app/models/repository.py`)_
- `AnalysisSession` inherits `Model`  _(defined in `app/models/repository.py`)_
- `AIModel` inherits `Model`  _(defined in `app/models/repository.py`)_
- `AIAnalysisResult` inherits `Model`  _(defined in `app/models/repository.py`)_
- `ModelComparison` inherits `Model`  _(defined in `app/models/repository.py`)_
- `ModelBenchmark` inherits `Model`  _(defined in `app/models/repository.py`)_
- `RepositoryCreate` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `RepositoryResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `AnalysisResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `TimelineResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `PatternOccurrenceResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `TechnologyResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `InsightResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `AIModelResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `AIAnalysisResultResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `ModelComparisonResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `AnalysisSessionResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `AIModelCreate` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `ModelComparisonCreate` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `AnalysisSessionCreate` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `ComprehensiveAnalysisResponse` inherits `BaseModel`  _(defined in `app/schemas/repository.py`)_
- `PatternAnalysis` inherits `BaseModel`  _(defined in `app/services/ai_service.py`)_
- `CodeQualityAnalysis` inherits `BaseModel`  _(defined in `app/services/ai_service.py`)_
- `EvolutionAnalysis` inherits `BaseModel`  _(defined in `app/services/ai_service.py`)_

---

Codex should use this report to assist in automated refactoring, validation, and restoration of backend functionality.

