#!/usr/bin/env python3
"""Initialize the truth data collection for ablation experiments.

This script prepares the AblationQueryTruth collection for experiments by:
1. Clearing any existing data
2. Creating the collection if it doesn't exist
3. Creating initial empty truth data entries for each activity collection
"""

import logging
import sys
import uuid
import os
import json
import subprocess

def setup_logging():
    """Set up logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )

def initialize_truth_collection():
    """Initialize the truth collection for ablation experiments."""
    logger = logging.getLogger(__name__)
    logger.info("Initializing truth collection...")
    
    try:
        # Define the activity collections
        activity_collections = [
            "AblationLocationActivity",
            "AblationTaskActivity",
            "AblationMusicActivity",
            "AblationCollaborationActivity",
            "AblationStorageActivity",
            "AblationMediaActivity",
        ]
        
        # Define the truth collection
        truth_collection = "AblationQueryTruth"
        
        # Step 1: Remove all documents from the truth collection using MCP
        logger.info(f"Clearing truth collection {truth_collection}...")
        cmd = f'''
        claude-cli mcp arango-mcp arango_query --json '{{"query": "FOR doc IN AblationQueryTruth REMOVE doc IN AblationQueryTruth"}}'
        '''
        subprocess.run(cmd, shell=True, check=True)
        logger.info(f"Cleared truth collection {truth_collection}")
        
        # Step 2: Create initial empty truth data for each activity collection
        for i, collection_name in enumerate(activity_collections):
            # Generate a unique query ID for this collection
            query_id = f"00000000-0000-0000-0000-{i+1:012d}"
            composite_key = f"init_{collection_name}"
            
            # Create a document with empty matching entities
            truth_doc = {
                "_key": composite_key,
                "query_id": query_id,
                "composite_key": composite_key,
                "matching_entities": [],
                "collection": collection_name,
            }
            
            # Insert the document using MCP
            logger.info(f"Creating empty truth data for {collection_name}...")
            cmd = f'''
            claude-cli mcp arango-mcp arango_insert --json '{{"collection": "{truth_collection}", "document": {json.dumps(truth_doc)}}}'
            '''
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Created empty truth data for {collection_name}")
        
        logger.info("Truth collection initialization complete")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize truth collection: {e}")
        return False

def main():
    """Run the script."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting truth collection initialization")
    
    success = initialize_truth_collection()
    
    if success:
        logger.info("Successfully initialized truth collection")
        sys.exit(0)
    else:
        logger.error("Failed to initialize truth collection")
        sys.exit(1)

if __name__ == "__main__":
    main()