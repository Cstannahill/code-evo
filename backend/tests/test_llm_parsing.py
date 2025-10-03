import sys
import os
import pytest

# Ensure the backend package is importable when running tests from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.ai_service import AIService
from app.models.ai_models import PatternAnalysis


def test_parse_partial_llm_output_returns_fallback():
    # Create an instance without running __init__ to avoid network checks
    service = object.__new__(AIService)

    # Simulate the exact kind of partial completion the logs showed
    partial_completion = (
        "{"
        'patterns:["class_pattern", "iteration_pattern", "async_await_pattern", "large_code_block"], '
        'confidence:None complexity_score:5.0 suggestions:["Break down the large code block in `setupProgram()` into smaller, more focused functions.", "Consider adding type definitions for better maintainability.", "Use environment variables or configuration files to reduce repetition in command options.", "Implement error handling and input validation for robustness.", "Add unit tests to ensure reliability."] processing_time:None token_usage:None}'
    )
    # Use the public parser wrapper; it will attempt to parse and fall back
    result = service._parse_llm_response(partial_completion, None, None)
    assert result is not None
    assert isinstance(result, PatternAnalysis)
    # Fallback returns 'unknown' pattern or the provided patterns; ensure no exception
    assert hasattr(result, "patterns")
    assert hasattr(result, "complexity_score")
