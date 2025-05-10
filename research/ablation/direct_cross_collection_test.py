#!/usr/bin/env python3
"""
Direct test of cross-collection query functionality using MCP tools.

This script bypasses the ablation framework to test direct AQL queries
for cross-collection relationships.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime

# Set up environment
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(os.path.dirname(current_path))
os.environ["INDALEKO_ROOT"] = root_path
sys.path.insert(0, root_path)


def generate_test_data():
    """Generate simple test data for cross-collection queries."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    try:
        # Try to import the MCP tools
        from mcp__arango_mcp import arango_insert, arango_list_collections, arango_query

        # Check available collections
        collections = arango_list_collections()
        logger.info(f"Available collections: {collections}")

        # Create test collections if needed
        test_collections = ["TestMusicActivity", "TestLocationActivity"]

        for collection in test_collections:
            if collection not in collections:
                logger.info(f"Creating collection {collection}")
                # Create collection using AQL
                create_query = f"""
                INSERT {{ _key: "test" }} INTO {collection}
                REMOVE {{ _key: "test" }} IN {collection}
                """
                arango_query(query=create_query)

        # Create location document
        location_id = str(uuid.uuid4())
        location_key = location_id.replace("-", "")
        location = {
            "_key": location_key,
            "id": location_id,
            "location_name": "Test Coffee Shop",
            "location_type": "cafe",
            "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
            "created_at": datetime.now().isoformat(),
            "device_name": "Test Device",
            "source": "direct_test",
        }

        # Insert location
        arango_insert(collection="TestLocationActivity", document=location)
        logger.info(f"Inserted location: {location['location_name']}")

        # Create multiple music documents with different reference formats
        # This will help identify which reference format works with ArangoDB

        # Format 1: Using full document ID
        music_id1 = str(uuid.uuid4())
        music_key1 = music_id1.replace("-", "")
        location_ref1 = f"TestLocationActivity/{location_key}"

        music1 = {
            "_key": music_key1,
            "id": music_id1,
            "artist": "Test Artist 1",
            "track": "Test Track - Full ID",
            "album": "Test Album",
            "genre": "Test Genre",
            "duration_seconds": 240,
            "platform": "Test Platform",
            "created_at": datetime.now().isoformat(),
            "references": {"listened_at": [location_ref1]},
            "source": "direct_test",
            "reference_format": "full_document_id",
        }

        # Format 2: Using an array of IDs
        music_id2 = str(uuid.uuid4())
        music_key2 = music_id2.replace("-", "")

        music2 = {
            "_key": music_key2,
            "id": music_id2,
            "artist": "Test Artist 2",
            "track": "Test Track - Array of IDs",
            "album": "Test Album",
            "genre": "Test Genre",
            "duration_seconds": 240,
            "platform": "Test Platform",
            "created_at": datetime.now().isoformat(),
            "listened_at_locations": [location_ref1],
            "source": "direct_test",
            "reference_format": "array_of_ids",
        }

        # Format 3: Using edge style from/to format
        music_id3 = str(uuid.uuid4())
        music_key3 = music_id3.replace("-", "")

        music3 = {
            "_key": music_key3,
            "id": music_id3,
            "artist": "Test Artist 3",
            "track": "Test Track - Edge Style",
            "album": "Test Album",
            "genre": "Test Genre",
            "duration_seconds": 240,
            "platform": "Test Platform",
            "created_at": datetime.now().isoformat(),
            "_from": f"TestMusicActivity/{music_key3}",
            "_to": location_ref1,
            "edge_type": "LISTENED_AT",
            "source": "direct_test",
            "reference_format": "edge_style",
        }

        # Format 4: Using _key instead of full ID
        music_id4 = str(uuid.uuid4())
        music_key4 = music_id4.replace("-", "")

        music4 = {
            "_key": music_key4,
            "id": music_id4,
            "artist": "Test Artist 4",
            "track": "Test Track - Key Reference",
            "album": "Test Album",
            "genre": "Test Genre",
            "duration_seconds": 240,
            "platform": "Test Platform",
            "created_at": datetime.now().isoformat(),
            "references": {"listened_at": [location_key]},
            "source": "direct_test",
            "reference_format": "key_only",
        }

        # Use music1 as the main reference for the rest of the script
        music = music1

        # Insert all music documents
        music_docs = [music1, music2, music3, music4]
        music_keys = [music_key1, music_key2, music_key3, music_key4]

        for i, doc in enumerate(music_docs):
            arango_insert(collection="TestMusicActivity", document=doc)
            logger.info(f"Inserted music {i+1}: {doc['artist']} - {doc['track']} (format: {doc['reference_format']})")

        # Verify documents were inserted
        location_check = arango_query(
            query="""
            FOR doc IN TestLocationActivity
            FILTER doc._key == @key
            RETURN doc
            """,
            bindVars={"key": location_key},
        )
        logger.info(f"Location document: {json.dumps(location_check, indent=2)}")

        # Check all music documents
        all_music = arango_query(
            query="""
            FOR doc IN TestMusicActivity
            FILTER doc.source == "direct_test"
            RETURN {
                _key: doc._key,
                artist: doc.artist,
                track: doc.track,
                reference_format: doc.reference_format,
                references: doc.references
            }
            """,
            bindVars={},
        )
        logger.info(f"All music documents: {json.dumps(all_music, indent=2)}")

        # Test different query approaches for each reference format
        logger.info("\n=== Testing queries for Format 1: Full Document ID ===")
        format1_queries = [
            {
                "name": "Direct ID reference",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "full_document_id"
                FILTER music.references.listened_at ANY == @location_id
                RETURN music
                """,
                "bind_vars": {"location_id": location_ref1},
            },
            {
                "name": "Using ANY comparison",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "full_document_id"
                FILTER @location_id IN music.references.listened_at
                RETURN music
                """,
                "bind_vars": {"location_id": location_ref1},
            },
        ]

        logger.info("\n=== Testing queries for Format 2: Array of IDs ===")
        format2_queries = [
            {
                "name": "Direct array membership",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "array_of_ids"
                FILTER @location_id IN music.listened_at_locations
                RETURN music
                """,
                "bind_vars": {"location_id": location_ref1},
            },
            {
                "name": "Using ANY comparison",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "array_of_ids"
                FILTER music.listened_at_locations ANY == @location_id
                RETURN music
                """,
                "bind_vars": {"location_id": location_ref1},
            },
        ]

        logger.info("\n=== Testing queries for Format 3: Edge Style ===")
        format3_queries = [
            {
                "name": "Using _from/_to",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "edge_style"
                FILTER music._to == @location_id
                RETURN music
                """,
                "bind_vars": {"location_id": location_ref1},
            },
        ]

        logger.info("\n=== Testing queries for Format 4: Key Only ===")
        format4_queries = [
            {
                "name": "Using _key reference",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "key_only"
                FILTER music.references.listened_at ANY == @location_key
                RETURN music
                """,
                "bind_vars": {"location_key": location_key},
            },
            {
                "name": "Using full ID in comparison",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "key_only"
                FOR loc IN TestLocationActivity
                FILTER loc._key IN music.references.listened_at
                RETURN { music: music, location: loc }
                """,
                "bind_vars": {},
            },
        ]

        # Test cross-collection JOIN formats
        logger.info("\n=== Testing Cross-Collection JOIN Patterns ===")
        join_queries = [
            {
                "name": "Explicit JOIN with subquery",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.source == "direct_test"
                LET location_refs = (
                    FOR ref IN music.references.listened_at || []
                    FOR loc IN TestLocationActivity
                    FILTER loc._id == ref OR loc._key == ref
                    RETURN loc
                )
                FILTER LENGTH(location_refs) > 0
                RETURN {
                    music: music,
                    locations: location_refs,
                    reference_format: music.reference_format
                }
                """,
                "bind_vars": {},
            },
            {
                "name": "JOIN with array handling",
                "query": """
                FOR music IN TestMusicActivity
                FILTER music.reference_format == "full_document_id"
                LET location_refs = (
                    FOR loc IN TestLocationActivity
                    FILTER CONCAT("TestLocationActivity/", loc._key) IN music.references.listened_at
                    RETURN loc
                )
                FILTER LENGTH(location_refs) > 0
                RETURN {
                    music: music,
                    locations: location_refs
                }
                """,
                "bind_vars": {},
            },
        ]

        # Combine all query groups
        all_queries = [
            {"group": "Format 1", "queries": format1_queries},
            {"group": "Format 2", "queries": format2_queries},
            {"group": "Format 3", "queries": format3_queries},
            {"group": "Format 4", "queries": format4_queries},
            {"group": "JOIN Patterns", "queries": join_queries},
        ]

        # Run each query group and log results
        for group in all_queries:
            logger.info(f"\n=== Running query group: {group['group']} ===")
            for q in group["queries"]:
                logger.info(f"\nRunning query: {q['name']}")
                try:
                    result = arango_query(query=q["query"], bindVars=q["bind_vars"])
                    logger.info(f"Results count: {len(result)}")
                    if len(result) > 0:
                        logger.info(f"First result: {json.dumps(result[0], indent=2)}")
                    else:
                        logger.info("No results found")
                except Exception as e:
                    logger.error(f"Query failed: {e}")

        # Run a final comprehensive test that combines patterns from all successful approaches
        logger.info("\n=== FINAL COMPREHENSIVE TEST ===")
        final_query = """
        // Comprehensive query that tries all reference patterns
        FOR music IN TestMusicActivity
        FILTER music.source == "direct_test"

        // Handle different reference formats
        LET has_ref = (
            // Format 1: Full document ID in references.listened_at
            (music.reference_format == "full_document_id" AND
             @location_id IN (music.references.listened_at || [])) OR

            // Format 2: Direct array of IDs
            (music.reference_format == "array_of_ids" AND
             @location_id IN (music.listened_at_locations || [])) OR

            // Format 3: Edge style with _to
            (music.reference_format == "edge_style" AND
             music._to == @location_id) OR

            // Format 4: Using key only
            (music.reference_format == "key_only" AND
             @location_key IN (music.references.listened_at || []))
        )

        FILTER has_ref

        RETURN {
            _key: music._key,
            artist: music.artist,
            track: music.track,
            reference_format: music.reference_format,
            matched_pattern: (
                music.reference_format == "full_document_id" ? "Full ID" :
                music.reference_format == "array_of_ids" ? "Array of IDs" :
                music.reference_format == "edge_style" ? "Edge Style" :
                music.reference_format == "key_only" ? "Key Only" :
                "Unknown"
            )
        }
        """

        try:
            final_result = arango_query(
                query=final_query, bindVars={"location_id": location_ref1, "location_key": location_key},
            )
            logger.info(f"Comprehensive test results: {len(final_result)}")
            logger.info(f"All matching documents: {json.dumps(final_result, indent=2)}")

            # Summary of which patterns worked best
            logger.info("\n=== SUMMARY OF WORKING PATTERNS ===")
            for item in final_result:
                logger.info(f"✅ Format {item['reference_format']} works with pattern: {item['matched_pattern']}")

        except Exception as e:
            logger.error(f"Comprehensive query failed: {e}")

        logger.info("\nCross-collection testing completed successfully")

    except ImportError as ie:
        logger.error(f"Failed to import MCP tools: {ie}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_test_data()
