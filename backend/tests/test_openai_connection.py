#!/usr/bin/env python3
"""
Test OpenAI API connectivity
"""
import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_openai_api():
    """Test basic OpenAI API connectivity"""
    print("🔑 Testing OpenAI API Connection\n")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False
        
    if len(api_key) < 20:
        print("❌ OPENAI_API_KEY appears to be invalid (too short)")
        return False
        
    print(f"✅ API Key found: {api_key[:10]}...")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Test with a very simple request
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'Hello' in JSON format: {\"greeting\": \"Hello\"}"}
            ],
            temperature=0.1,
            max_tokens=50,
        )
        
        print("✅ OpenAI API call successful!")
        print(f"   Response: {response.choices[0].message.content}")
        print(f"   Tokens used: {response.usage.total_tokens}")
        print(f"   Cost estimate: ${response.usage.total_tokens * 0.00015 / 1000:.6f}")
        
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API call failed: {e}")
        return False

if __name__ == "__main__":
    test_openai_api()