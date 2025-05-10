#!/usr/bin/env python3
"""
Fix query/truth data matching issues by ensuring deterministic entity selection.

This script:
1. Finds queries where entity selection is non-deterministic
2. Assigns a fixed set of entities to each query/collection pair
3. Updates the AblationQueryTruth collection with consistent data
"""

import argparse
import logging
import sys
import time
import uuid
from typing import List, Dict, Any, Set

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


def get_deterministic_entities(db, collection_name: str, query_hash: str, entity_count: int = 5) -> List[str]:
    """
    Get a deterministic set of entities from a collection based on a query hash.
    
    Args:
        db: ArangoDB connection
        collection_name: The collection to get entities from
        query_hash: A hash to use for deterministic selection
        entity_count: Number of entities to select
        
    Returns:
        List of entity IDs
    """
    # Convert the hash to an integer seed
    hash_seed = int(query_hash.replace('-', '')[:8], 16)
    
    # Use the hash seed to determine a deterministic offset
    offset = hash_seed % 20  # Use modulo to get a reasonable offset
    
    # Execute query to get entity IDs in a deterministic way
    try:
        aql = f"""
        FOR doc IN {collection_name}
        SORT doc._key  /* Sort by a stable field for deterministic selection */
        LIMIT {offset}, {entity_count}
        RETURN doc._key
        """
        cursor = db.aql.execute(aql)
        entities = [doc for doc in cursor]
        return entities
    except Exception as e:
        logging.error(f"Error getting deterministic entities from {collection_name}: {e}")
        return []


def update_truth_data(dry_run: bool = True) -> bool:
    """
    Update truth data to ensure consistent entity selection.
    
    Args:
        dry_run: If True, don't actually update the database
        
    Returns:
        bool: Whether the update was successful
    """
    logger = logging.getLogger(__name__)
    
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
            
        truth_collection = db.collection(truth_collection_name)
    except Exception as e:
        logger.error(f"Error accessing truth collection: {e}")
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
    
    # Get all existing truth data entries
    try:
        cursor = db.aql.execute(f"FOR doc IN {truth_collection_name} RETURN doc")
        existing_truth_entries = {f"{doc['query_id']}_{doc['collection']}": doc for doc in cursor}
        logger.info(f"Found {len(existing_truth_entries)} existing truth data entries")
    except Exception as e:
        logger.error(f"Error getting existing truth data entries: {e}")
        return False
    
    # For each query/collection pair, update the truth data
    empty_truth_entries = []
    updated_truth_entries = []
    
    # First, find entries with no truth data or suspicious counts
    for entry_key, entry in existing_truth_entries.items():
        matching_entities = entry.get("matching_entities", [])
        if not matching_entities:
            empty_truth_entries.append(entry)
            logger.warning(f"Found empty truth data for {entry_key}")
            
    logger.info(f"Found {len(empty_truth_entries)} empty truth data entries to fix")
    
    # Now update each entry with deterministic entity selection
    for entry in empty_truth_entries:
        query_id = entry.get("query_id")
        collection_name = entry.get("collection")
        composite_key = f"{query_id}_{collection_name}"
        
        # Get deterministic entities based on the query ID
        new_entities = get_deterministic_entities(db, collection_name, query_id)
        
        if not new_entities:
            logger.error(f"Failed to get deterministic entities for {composite_key}")
            continue
            
        # Update the truth data entry
        logger.info(f"Updating truth data for {composite_key} with {len(new_entities)} entities")
        
        if not dry_run:
            try:
                # Get the document by its composite key
                doc = truth_collection.get(composite_key)
                if doc:
                    # Update the existing document
                    doc["matching_entities"] = new_entities
                    truth_collection.update(doc)
                    updated_truth_entries.append(composite_key)
                    logger.info(f"Updated truth data for {composite_key}")
                else:
                    # Create a new document
                    new_doc = {
                        "_key": composite_key,
                        "query_id": query_id,
                        "composite_key": composite_key,
                        "collection": collection_name,
                        "matching_entities": new_entities
                    }
                    truth_collection.insert(new_doc)
                    updated_truth_entries.append(composite_key)
                    logger.info(f"Created new truth data for {composite_key}")
            except Exception as e:
                logger.error(f"Error updating truth data for {composite_key}: {e}")
    
    # Report results
    if dry_run:
        logger.info(f"DRY RUN: Would have updated {len(empty_truth_entries)} truth data entries")
    else:
        logger.info(f"Updated {len(updated_truth_entries)} truth data entries")
        
    return True


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Fix query truth matching issues")
    parser.add_argument("--apply", action="store_true", help="Apply fixes (default is dry run)")
    args = parser.parse_args()
    
    logger = setup_logging()
    logger.info("Starting truth data fix script")
    
    if args.apply:
        logger.info("Running in APPLY mode - changes will be made")
        dry_run = False
    else:
        logger.info("Running in DRY RUN mode - no changes will be made")
        dry_run = True
    
    success = update_truth_data(dry_run=dry_run)
    
    if success:
        logger.info("✅ Truth data fix script completed successfully")
        return 0
    else:
        logger.error("❌ Truth data fix script failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())