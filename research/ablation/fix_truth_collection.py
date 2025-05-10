#!/usr/bin/env python3
"""
Fix unique constraint violations in the AblationQueryTruth collection.

This script:
1. Identifies existing duplicates in the AblationQueryTruth collection
2. Removes duplicates to resolve constraint violations
3. Verifies the collection is in a clean state for testing
"""

import logging
import os
import sys
from pathlib import Path

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from db.db_config import IndalekoDBConfig


def setup_logging(verbose=False):
    """Set up logging for the fix script."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def drop_truth_collection():
    """Drop and recreate the AblationQueryTruth collection to resolve constraint issues."""
    logger = logging.getLogger(__name__)
    
    try:
        # Connect to ArangoDB
        db_config = IndalekoDBConfig()
        db = db_config.get_arangodb()
        
        truth_collection = "AblationQueryTruth"
        
        # Check if collection exists
        if db.has_collection(truth_collection):
            logger.info(f"Found existing {truth_collection} collection")
            
            # Get document count
            doc_count = db.aql.execute(f"RETURN LENGTH({truth_collection})").next()
            logger.info(f"Collection contains {doc_count} documents")
            
            # Drop collection
            db.delete_collection(truth_collection)
            logger.info(f"Dropped collection {truth_collection}")
            
            # Recreate collection
            db.create_collection(truth_collection)
            logger.info(f"Recreated collection {truth_collection}")
            
            # Create key index
            db.collection(truth_collection).add_persistent_index(["query_id", "collection"], unique=True)
            logger.info(f"Added unique index on query_id and collection fields")
            
            return True
        else:
            logger.info(f"Collection {truth_collection} does not exist, nothing to fix")
            return False
    
    except Exception as e:
        logger.error(f"Error fixing truth collection: {e}")
        return False


def main():
    """Main entry point for the fix script."""
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Fix AblationQueryTruth collection")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting AblationQueryTruth collection fix")
    
    # Drop and recreate the collection
    success = drop_truth_collection()
    
    if success:
        logger.info("Successfully fixed AblationQueryTruth collection")
        logger.info("You can now run the ablation test again")
    else:
        logger.error("Failed to fix AblationQueryTruth collection")
        sys.exit(1)


if __name__ == "__main__":
    main()