#!/usr/bin/env python3
"""
Verify truth data integrity for ablation tests.

This script checks that all truth data entries reference valid entities
and that we have proper scientific metrics data.
"""

import argparse
import logging
import sys
from typing import List, Dict, Any, Set
import uuid

from db.db_config import IndalekoDBConfig


def setup_logging():
    """Set up logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )
    return logging.getLogger(__name__)


def check_truth_data_integrity(logger) -> bool:
    """
    Check the integrity of the truth data.
    
    Specifically:
    1. Check that each truth data entry points to valid entities
    2. Count the number of unique query/collection pairs
    3. Verify we have truth data for all collections
    
    Returns:
        bool: Whether the truth data is valid
    """
    # Connect to the database
    try:
        db_config = IndalekoDBConfig()
        db = db_config.get_arangodb()
        logger.info("Successfully connected to ArangoDB database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return False
        
    # Get the truth collection
    truth_collection_name = "AblationQueryTruth"
    try:
        if not db.has_collection(truth_collection_name):
            logger.error(f"Truth collection {truth_collection_name} does not exist")
            return False
    except Exception as e:
        logger.error(f"Error checking truth collection: {e}")
        return False
        
    # Get all ablation collections
    ablation_collections = []
    for collection_name in db.collections():
        if collection_name.startswith("Ablation") and "Activity" in collection_name:
            ablation_collections.append(collection_name)
    
    if not ablation_collections:
        logger.error("No ablation collections found")
        return False
        
    logger.info(f"Found {len(ablation_collections)} ablation collections: {ablation_collections}")
    
    # Get all truth data entries
    try:
        cursor = db.aql.execute(f"FOR doc IN {truth_collection_name} RETURN doc")
        truth_entries = list(cursor)
        logger.info(f"Found {len(truth_entries)} truth data entries")
    except Exception as e:
        logger.error(f"Error getting truth data entries: {e}")
        return False
        
    # Check the integrity of each truth data entry
    is_valid = True
    entry_counts_by_collection = {}
    missing_entities_by_collection = {}
    query_ids = set()
    
    for entry in truth_entries:
        # Get the collection and query_id
        collection_name = entry.get("collection")
        query_id = entry.get("query_id")
        matching_entities = entry.get("matching_entities", [])
        
        if not collection_name:
            logger.error(f"Missing collection name in truth entry: {entry}")
            is_valid = False
            continue
            
        if not query_id:
            logger.error(f"Missing query_id in truth entry: {entry}")
            is_valid = False
            continue
            
        # Add to counts
        entry_counts_by_collection[collection_name] = entry_counts_by_collection.get(collection_name, 0) + 1
        query_ids.add(query_id)
        
        # Check that all entities exist in the referenced collection
        if not db.has_collection(collection_name):
            logger.error(f"Collection {collection_name} referenced by truth entry does not exist")
            is_valid = False
            continue
            
        # Initialize missing entities tracking if needed
        if collection_name not in missing_entities_by_collection:
            missing_entities_by_collection[collection_name] = []
            
        # Check each entity reference
        missing_entities = []
        for entity_id in matching_entities:
            try:
                # Try to get the entity by its key
                entity_exists = db.collection(collection_name).has(entity_id)
                if not entity_exists:
                    missing_entities.append(entity_id)
            except Exception as e:
                logger.error(f"Error checking entity {entity_id} in {collection_name}: {e}")
                is_valid = False
                continue
                
        # If we found missing entities, track them
        if missing_entities:
            missing_entities_by_collection[collection_name].extend(missing_entities)
            logger.warning(f"Found {len(missing_entities)} missing entities in collection {collection_name} for query {query_id}")
            is_valid = False
    
    # Report on the integrity check
    logger.info(f"Found {len(query_ids)} unique query IDs")
    logger.info("Truth data counts by collection:")
    for collection_name, count in entry_counts_by_collection.items():
        logger.info(f"  {collection_name}: {count} entries")
        
    # Check we have truth data for all collections
    for collection_name in ablation_collections:
        if collection_name not in entry_counts_by_collection:
            logger.error(f"No truth data entries for collection {collection_name}")
            is_valid = False
            
    # Report on missing entities
    for collection_name, missing_entities in missing_entities_by_collection.items():
        if missing_entities:
            logger.error(f"Collection {collection_name} has {len(missing_entities)} missing entities: {missing_entities[:10]}...")
            is_valid = False
            
    # Report on queries per collection - more useful statistics
    queries_by_collection = {}
    for entry in truth_entries:
        collection_name = entry.get("collection")
        query_id = entry.get("query_id")
        
        if collection_name not in queries_by_collection:
            queries_by_collection[collection_name] = set()
            
        queries_by_collection[collection_name].add(query_id)
        
    logger.info("Unique queries by collection:")
    for collection_name, query_set in queries_by_collection.items():
        logger.info(f"  {collection_name}: {len(query_set)} unique queries")
    
    # Check entity count statistics - may help diagnose issues
    entity_counts_by_collection = {}
    for entry in truth_entries:
        collection_name = entry.get("collection")
        matching_entities = entry.get("matching_entities", [])
        
        if collection_name not in entity_counts_by_collection:
            entity_counts_by_collection[collection_name] = []
            
        entity_counts_by_collection[collection_name].append(len(matching_entities))
    
    logger.info("Truth entity count statistics by collection:")
    for collection_name, counts in entity_counts_by_collection.items():
        if counts:
            avg_count = sum(counts) / len(counts)
            min_count = min(counts)
            max_count = max(counts)
            logger.info(f"  {collection_name}: avg={avg_count:.1f}, min={min_count}, max={max_count}, total={sum(counts)}")
            
            # Flag potential issues with empty truth data
            zero_counts = sum(1 for count in counts if count == 0)
            if zero_counts > 0:
                logger.warning(f"  {collection_name} has {zero_counts} entries with no matching entities!")
                is_valid = False
    
    return is_valid
    

def main():
    """Main entry point for the script."""
    logger = setup_logging()
    logger.info("Starting truth data integrity check")
    
    is_valid = check_truth_data_integrity(logger)
    
    if is_valid:
        logger.info("✅ Truth data integrity check passed")
        return 0
    else:
        logger.error("❌ Truth data integrity check failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())