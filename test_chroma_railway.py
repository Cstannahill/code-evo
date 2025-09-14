#!/usr/bin/env python3
"""
Test script to validate ChromaDB configuration for Railway deployment
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_chroma_configuration():
    """Test ChromaDB configuration for Railway deployment"""
    
    print("🧪 Testing ChromaDB Configuration for Railway Deployment")
    print("=" * 60)
    
    # Test 1: Environment Detection
    print("\n1. Environment Detection:")
    railway_env = os.getenv("RAILWAY_ENVIRONMENT")
    port_env = os.getenv("PORT")
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    
    print(f"   RAILWAY_ENVIRONMENT: {railway_env}")
    print(f"   PORT: {port_env}")
    print(f"   CHROMA_HOST: {chroma_host}")
    
    is_railway = railway_env or port_env
    print(f"   Detected Railway mode: {bool(is_railway)}")
    
    # Test 2: ChromaDB Path
    print("\n2. ChromaDB Path Configuration:")
    chroma_db_path = os.getenv("CHROMA_DB_PATH", "/tmp/chroma_db")
    print(f"   CHROMA_DB_PATH: {chroma_db_path}")
    
    # Test 3: Directory Creation
    print("\n3. Directory Creation Test:")
    try:
        os.makedirs(chroma_db_path, exist_ok=True)
        print(f"   ✅ Directory created/verified: {chroma_db_path}")
        
        # Check if directory is writable
        test_file = os.path.join(chroma_db_path, "test_write.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        os.remove(test_file)
        print(f"   ✅ Directory is writable")
        
    except Exception as e:
        print(f"   ❌ Directory creation failed: {e}")
        return False
    
    # Test 4: ChromaDB Import and Client Creation
    print("\n4. ChromaDB Client Creation Test:")
    try:
        # Set telemetry environment variables
        os.environ["ANONYMIZED_TELEMETRY"] = "False"
        os.environ["CHROMA_SERVER_TELEMETRY"] = "False"
        os.environ["CHROMA_CLIENT_TELEMETRY"] = "False"
        
        import chromadb
        from chromadb.config import Settings as ChromaSettings
        
        if is_railway or chroma_host == "localhost":
            # Test embedded mode
            print("   Testing embedded ChromaDB mode...")
            client = chromadb.PersistentClient(
                path=chroma_db_path,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                    is_persistent=True,
                ),
            )
            print("   ✅ Embedded ChromaDB client created successfully")
        else:
            # Test HTTP client mode
            print("   Testing HTTP ChromaDB client mode...")
            chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
            client = chromadb.HttpClient(
                host=chroma_host,
                port=chroma_port,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                ),
            )
            print("   ✅ HTTP ChromaDB client created successfully")
        
        # Test 5: Collection Creation
        print("\n5. Collection Creation Test:")
        try:
            collection = client.get_or_create_collection(
                name="test_collection",
                metadata={"description": "Test collection for Railway deployment"}
            )
            print("   ✅ Collection created/retrieved successfully")
            
            # Test adding a document
            collection.add(
                documents=["This is a test document for Railway deployment"],
                metadatas=[{"source": "test"}],
                ids=["test_id_1"]
            )
            print("   ✅ Document added successfully")
            
            # Test querying
            results = collection.query(
                query_texts=["test document"],
                n_results=1
            )
            print("   ✅ Query executed successfully")
            print(f"   Found {len(results['documents'][0])} results")
            
        except Exception as e:
            print(f"   ❌ Collection operations failed: {e}")
            return False
            
    except ImportError as e:
        print(f"   ❌ ChromaDB import failed: {e}")
        print("   Make sure chromadb is installed: pip install chromadb")
        return False
    except Exception as e:
        print(f"   ❌ ChromaDB client creation failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! ChromaDB is ready for Railway deployment.")
    return True

def test_railway_environment():
    """Test Railway-specific environment setup"""
    print("\n🚂 Railway Environment Test:")
    print("-" * 40)
    
    # Simulate Railway environment
    os.environ["RAILWAY_ENVIRONMENT"] = "1"
    os.environ["PORT"] = "8080"
    os.environ["CHROMA_HOST"] = "localhost"
    
    print("   Simulating Railway environment...")
    print("   RAILWAY_ENVIRONMENT=1")
    print("   PORT=8080")
    print("   CHROMA_HOST=localhost")
    
    # Test the configuration logic
    is_railway = os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("PORT")
    chroma_host = os.getenv("CHROMA_HOST", "localhost")
    
    if is_railway or chroma_host == "localhost":
        print("   ✅ Railway mode detected - will use embedded ChromaDB")
        return True
    else:
        print("   ❌ Railway mode not detected")
        return False

if __name__ == "__main__":
    print("🚀 ChromaDB Railway Deployment Test")
    print("=" * 60)
    
    # Test Railway environment detection
    railway_test = test_railway_environment()
    
    # Test ChromaDB configuration
    chroma_test = test_chroma_configuration()
    
    print("\n" + "=" * 60)
    if railway_test and chroma_test:
        print("✅ All tests passed! Ready for Railway deployment.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the configuration.")
        sys.exit(1)
