#!/usr/bin/env python3
"""
Script to inspect AblationMusicActivity collection schema and content
"""

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

def main():
    print("Connecting to database...")
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    collection_name = "AblationMusicActivity"
    print(f"Checking if collection {collection_name} exists...")
    if not db.has_collection(collection_name):
        print(f"Collection {collection_name} does not exist!")
        return 1
    
    # Get a sample document to understand the schema
    print(f"Getting a sample document from {collection_name}...")
    aql_query = f"""
    FOR doc IN {collection_name}
    LIMIT 1
    RETURN doc
    """
    cursor = db.aql.execute(aql_query)
    documents = list(cursor)
    
    if not documents:
        print("No documents found in collection!")
        return 1
    
    sample_doc = documents[0]
    print("Sample document schema:")
    for key, value in sample_doc.items():
        print(f"  {key}: {type(value).__name__}")
    
    print("\nSample document content:")
    print(sample_doc)
    
    # Check for any documents with artist="Taylor Swift"
    print("\nChecking for documents with artist='Taylor Swift'...")
    aql_query = f"""
    FOR doc IN {collection_name}
    FILTER doc.artist == "Taylor Swift"
    RETURN doc
    """
    cursor = db.aql.execute(aql_query)
    documents = list(cursor)
    print(f"Found {len(documents)} documents with artist='Taylor Swift'")
    
    if documents:
        print("Sample Taylor Swift document:")
        print(documents[0])
    
    return 0

if __name__ == "__main__":
    sys.exit(main())