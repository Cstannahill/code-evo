"""Add multi-model AI analysis support

Revision ID: add_multi_model_support
Revises: [previous_revision]
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_multi_model_support'
down_revision = None  # Replace with your latest revision
branch_labels = None
depends_on = None


def upgrade():
    """Add multi-model support tables and columns"""
    
    # Add columns to existing pattern_occurrences table
    op.add_column('pattern_occurrences', sa.Column('ai_model_used', sa.String(), nullable=True))
    op.add_column('pattern_occurrences', sa.Column('model_confidence', sa.Float(), nullable=True))
    op.add_column('pattern_occurrences', sa.Column('processing_time_ms', sa.Integer(), nullable=True))
    op.add_column('pattern_occurrences', sa.Column('token_usage', sa.JSON(), nullable=True))
    
    # Create index for ai_model_used
    op.create_index('idx_pattern_occurrence_model', 'pattern_occurrences', ['ai_model_used'])
    
    # Create ai_models table
    op.create_table(
        'ai_models',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model_type', sa.String(), nullable=True, default='code_analysis'),
        sa.Column('context_window', sa.Integer(), nullable=True),
        sa.Column('cost_per_1k_tokens', sa.Float(), nullable=True, default=0.0),
        sa.Column('strengths', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_used', sa.DateTime(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True, default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    
    # Create indexes for ai_models
    op.create_index('idx_ai_model_provider', 'ai_models', ['provider'])
    op.create_index('idx_ai_model_available', 'ai_models', ['is_available'])
    op.create_index(op.f('ix_ai_models_name'), 'ai_models', ['name'])
    
    # Create ai_analysis_results table
    op.create_table(
        'ai_analysis_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('analysis_session_id', sa.String(), nullable=True),
        sa.Column('model_id', sa.String(), nullable=True),
        sa.Column('code_snippet', sa.Text(), nullable=False),
        sa.Column('language', sa.String(), nullable=True),
        sa.Column('detected_patterns', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('complexity_score', sa.Float(), nullable=True),
        sa.Column('skill_level', sa.String(), nullable=True),
        sa.Column('suggestions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('processing_time', sa.Float(), nullable=True),
        sa.Column('token_usage', sa.JSON(), nullable=True),
        sa.Column('cost_estimate', sa.Float(), nullable=True, default=0.0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['analysis_session_id'], ['analysis_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['model_id'], ['ai_models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for ai_analysis_results
    op.create_index('idx_ai_result_session', 'ai_analysis_results', ['analysis_session_id'])
    op.create_index('idx_ai_result_model', 'ai_analysis_results', ['model_id'])
    op.create_index('idx_ai_result_created', 'ai_analysis_results', ['created_at'])
    
    # Create model_comparisons table
    op.create_table(
        'model_comparisons',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('repository_id', sa.String(), nullable=True),
        sa.Column('models_compared', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('analysis_type', sa.String(), nullable=True, default='comparison'),
        sa.Column('consensus_patterns', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('disputed_patterns', sa.JSON(), nullable=True),
        sa.Column('agreement_score', sa.Float(), nullable=True),
        sa.Column('diversity_score', sa.Float(), nullable=True),
        sa.Column('consistency_score', sa.Float(), nullable=True),
        sa.Column('performance_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('configuration', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Create indexes for model_comparisons
    op.create_index('idx_model_comparison_repo', 'model_comparisons', ['repository_id'])
    op.create_index('idx_model_comparison_created', 'model_comparisons', ['created_at'])
    op.create_index('idx_model_comparison_models', 'model_comparisons', ['models_compared'])
    
    # Create model_benchmarks table
    op.create_table(
        'model_benchmarks',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=True),
        sa.Column('benchmark_name', sa.String(), nullable=False),
        sa.Column('benchmark_version', sa.String(), nullable=True, default='1.0'),
        sa.Column('test_dataset_size', sa.Integer(), nullable=True),
        sa.Column('accuracy_score', sa.Float(), nullable=True),
        sa.Column('precision_score', sa.Float(), nullable=True),
        sa.Column('recall_score', sa.Float(), nullable=True),
        sa.Column('f1_score', sa.Float(), nullable=True),
        sa.Column('avg_processing_time', sa.Float(), nullable=True),
        sa.Column('avg_cost_per_analysis', sa.Float(), nullable=True),
        sa.Column('pattern_detection_rate', sa.JSON(), nullable=True),
        sa.Column('false_positive_rate', sa.Float(), nullable=True),
        sa.Column('false_negative_rate', sa.Float(), nullable=True),
        sa.Column('benchmark_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['model_id'], ['ai_models.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_id', 'benchmark_name', 'benchmark_version', name='uq_model_benchmark'),
    )
    
    # Create indexes for model_benchmarks
    op.create_index('idx_benchmark_model', 'model_benchmarks', ['model_id'])
    op.create_index('idx_benchmark_name', 'model_benchmarks', ['benchmark_name'])
    op.create_index('idx_benchmark_date', 'model_benchmarks', ['benchmark_date'])
    
    # Insert default AI models
    from datetime import datetime
    
    # Create a connection to insert default data
    connection = op.get_bind()
    
    # Insert default Ollama models
    default_models = [
        {
            'id': 'codellama-7b-001',
            'name': 'codellama:7b',
            'display_name': 'CodeLlama 7B',
            'provider': 'Ollama (Local)',
            'model_type': 'code_analysis',
            'context_window': 16384,
            'cost_per_1k_tokens': 0.0,
            'strengths': ['Fast inference', 'Good for basic patterns', 'Privacy-focused'],
            'is_available': True,
            'created_at': datetime.utcnow(),
            'usage_count': 0,
        },
        {
            'id': 'codellama-13b-001',
            'name': 'codellama:13b',
            'display_name': 'CodeLlama 13B',
            'provider': 'Ollama (Local)',
            'model_type': 'code_analysis',
            'context_window': 16384,
            'cost_per_1k_tokens': 0.0,
            'strengths': ['Better reasoning', 'Complex pattern detection', 'Architectural insights'],
            'is_available': False,  # Will be set to True when detected
            'created_at': datetime.utcnow(),
            'usage_count': 0,
        },
        {
            'id': 'gpt-4-001',
            'name': 'gpt-4',
            'display_name': 'GPT-4',
            'provider': 'OpenAI',
            'model_type': 'general',
            'context_window': 128000,
            'cost_per_1k_tokens': 0.03,
            'strengths': ['Exceptional reasoning', 'Detailed explanations', 'Latest patterns'],
            'is_available': False,  # Will be set based on API key
            'created_at': datetime.utcnow(),
            'usage_count': 0,
        },
        {
            'id': 'claude-3-sonnet-001',
            'name': 'claude-3-sonnet',
            'display_name': 'Claude 3 Sonnet',
            'provider': 'Anthropic',
            'model_type': 'general',
            'context_window': 200000,
            'cost_per_1k_tokens': 0.015,
            'strengths': ['Code quality focus', 'Security analysis', 'Best practices'],
            'is_available': False,  # Will be set based on API key
            'created_at': datetime.utcnow(),
            'usage_count': 0,
        },
    ]
    
    # Insert the default models
    ai_models_table = sa.table(
        'ai_models',
        sa.column('id', sa.String),
        sa.column('name', sa.String),
        sa.column('display_name', sa.String),
        sa.column('provider', sa.String),
        sa.column('model_type', sa.String),
        sa.column('context_window', sa.Integer),
        sa.column('cost_per_1k_tokens', sa.Float),
        sa.column('strengths', postgresql.ARRAY(sa.String)),
        sa.column('is_available', sa.Boolean),
        sa.column('created_at', sa.DateTime),
        sa.column('usage_count', sa.Integer),
    )
    
    for model_data in default_models:
        connection.execute(
            ai_models_table.insert().values(**model_data)
        )


def downgrade():
    """Remove multi-model support"""
    
    # Drop new tables (in reverse order due to foreign keys)
    op.drop_table('model_benchmarks')
    op.drop_table('model_comparisons')
    op.drop_table('ai_analysis_results')
    op.drop_table('ai_models')
    
    # Remove columns from existing tables
    op.drop_index('idx_pattern_occurrence_model', table_name='pattern_occurrences')
    op.drop_column('pattern_occurrences', 'token_usage')
    op.drop_column('pattern_occurrences', 'processing_time_ms')
    op.drop_column('pattern_occurrences', 'model_confidence')
    op.drop_column('pattern_occurrences', 'ai_model_used')
