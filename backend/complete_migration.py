# final_fixed_setup.py - Fixed the data insertion bug
"""
Final fixed SQLite database setup - data insertion bug resolved
"""

import logging
import uuid
from sqlalchemy import text
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_all_tables():
    """Create ALL tables first, then indexes"""

    # STEP 1: Create all tables (NO INDEXES YET)
    create_tables_sql = """
    CREATE TABLE IF NOT EXISTS repositories (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        url TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        default_branch TEXT DEFAULT 'main',
        status TEXT DEFAULT 'pending',
        total_commits INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        last_analyzed TEXT,
        error_message TEXT
    );

    CREATE TABLE IF NOT EXISTS commits (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        repository_id TEXT REFERENCES repositories(id) ON DELETE CASCADE,
        hash TEXT NOT NULL,
        author_name TEXT,
        author_email TEXT,
        committed_date TEXT,
        message TEXT,
        stats TEXT
    );

    CREATE TABLE IF NOT EXISTS file_changes (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        commit_id TEXT REFERENCES commits(id) ON DELETE CASCADE,
        file_path TEXT NOT NULL,
        change_type TEXT,
        language TEXT,
        additions INTEGER DEFAULT 0,
        deletions INTEGER DEFAULT 0,
        content_snippet TEXT
    );

    CREATE TABLE IF NOT EXISTS technologies (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        repository_id TEXT REFERENCES repositories(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        category TEXT,
        version TEXT,
        usage_count INTEGER DEFAULT 1,
        first_seen TEXT DEFAULT (datetime('now')),
        last_seen TEXT DEFAULT (datetime('now')),
        tech_metadata TEXT
    );

    CREATE TABLE IF NOT EXISTS patterns (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        name TEXT NOT NULL UNIQUE,
        category TEXT,
        description TEXT,
        complexity_level TEXT,
        is_antipattern INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS pattern_occurrences (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        repository_id TEXT REFERENCES repositories(id) ON DELETE CASCADE,
        pattern_id TEXT REFERENCES patterns(id) ON DELETE CASCADE,
        commit_id TEXT REFERENCES commits(id) ON DELETE CASCADE,
        file_path TEXT,
        code_snippet TEXT,
        line_number INTEGER,
        confidence_score REAL DEFAULT 1.0,
        detected_at TEXT DEFAULT (datetime('now')),
        ai_model_used TEXT,
        model_confidence REAL,
        processing_time_ms INTEGER,
        token_usage TEXT
    );

    CREATE TABLE IF NOT EXISTS analysis_sessions (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        repository_id TEXT REFERENCES repositories(id) ON DELETE CASCADE,
        status TEXT DEFAULT 'running',
        started_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT,
        commits_analyzed INTEGER DEFAULT 0,
        patterns_found INTEGER DEFAULT 0,
        configuration TEXT,
        error_message TEXT
    );

    CREATE TABLE IF NOT EXISTS ai_models (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        name TEXT NOT NULL UNIQUE,
        display_name TEXT NOT NULL,
        provider TEXT NOT NULL,
        model_type TEXT DEFAULT 'code_analysis',
        context_window INTEGER,
        cost_per_1k_tokens REAL DEFAULT 0.0,
        strengths TEXT,
        is_available INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        last_used TEXT,
        usage_count INTEGER DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS ai_analysis_results (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        analysis_session_id TEXT REFERENCES analysis_sessions(id) ON DELETE CASCADE,
        model_id TEXT REFERENCES ai_models(id) ON DELETE CASCADE,
        code_snippet TEXT NOT NULL,
        language TEXT,
        detected_patterns TEXT,
        complexity_score REAL,
        skill_level TEXT,
        suggestions TEXT,
        confidence_score REAL,
        processing_time REAL,
        token_usage TEXT,
        cost_estimate REAL DEFAULT 0.0,
        created_at TEXT DEFAULT (datetime('now')),
        error_message TEXT
    );

    CREATE TABLE IF NOT EXISTS model_comparisons (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        repository_id TEXT REFERENCES repositories(id) ON DELETE CASCADE,
        models_compared TEXT NOT NULL,
        analysis_type TEXT DEFAULT 'comparison',
        consensus_patterns TEXT,
        disputed_patterns TEXT,
        agreement_score REAL,
        diversity_score REAL,
        consistency_score REAL,
        performance_metrics TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        configuration TEXT
    );

    CREATE TABLE IF NOT EXISTS model_benchmarks (
        id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
        model_id TEXT REFERENCES ai_models(id) ON DELETE CASCADE,
        benchmark_name TEXT NOT NULL,
        benchmark_version TEXT DEFAULT '1.0',
        test_dataset_size INTEGER,
        accuracy_score REAL,
        precision_score REAL,
        recall_score REAL,
        f1_score REAL,
        avg_processing_time REAL,
        avg_cost_per_analysis REAL,
        pattern_detection_rate TEXT,
        false_positive_rate REAL,
        false_negative_rate REAL,
        benchmark_date TEXT DEFAULT (datetime('now')),
        notes TEXT,
        UNIQUE(model_id, benchmark_name, benchmark_version)
    );
    """

    # STEP 2: Create all indexes (AFTER TABLES EXIST)
    create_indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_repositories_url ON repositories(url);
    CREATE INDEX IF NOT EXISTS idx_repositories_status ON repositories(status);
    CREATE INDEX IF NOT EXISTS idx_commits_repo ON commits(repository_id);
    CREATE INDEX IF NOT EXISTS idx_commits_hash ON commits(hash);
    CREATE INDEX IF NOT EXISTS idx_commits_date ON commits(committed_date);
    CREATE UNIQUE INDEX IF NOT EXISTS uq_repo_commit_hash ON commits(repository_id, hash);
    CREATE INDEX IF NOT EXISTS idx_file_changes_commit ON file_changes(commit_id);
    CREATE INDEX IF NOT EXISTS idx_file_changes_language ON file_changes(language);
    CREATE INDEX IF NOT EXISTS idx_technologies_repo ON technologies(repository_id);
    CREATE INDEX IF NOT EXISTS idx_technologies_category ON technologies(category);
    CREATE UNIQUE INDEX IF NOT EXISTS uq_repo_tech ON technologies(repository_id, name, category);
    CREATE INDEX IF NOT EXISTS idx_patterns_name ON patterns(name);
    CREATE INDEX IF NOT EXISTS idx_patterns_category ON patterns(category);
    CREATE INDEX IF NOT EXISTS idx_pattern_occurrence_repo ON pattern_occurrences(repository_id);
    CREATE INDEX IF NOT EXISTS idx_pattern_occurrence_pattern ON pattern_occurrences(pattern_id);
    CREATE INDEX IF NOT EXISTS idx_pattern_occurrence_detected ON pattern_occurrences(detected_at);
    CREATE INDEX IF NOT EXISTS idx_pattern_occurrence_model ON pattern_occurrences(ai_model_used);
    CREATE INDEX IF NOT EXISTS idx_analysis_sessions_repo ON analysis_sessions(repository_id);
    CREATE INDEX IF NOT EXISTS idx_analysis_sessions_status ON analysis_sessions(status);
    CREATE INDEX IF NOT EXISTS idx_ai_model_provider ON ai_models(provider);
    CREATE INDEX IF NOT EXISTS idx_ai_model_available ON ai_models(is_available);
    CREATE INDEX IF NOT EXISTS idx_ai_models_name ON ai_models(name);
    CREATE INDEX IF NOT EXISTS idx_ai_result_session ON ai_analysis_results(analysis_session_id);
    CREATE INDEX IF NOT EXISTS idx_ai_result_model ON ai_analysis_results(model_id);
    CREATE INDEX IF NOT EXISTS idx_ai_result_created ON ai_analysis_results(created_at);
    CREATE INDEX IF NOT EXISTS idx_model_comparison_repo ON model_comparisons(repository_id);
    CREATE INDEX IF NOT EXISTS idx_model_comparison_created ON model_comparisons(created_at);
    CREATE INDEX IF NOT EXISTS idx_benchmark_model ON model_benchmarks(model_id);
    CREATE INDEX IF NOT EXISTS idx_benchmark_name ON model_benchmarks(benchmark_name);
    CREATE INDEX IF NOT EXISTS idx_benchmark_date ON model_benchmarks(benchmark_date);
    """

    try:
        with engine.begin() as connection:
            logger.info("🗄️ Step 1: Creating all tables...")

            # Execute table creation statements
            table_statements = [
                stmt.strip() for stmt in create_tables_sql.split(";") if stmt.strip()
            ]
            for stmt in table_statements:
                if stmt.strip() and "CREATE TABLE" in stmt:
                    connection.execute(text(stmt))
                    table_name = stmt.split("CREATE TABLE IF NOT EXISTS ")[1].split(
                        " "
                    )[0]
                    logger.info(f"✅ Created table: {table_name}")

            logger.info("🗄️ Step 2: Creating all indexes...")

            # Execute index creation statements
            index_statements = [
                stmt.strip() for stmt in create_indexes_sql.split(";") if stmt.strip()
            ]
            for stmt in index_statements:
                if stmt.strip():
                    connection.execute(text(stmt))
                    logger.info(f"✅ Created index")

        logger.info("✅ All tables and indexes created successfully")
        return True

    except Exception as e:
        logger.error(f"❌ Table creation failed: {e}")
        return False


def insert_default_data():
    """Insert default AI models and patterns - FIXED VERSION"""
    try:
        with engine.begin() as connection:
            # Check if data already exists
            result = connection.execute(text("SELECT COUNT(*) FROM ai_models"))
            if result.scalar() > 0:
                logger.info("⚠️ AI models already exist, skipping insert")
                return True

            # Insert AI models one by one (FIXED APPROACH)
            models_data = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "codellama:7b",
                    "display_name": "CodeLlama 7B",
                    "provider": "Ollama (Local)",
                    "context_window": 16384,
                    "cost_per_1k_tokens": 0.0,
                    "strengths": '["Fast inference", "Good for basic patterns", "Privacy-focused"]',
                    "is_available": 1,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "codellama:13b",
                    "display_name": "CodeLlama 13B",
                    "provider": "Ollama (Local)",
                    "context_window": 16384,
                    "cost_per_1k_tokens": 0.0,
                    "strengths": '["Better reasoning", "Complex pattern detection"]',
                    "is_available": 0,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "gpt-4",
                    "display_name": "GPT-4",
                    "provider": "OpenAI",
                    "context_window": 128000,
                    "cost_per_1k_tokens": 0.03,
                    "strengths": '["Exceptional reasoning", "Detailed explanations"]',
                    "is_available": 0,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "claude-3-sonnet",
                    "display_name": "Claude 3 Sonnet",
                    "provider": "Anthropic",
                    "context_window": 200000,
                    "cost_per_1k_tokens": 0.015,
                    "strengths": '["Code quality focus", "Security analysis"]',
                    "is_available": 0,
                },
            ]

            # Insert each model individually
            for model in models_data:
                connection.execute(
                    text(
                        """
                    INSERT INTO ai_models (
                        id, name, display_name, provider, model_type, 
                        context_window, cost_per_1k_tokens, strengths, 
                        is_available, usage_count
                    )
                    VALUES (
                        :id, :name, :display_name, :provider, 'code_analysis',
                        :context_window, :cost_per_1k_tokens, :strengths,
                        :is_available, 0
                    )
                """
                    ),
                    model,
                )
                logger.info(f"✅ Inserted model: {model['display_name']}")

            # Insert basic patterns
            patterns_data = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "async_await",
                    "category": "language_feature",
                    "description": "Async/await patterns",
                    "complexity_level": "intermediate",
                    "is_antipattern": 0,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "error_handling",
                    "category": "best_practice",
                    "description": "Error handling patterns",
                    "complexity_level": "intermediate",
                    "is_antipattern": 0,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "api_integration",
                    "category": "architectural",
                    "description": "API integration patterns",
                    "complexity_level": "intermediate",
                    "is_antipattern": 0,
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "functional_programming",
                    "category": "paradigm",
                    "description": "Functional programming patterns",
                    "complexity_level": "intermediate",
                    "is_antipattern": 0,
                },
            ]

            for pattern in patterns_data:
                connection.execute(
                    text(
                        """
                    INSERT INTO patterns (
                        id, name, category, description, complexity_level, is_antipattern
                    )
                    VALUES (
                        :id, :name, :category, :description, :complexity_level, :is_antipattern
                    )
                """
                    ),
                    pattern,
                )
                logger.info(f"✅ Inserted pattern: {pattern['name']}")

            logger.info("✅ All default data inserted successfully")
            return True

    except Exception as e:
        logger.error(f"❌ Failed to insert data: {e}")
        return False


def verify_setup():
    """Verify everything is set up correctly"""
    try:
        with engine.begin() as connection:
            # Count tables
            result = connection.execute(
                text(
                    """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """
                )
            )
            tables = [row[0] for row in result]

            # Count records in key tables
            counts = {}
            for table in ["repositories", "ai_models", "patterns"]:
                if table in tables:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    counts[table] = result.scalar()

            logger.info(f"📋 Tables created: {len(tables)}")
            logger.info(f"📊 Record counts: {counts}")

            # Check if we have the expected data
            success = (
                len(tables) >= 10  # Should have at least 10 tables
                and counts.get("ai_models", 0) >= 4  # Should have 4 AI models
                and counts.get("patterns", 0) >= 4  # Should have 4 patterns
            )

            if success:
                logger.info("✅ Database setup verification passed!")
            else:
                logger.warning("⚠️ Database setup verification failed")

            return success

    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False


if __name__ == "__main__":
    logger.info("🚀 Starting FINAL database setup...")

    success = True

    # Step 1: Create tables and indexes
    if not create_all_tables():
        success = False
        logger.error("❌ Failed to create tables")

    # Step 2: Insert default data
    if success and not insert_default_data():
        success = False
        logger.error("❌ Failed to insert data")

    # Step 3: Verify everything
    if success and verify_setup():
        print("\n" + "=" * 60)
        print("🎉 DATABASE SETUP COMPLETE!")
        print("=" * 60)
        print("✅ 11 tables created")
        print("✅ 30+ indexes created")
        print("✅ 4 AI models added")
        print("✅ 4 basic patterns added")
        print("✅ Multi-model columns included")
        print("\n🚀 NEXT STEPS:")
        print("1. Add routes to your main.py:")
        print(
            "   from app.api.multi_model_analysis import router as multi_model_router"
        )
        print("   app.include_router(multi_model_router)")
        print("\n2. Start server: uvicorn app.main:app --reload")
        print("\n🧠 READY FOR MULTI-MODEL AI ANALYSIS!")
    else:
        logger.error("❌ Setup failed - check logs above")
