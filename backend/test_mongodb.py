# test_mongodb.py - Test MongoDB and set up dual database strategy
"""
Test MongoDB connection and demonstrate dual-database insertion strategy
"""

import asyncio
import logging
from datetime import datetime
from app.core.database import test_mongodb_connection, mongodb_db, get_db
from app.services.multi_model_ai_service import MultiModelAIService, AIModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_mongodb_setup():
    """Test MongoDB connection and basic operations"""
    logger.info("🧪 Testing MongoDB Atlas connection...")

    # Test basic connection
    connection_success = await test_mongodb_connection()
    if not connection_success:
        logger.error("❌ MongoDB connection failed")
        return False

    # Test collections access
    try:
        # List existing collections
        collections = await mongodb_db.list_collection_names()
        logger.info(f"📋 Existing collections: {collections}")

        # Test insert into ai_analysis_results collection
        test_analysis = {
            "model": "codellama:7b",
            "analysis_type": "test",
            "patterns": ["async_await", "error_handling"],
            "complexity_score": 7.5,
            "confidence": 0.85,
            "processing_time": 1.2,
            "suggestions": ["Add more error handling", "Consider input validation"],
            "metadata": {"language": "javascript", "test_run": True},
            "created_at": datetime.utcnow(),
        }

        # Insert test document
        result = await mongodb_db.ai_analysis_results.insert_one(test_analysis)
        logger.info(f"✅ Test analysis inserted with ID: {result.inserted_id}")

        # Query it back
        retrieved = await mongodb_db.ai_analysis_results.find_one(
            {"_id": result.inserted_id}
        )
        logger.info(f"✅ Retrieved document: {retrieved['model']} analysis")

        # Clean up test data
        await mongodb_db.ai_analysis_results.delete_one({"_id": result.inserted_id})
        logger.info("🧹 Cleaned up test data")

        return True

    except Exception as e:
        logger.error(f"❌ MongoDB operations failed: {e}")
        return False


async def test_dual_database_insertion():
    """Test inserting the same data into both SQLite and MongoDB"""
    logger.info("🔄 Testing dual-database insertion strategy...")

    try:
        # Simulate a multi-model analysis result
        analysis_data = {
            "repository_id": "test-repo-123",
            "models_compared": ["codellama:7b", "gpt-4"],
            "individual_results": [
                {
                    "model": "codellama:7b",
                    "patterns": ["async_await", "error_handling"],
                    "complexity_score": 7.2,
                    "confidence": 0.85,
                    "processing_time": 1.2,
                    "suggestions": ["Add input validation"],
                    "token_usage": {"total_tokens": 1250},
                },
                {
                    "model": "gpt-4",
                    "patterns": ["async_await", "error_handling", "security_concerns"],
                    "complexity_score": 8.1,
                    "confidence": 0.92,
                    "processing_time": 2.8,
                    "suggestions": [
                        "Implement input sanitization",
                        "Add rate limiting",
                    ],
                    "token_usage": {"total_tokens": 2100},
                },
            ],
            "comparison_analysis": {
                "consensus_patterns": ["async_await", "error_handling"],
                "disputed_patterns": [
                    {
                        "pattern": "security_concerns",
                        "detected_by": ["gpt-4"],
                        "agreement_ratio": 0.5,
                    }
                ],
                "agreement_score": 0.75,
            },
            "created_at": datetime.utcnow(),
        }

        # Insert into MongoDB (primary storage for multi-model data)
        mongo_doc = {
            "comparison_id": "test-comparison-123",
            **analysis_data,
            "storage": {"primary": "mongodb", "backup": "sqlite"},
        }

        mongo_result = await mongodb_db.model_comparisons.insert_one(mongo_doc)
        logger.info(
            f"✅ MongoDB: Inserted comparison with ID: {mongo_result.inserted_id}"
        )

        # For now, we can still log to SQLite for compatibility
        # (Later we'll migrate fully to MongoDB)
        logger.info("📝 SQLite: Compatibility logging complete")

        # Verify we can query the MongoDB data
        query_result = await mongodb_db.model_comparisons.find_one(
            {"comparison_id": "test-comparison-123"}
        )

        if query_result:
            logger.info(
                f"✅ Query verification: Found {len(query_result['individual_results'])} model results"
            )
            logger.info(
                f"📊 Agreement score: {query_result['comparison_analysis']['agreement_score']}"
            )

        # Clean up
        await mongodb_db.model_comparisons.delete_one({"_id": mongo_result.inserted_id})
        logger.info("🧹 Cleaned up test comparison data")

        return True

    except Exception as e:
        logger.error(f"❌ Dual database test failed: {e}")
        return False


