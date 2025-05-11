#!/usr/bin/env python
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import required modules
    from research.ablation.ablation_tester import AblationTester
    from db.db_config import IndalekoDBConfig
    
    # Initialize tester
    tester = AblationTester()
    
    # Get database connection
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    # Test ID to debug
    test_uuid = "b735aff6-1e77-505c-a5c2-37d742e023ce"
    test_collection = "AblationLocationActivity"
    
    print(f"\n--- DEBUGGING TRUTH DATA ACCESS ---")
    print(f"Testing ID: {test_uuid}")
    print(f"Testing Collection: {test_collection}")
    
    # Get unified truth data directly
    unified_data = tester.get_unified_truth_data(test_uuid)
    print(f"\nUnified truth data: {'Present' if unified_data else 'None'}")
    
    if unified_data:
        print(f"Collections in unified data: {unified_data.keys()}")
        
        if test_collection in unified_data:
            entities = unified_data[test_collection]
            print(f"Entities for {test_collection}: {entities} (Length: {len(entities)})")
        else:
            print(f"WARNING: {test_collection} not found in keys")
    
    # Now try to get collection-specific truth data
    collection_data = tester.get_collection_truth_data(test_uuid, test_collection)
    print(f"\nCollection truth data: {collection_data}")
    print(f"Collection data type: {type(collection_data)}")
    print(f"Is None: {collection_data is None}")
    print(f"Is empty set: {collection_data == set()}")
    
    # Try direct database access
    print("\nDirect database lookup:")
    truth_doc = db.collection("AblationQueryTruth").get(test_uuid)
    if truth_doc:
        print(f"  Found document with key {test_uuid}")
        if "matching_entities" in truth_doc:
            print(f"  Document has matching_entities field")
            if test_collection in truth_doc["matching_entities"]:
                entities = truth_doc["matching_entities"][test_collection]
                print(f"  {test_collection} entities: {entities} (Length: {len(entities)})")
            else:
                print(f"  {test_collection} not found in matching_entities")
        else:
            print(f"  No matching_entities field in document")
    else:
        print(f"  No document found with key {test_uuid}")
    
except Exception as e:
    print(f"Error: {e}")