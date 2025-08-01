#!/usr/bin/env python3
"""
Test script to verify model selection functionality
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_model_selection():
    """Test the complete model selection flow"""
    print("🧪 Testing Model Selection Flow\n")
    
    try:
        from app.services.ai_service import AIService
        from app.services.multi_model_ai_service import MultiModelAIService
        
        print("✅ Imports successful")
        
        # Initialize services
        ai_service = AIService()
        print("✅ AIService initialized")
        
        # Test model selection
        test_model = "gpt-4o-mini"  # This should trigger OpenAI API calls
        ai_service.set_preferred_model(test_model)
        print(f"✅ Model selected: {test_model}")
        
        # Get status
        status = ai_service.get_status()
        print(f"✅ Service status: {status.get('preferred_model')}")
        print(f"   Multi-model available: {status.get('multi_model_service_available')}")
        print(f"   Available models count: {status.get('available_models_count', 0)}")
        print(f"   OpenAI models available: {status.get('openai_models_available', False)}")
        
        # Test with a simple code snippet
        test_code = """
        async function fetchData(url) {
            try {
                const response = await fetch(url);
                return await response.json();
            } catch (error) {
                console.error('Error:', error);
                throw error;
            }
        }
        """
        
        print("\n🔍 Testing pattern analysis with selected model...")
        result = await ai_service.analyze_code_pattern(test_code, "javascript")
        
        print(f"✅ Analysis completed")
        print(f"   Model used: {result.get('model_used', 'unknown')}")
        print(f"   AI powered: {result.get('ai_powered', False)}")
        print(f"   Patterns found: {len(result.get('combined_patterns', []))}")
        
        if result.get('token_usage'):
            print(f"   Token usage: {result['token_usage']}")
            print("🎉 SUCCESS: OpenAI API was called!")
        else:
            print("⚠️  No token usage recorded - may have fallen back to local model")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_model_selection())