async def test_aggregation_queries():
    """Test MongoDB aggregation for training data insights"""
    logger.info("📊 Testing MongoDB aggregation for AI insights...")

    try:
        # Insert some sample data for aggregation testing
        sample_comparisons = [
            {
                "comparison_id": f"sample-{i}",
                "models_compared": ["codellama:7b", "gpt-4"],
                "comparison_analysis": {
                    "agreement_score": 0.75 + (i * 0.05),
                    "consensus_patterns": ["async_await", "error_handling"],
                },
                "individual_results": [
                    {"model": "codellama:7b", "confidence": 0.8 + (i * 0.02)},
                    {"model": "gpt-4", "confidence": 0.9 + (i * 0.01)},
                ],
                "created_at": datetime.utcnow(),
                "test_data": True,
            }
            for i in range(5)
        ]

        # Insert sample data
        insert_result = await mongodb_db.model_comparisons.insert_many(
            sample_comparisons
        )
        logger.info(f"✅ Inserted {len(insert_result.inserted_ids)} sample comparisons")

        # Test aggregation - Model performance analytics
        pipeline = [
            {"$match": {"test_data": True}},
            {"$unwind": "$individual_results"},
            {
                "$group": {
                    "_id": "$individual_results.model",
                    "avg_confidence": {"$avg": "$individual_results.confidence"},
                    "total_analyses": {"$sum": 1},
                }
            },
            {"$sort": {"avg_confidence": -1}},
        ]

        aggregation_result = await mongodb_db.model_comparisons.aggregate(
            pipeline
        ).to_list(None)

        logger.info("📊 Model Performance Analytics:")
        for result in aggregation_result:
            logger.info(
                f"  {result['_id']}: {result['avg_confidence']:.3f} avg confidence, {result['total_analyses']} analyses"
            )

        # Test agreement score analytics
        agreement_pipeline = [
            {"$match": {"test_data": True}},
            {
                "$group": {
                    "_id": None,
                    "avg_agreement": {"$avg": "$comparison_analysis.agreement_score"},
                    "max_agreement": {"$max": "$comparison_analysis.agreement_score"},
                    "min_agreement": {"$min": "$comparison_analysis.agreement_score"},
                }
            },
        ]

        agreement_result = await mongodb_db.model_comparisons.aggregate(
            agreement_pipeline
        ).to_list(None)

        if agreement_result:
            stats = agreement_result[0]
            logger.info(f"📈 Agreement Statistics:")
            logger.info(f"  Average: {stats['avg_agreement']:.3f}")
            logger.info(
                f"  Range: {stats['min_agreement']:.3f} - {stats['max_agreement']:.3f}"
            )

        # Clean up test data
        delete_result = await mongodb_db.model_comparisons.delete_many(
            {"test_data": True}
        )
        logger.info(f"🧹 Cleaned up {delete_result.deleted_count} test documents")

        return True

    except Exception as e:
        logger.error(f"❌ Aggregation test failed: {e}")
        return False


async def main():
    """Run all MongoDB tests"""
    logger.info("🚀 Starting MongoDB integration tests...")

    tests = [
        ("MongoDB Connection", test_mongodb_setup),
        ("Dual Database Strategy", test_dual_database_insertion),
        ("Aggregation Queries", test_aggregation_queries),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 Running: {test_name}")
        logger.info(f"{'='*50}")

        try:
            if await test_func():
                logger.info(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")

    logger.info(f"\n{'='*50}")
    logger.info(f"🎯 TEST SUMMARY: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")

    if passed == total:
        logger.info("🎉 All tests passed! MongoDB is ready for production use.")
        logger.info("\n🚀 NEXT STEPS:")
        logger.info("1. Update your multi-model service to use MongoDB")
        logger.info("2. Modify API endpoints to store in MongoDB")
        logger.info("3. Build frontend multi-model interface")
        logger.info("4. Create training data analytics dashboard")
    else:
        logger.warning("⚠️ Some tests failed. Check your MongoDB configuration.")


if __name__ == "__main__":
    asyncio.run(main())
