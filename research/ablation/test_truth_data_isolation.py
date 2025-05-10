#\!/usr/bin/env python3
"""Test script to isolate test/control truth data issues."""

import logging
import uuid
from pathlib import Path
import os
import sys

# Set up path
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = current_path.parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from db.db_config import IndalekoDBConfig
from research.ablation.experimental.test_control_manager import TestControlGroupManager
from research.ablation.ablation_tester import AblationTester

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("isolate_test")

# Define collections
collections = [
    "AblationTaskActivity",
    "AblationLocationActivity",
]

# 1. Set up experiment
db_config = IndalekoDBConfig()
db = db_config.get_arangodb()

# Clear existing truth data
truth_collection = "AblationQueryTruth"
if db.has_collection(truth_collection):
    db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
    logger.info(f"Cleared collection {truth_collection}")

# 2. Create test/control manager
manager = TestControlGroupManager(
    collections=collections,
    control_percentage=0.5,  # 50/50 split for clearer results
    seed=42,
)

# 3. Split collections
test_collections, control_collections = manager.assign_collections()
logger.info(f"Test collections: {test_collections}")
logger.info(f"Control collections: {control_collections}")

# 4. Create a fixed set of queries
query_texts = [
    "Find documents related to the quarterly report",
    "Show me recent files from the Seattle office",
]

# 5. Create ablation tester
tester = AblationTester()

# 6. Process each query twice - once as test collection, once as control collection
for query_text in query_texts:
    # Use the same query ID for both test and control to simulate the same query
    # being processed in different contexts
    query_id = uuid.uuid4()
    logger.info(f"Processing query: {query_text} (ID: {query_id})")

    # Process as TEST query
    logger.info(f"Processing as TEST query")
    for collection in test_collections:
        # Execute query to generate results
        results, _, _ = tester.execute_query(query_id, query_text, collection)
        logger.info(f"Query returned {len(results)} results from {collection}")

        # Explicitly store truth data to simulate what happens in the full framework
        if results:
            # In a real scenario, truth data would be derived from these results
            # Here we'll just use the first 5 document keys as our truth data
            truth_entities = [doc["_key"] for doc in results[:5]]

            # Store the truth data explicitly
            tester.store_truth_data(query_id, collection, truth_entities)
            logger.info(f"Stored truth data for {collection}: {len(truth_entities)} entities")
        else:
            # Generate synthetic truth data for testing even when no results
            # This helps identify issues with truth data storage/retrieval
            synthetic_truth = [f"synthetic_{i}" for i in range(5)]
            tester.store_truth_data(query_id, collection, synthetic_truth)
            logger.info(f"Stored synthetic truth data for {collection}: {len(synthetic_truth)} entities")

    # Process as CONTROL query - using the same query ID
    logger.info(f"Processing as CONTROL query")
    for collection in control_collections:
        # Execute query to generate results
        results, _, _ = tester.execute_query(query_id, query_text, collection)
        logger.info(f"Query returned {len(results)} results from {collection}")

        # Explicitly store truth data with the same query ID but different collection
        # In a multistage test, this might happen during different phases
        if results:
            # Truth data from control collection might differ from test
            truth_entities = [doc["_key"] for doc in results[:5]]

            # Store using the same query ID but different collection
            tester.store_truth_data(query_id, collection, truth_entities)
            logger.info(f"Stored truth data for {collection}: {len(truth_entities)} entities")
        else:
            # Different synthetic data for control group to highlight potential conflicts
            # Use different IDs to create observable differences
            synthetic_truth = [f"control_synthetic_{i}" for i in range(5)]
            tester.store_truth_data(query_id, collection, synthetic_truth)
            logger.info(f"Stored synthetic truth data for {collection}: {len(synthetic_truth)} entities")

# 7. Examine the truth data in detail
logger.info("Examining truth data in AblationQueryTruth collection:")
truth_results = db.aql.execute(
    f"""
    FOR doc IN {truth_collection}
    RETURN {{
        _key: doc._key,
        query_id: doc.query_id,
        collection: doc.collection,
        entity_count: LENGTH(doc.matching_entities),
        entities: doc.matching_entities
    }}
    """
)

for doc in truth_results:
    logger.info(f"Truth data: {doc['query_id']} / {doc['collection']} - {doc['entity_count']} entities")
    logger.info(f"  Key: {doc['_key']}")
    logger.info(f"  Entities: {doc['entities'][:3]}... (showing first 3)")

logger.info("Test complete")
