ALTER TABLE code_analysis_results ADD COLUMN ai_model_used VARCHAR(100);
ALTER TABLE code_analysis_results ADD COLUMN model_confidence FLOAT;
ALTER TABLE code_analysis_results ADD COLUMN processing_time_ms INTEGER;
ALTER TABLE code_analysis_results ADD COLUMN token_usage JSONB;

-- New comparison tracking table
CREATE TABLE model_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    repository_id UUID REFERENCES repositories(id) ON DELETE CASCADE,
    models_compared TEXT[] NOT NULL,
    consensus_patterns TEXT[],
    disputed_patterns JSONB,
    agreement_score FLOAT CHECK (agreement_score >= 0 AND agreement_score <= 1),
    performance_metrics JSONB,
    diversity_score FLOAT,
    consistency_score FLOAT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_model_comparisons_repo ON model_comparisons(repository_id);
CREATE INDEX idx_model_comparisons_created ON model_comparisons(created_at);