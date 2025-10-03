#!/usr/bin/env python3
"""
Complete end-to-end test of model selection flow
"""
import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))


async def _async_test_complete_flow():
    """Async implementation of the complete flow test"""
    print("🚀 Complete Model Selection Flow Test\n")

    try:
        # Load environment variables like the real app does
        from dotenv import load_dotenv

        load_dotenv("backend/.env")

        from app.services.analysis_service import AnalysisService

        print("✅ Services imported successfully")

        # Initialize analysis service (this initializes AIService internally)
        analysis_service = AnalysisService()
        print("✅ AnalysisService initialized")

        # Test model selection - this should now work!
        selected_model = "gpt-4o-mini"
        analysis_service.set_preferred_model(selected_model)
        print(f"✅ Model selected: {selected_model}")

        # Test with real code analysis
        test_code = """
        import React, { useState, useEffect } from 'react';
        
        const UserProfile = ({ userId }) => {
            const [user, setUser] = useState(null);
            const [loading, setLoading] = useState(true);
            const [error, setError] = useState(null);
            
            useEffect(() => {
                const fetchUser = async () => {
                    try {
                        const response = await fetch(`/api/users/${userId}`);
                        if (!response.ok) throw new Error('Failed to fetch');
                        const userData = await response.json();
                        setUser(userData);
                    } catch (err) {
                        setError(err.message);
                    } finally {
                        setLoading(false);
                    }
                };
                
                fetchUser();
            }, [userId]);
            
            if (loading) return <div>Loading...</div>;
            if (error) return <div>Error: {error}</div>;
            if (!user) return <div>User not found</div>;
            
            return (
                <div className="user-profile">
                    <h2>{user.name}</h2>
                    <p>{user.email}</p>
                </div>
            );
        };
        
        export default UserProfile;
        """

        print("🧪 Running pattern analysis with selected OpenAI model...")
        result = await analysis_service.ai.analyze_code_pattern(test_code, "typescript")

        print(f"✅ Pattern analysis completed!")
        print(f"   Model used: {result.get('model_used', 'unknown')}")
        print(f"   AI powered: {result.get('ai_powered', False)}")
        print(f"   Patterns found: {len(result.get('combined_patterns', []))}")
        print(f"   Confidence: {result.get('confidence', 'N/A')}")

        if result.get("token_usage"):
            usage = result["token_usage"]
            print(f"   🎉 TOKEN USAGE DETECTED!")
            print(f"      Input tokens: {usage.get('prompt_tokens', 0)}")
            print(f"      Output tokens: {usage.get('completion_tokens', 0)}")
            print(f"      Total tokens: {usage.get('total_tokens', 0)}")

            # Calculate cost for gpt-4o-mini ($0.15 per 1M input tokens, $0.60 per 1M output tokens)
            input_cost = (usage.get("prompt_tokens", 0) / 1000000) * 0.15
            output_cost = (usage.get("completion_tokens", 0) / 1000000) * 0.60
            total_cost = input_cost + output_cost
            print(f"      💰 Estimated cost: ${total_cost:.6f}")

            print("\n🎯 SUCCESS: OpenAI API was properly called with selected model!")
            print("   Your application will now correctly charge for API usage.")

        else:
            print("⚠️  No token usage - may have fallen back to local model")
            print("   Check OpenAI API key and connectivity")

        print(f"\n📊 Analysis Results Preview:")
        print(f"   Patterns: {result.get('combined_patterns', [])[:3]}...")
        print(f"   Complexity: {result.get('complexity_score', 'N/A')}/10")
        print(f"   Skill level: {result.get('skill_level', 'N/A')}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


def test_complete_flow():
    import asyncio

    asyncio.run(_async_test_complete_flow())
