#!/usr/bin/env python3
"""
Test script specifically for the store_unified_truth_data method.
"""

import logging
import sys
import uuid
from pathlib import Path
import os

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from research.ablation.ablation_tester import AblationTester

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_store_truth_data")

def main():
    """Test the store_unified_truth_data method."""
    try:
        logger.info("Creating AblationTester")
        tester = AblationTester()
        
        # Get a list of collections to test with
        collections = []
        logger.info("Checking for collections")
        for collection_name in [
            "AblationMusicActivity",
            "AblationLocationActivity",
            "AblationTaskActivity",
            "AblationCollaborationActivity",
            "AblationStorageActivity",
            "AblationMediaActivity"
        ]:
            if tester.db.has_collection(collection_name):
                collections.append(collection_name)
                logger.info(f"Found collection: {collection_name}")
        
        if not collections:
            logger.error("No ablation collections found")
            return 1
            
        # Get a test collection
        test_collection = collections[0]
        logger.info(f"Using collection: {test_collection}")
        
        # Get a few entities from the collection
        logger.info(f"Getting entities from collection: {test_collection}")
        aql_query = f"""
        FOR doc IN {test_collection}
        LIMIT 5
        RETURN doc._key
        """
        cursor = tester.db.aql.execute(aql_query)
        entity_keys = list(cursor)
        logger.info(f"Found entities: {entity_keys}")
        
        # Generate a query ID
        query_id = uuid.uuid4()
        logger.info(f"Generated query ID: {query_id}")
        
        # Create unified truth data
        unified_truth_data = {
            test_collection: entity_keys
        }
        logger.info(f"Created unified truth data: {unified_truth_data}")
        
        # Store the truth data
        logger.info("Storing unified truth data")
        try:
            result = tester.store_unified_truth_data(query_id, unified_truth_data)
            logger.info(f"Result: {result}")
        except Exception as e:
            logger.error(f"Exception storing truth data: {str(e)}")
            logger.exception("Traceback:")
            return 1
            
        # Try to verify the truth data was stored
        logger.info("Verifying truth data was stored")
        try:
            truth_doc = tester.db.collection(tester.TRUTH_COLLECTION).get(str(query_id))
            if truth_doc:
                logger.info(f"Successfully retrieved truth document by key: {truth_doc}")
            else:
                logger.warning(f"Could not retrieve truth document by key")
                # Try an alternative lookup
                aql_query = f"""
                FOR doc IN {tester.TRUTH_COLLECTION}
                FILTER doc.query_id == @query_id
                RETURN doc
                """
                cursor = tester.db.aql.execute(aql_query, bind_vars={"query_id": str(query_id)})
                results = list(cursor)
                if results:
                    logger.info(f"Found truth document by query: {results[0]}")
                else:
                    logger.error("Could not find truth document by query")
                    return 1
        except Exception as e:
            logger.error(f"Exception verifying truth data: {str(e)}")
            logger.exception("Traceback:")
            return 1
            
        # Try to retrieve collection truth data
        logger.info("Retrieving collection truth data")
        try:
            truth_data = tester.get_collection_truth_data(query_id, test_collection)
            logger.info(f"Retrieved collection truth data: {truth_data}")
        except Exception as e:
            logger.error(f"Exception retrieving collection truth data: {str(e)}")
            logger.exception("Traceback:")
            return 1
            
        logger.info("Test completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected exception: {str(e)}")
        logger.exception("Traceback:")
        return 1

if __name__ == "__main__":
    sys.exit(main())