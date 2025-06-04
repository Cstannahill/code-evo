"""
Migration Script: Switch to Enhanced MongoDB System
This script helps migrate from the basic MongoDB setup to the enhanced system
with comprehensive monitoring, indexing, and error handling.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import (
    initialize_enhanced_database,
    export_health_report,
)
from app.core.mongodb_config import MongoDBConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def run_migration():
    """
    Run the migration to enhanced MongoDB system
    """
    print("🚀 Starting MongoDB Enhancement Migration")
    print("=" * 50)

    try:
        # Step 1: Validate configuration
        print("\n📋 Step 1: Validating MongoDB configuration...")
        try:
            config = MongoDBConfig()
            print(f"✅ Configuration valid")
            print(f"   📊 Database: {config.database_name}")
            print(f"   🔗 Pool size: {config.min_pool_size}-{config.max_pool_size}")
            print(f"   🔍 Monitoring: {config.enable_monitoring}")
        except Exception as e:
            print(f"❌ Configuration validation failed: {e}")
            print(
                "\n💡 Please check your .env file and ensure all required MongoDB settings are present."
            )
            return False

        # Step 2: Initialize enhanced system
        print("\n🔧 Step 2: Initializing enhanced MongoDB system...")
        try:
            result = await initialize_enhanced_database()

            if result["mongodb_connected"]:
                print("✅ MongoDB connection established")
            else:
                print("❌ MongoDB connection failed")
                return False

            if result["indexes_created"]:
                index_stats = result.get("index_results", {})
                print(
                    f"✅ Indexes created: {index_stats.get('successful_indexes', 0)}/{index_stats.get('total_indexes', 0)}"
                )
            else:
                print("⚠️  Index creation had issues")

            if result["monitoring_started"]:
                print("✅ Health monitoring started")
            else:
                print("⚠️  Health monitoring not started")

        except Exception as e:
            print(f"❌ Enhanced system initialization failed: {e}")
            return False

        # Step 3: Verify health status
        print("\n🔍 Step 3: Performing health verification...")
        try:
            health_check = result.get("health_check")
            if health_check:
                overall_status = health_check.get("overall_status", "unknown")
                metrics_count = len(health_check.get("metrics", []))
                print(f"✅ Health check completed: {overall_status}")
                print(f"   📊 Metrics collected: {metrics_count}")

                # Show key metrics
                metrics = health_check.get("metrics", [])
                for metric in metrics[:5]:  # Show first 5 metrics
                    name = metric.get("name", "unknown")
                    value = metric.get("value", "N/A")
                    unit = metric.get("unit", "")
                    status = metric.get("status", "unknown")
                    print(f"   📈 {name}: {value}{unit} ({status})")

                if metrics_count > 5:
                    print(f"   ... and {metrics_count - 5} more metrics")
            else:
                print("⚠️  No health check data available")

        except Exception as e:
            print(f"⚠️  Health verification failed: {e}")

        # Step 4: Generate migration report
        print("\n📄 Step 4: Generating migration report...")
        try:
            report = await export_health_report()

            # Save report to file
            report_file = backend_dir / "mongodb_migration_report.json"
            import json

            with open(report_file, "w") as f:
                json.dump(report, f, indent=2, default=str)

            print(f"✅ Migration report saved to: {report_file}")

        except Exception as e:
            print(f"⚠️  Report generation failed: {e}")

        print("\n🎉 MongoDB Enhancement Migration Completed Successfully!")
        print("=" * 50)
        print("\n📋 Next Steps:")
        print(
            "1. Update your application imports to use 'database' instead of 'database2_enhanced' or 'database2'"
        )
        print("2. Test your application with the enhanced MongoDB system")
        print("3. Monitor the health dashboard for performance metrics")
        print("4. Consider setting up alerting based on health check results")

        return True

    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your MongoDB connection string in .env")
        print("2. Ensure MongoDB Atlas cluster is accessible")
        print("3. Verify network connectivity and firewall settings")
        print("4. Check the logs for detailed error information")
        return False


async def main():
    """Main migration function"""
    print("MongoDB Enhancement Migration Tool")
    print("This tool will migrate your application to use the enhanced MongoDB system")
    print("with comprehensive monitoring, indexing, and error handling.\n")

    # Ask for confirmation
    response = (
        input("Do you want to proceed with the migration? (y/N): ").strip().lower()
    )
    if response not in ["y", "yes"]:
        print("Migration cancelled.")
        return

    success = await run_migration()

    if success:
        print("\n✅ Migration completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Migration failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
