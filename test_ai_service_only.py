#!/usr/bin/env python3
"""
Direct AIService test for model selection
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

async def test_ai_service_directly():
    """Test AIService model selection without full app initialization"""
    print("🤖 Direct AIService Model Selection Test\n")
    
    try:
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv("backend/.env")
        
        from app.services.ai_service import AIService
        
        print("✅ AIService imported successfully")
        
        # Initialize AI service directly
        ai_service = AIService()
        print("✅ AIService initialized")
        
        # Test model selection
        selected_model = "gpt-4o-mini"
        ai_service.set_preferred_model(selected_model)
        print(f"✅ Model selected: {selected_model}")
        
        # Get status to verify
        status = ai_service.get_status()
        print(f"✅ Preferred model in status: {status.get('preferred_model')}")
        print(f"   OpenAI models available: {status.get('openai_models_available', False)}")
        
        # Test with simple code
        test_code = """
        const fetchUser = async (id) => {
            const response = await fetch(`/api/users/${id}`);
            if (!response.ok) throw new Error('Failed');
            return response.json();
        };
        """
        
        print("\n🔍 Testing pattern analysis with selected model...")
        result = await ai_service.analyze_code_pattern(test_code, "javascript")
        
        print(f"✅ Analysis completed!")
        print(f"   Model used: {result.get('model_used', 'unknown')}")
        print(f"   AI powered: {result.get('ai_powered', False)}")
        print(f"   Patterns: {result.get('combined_patterns', [])}")
        print(f"   Complexity: {result.get('complexity_score', 'N/A')}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")
        print(f"   Processing time: {result.get('processing_time', 'N/A')}s")
        
        if result.get('token_usage'):
            usage = result['token_usage']
            print(f"\n🎉 SUCCESS: OpenAI API CALLED!")
            print(f"   Input tokens: {usage.get('prompt_tokens', 0)}")
            print(f"   Output tokens: {usage.get('completion_tokens', 0)}")
            print(f"   Total tokens: {usage.get('total_tokens', 0)}")
            
            # Cost calculation for gpt-4o-mini
            total_tokens = usage.get('total_tokens', 0)
            cost = total_tokens * 0.00015 / 1000  # $0.15 per 1M tokens
            print(f"   💰 Estimated cost: ${cost:.6f}")
            print(f"\n✅ Model selection is working correctly!")
            print(f"   You should now see charges in your OpenAI usage.")
            
        else:
            print(f"\n⚠️  No token usage recorded")
            print(f"   This might indicate:")
            print(f"   1. API call failed (check logs above)")
            print(f"   2. Fallback to local model occurred")
            print(f"   3. Rate limiting or API issue")
            
        # Test quality analysis too
        print(f"\n🔍 Testing quality analysis...")
        quality_result = await ai_service.analyze_code_quality(test_code, "javascript")
        print(f"✅ Quality analysis: {quality_result.get('model_used', 'unknown')} model")
        
        if quality_result.get('token_usage'):
            print(f"   🎉 Quality analysis also used OpenAI!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ai_service_directly())