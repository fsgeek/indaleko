#!/usr/bin/env python3
"""
Run a simple cross-collection ablation test with proper model serialization.

This script provides a focused test of the cross-collection functionality
in the ablation testing framework, with minimal setup and data generation.
"""

import json
import logging
import os
import random
import sys
import uuid

# Set up environment
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(os.path.dirname(current_path))
os.environ["INDALEKO_ROOT"] = root_path
sys.path.insert(0, root_path)

# Import required modules
from db.db_config import IndalekoDBConfig
from research.ablation.ablation_tester import AblationConfig, AblationTester
from research.ablation.models.activity import ActivityType
from research.ablation.models.location_activity import LocationActivity
from research.ablation.models.music_activity import MusicActivity
from research.ablation.registry.shared_entity_registry import SharedEntityRegistry


def setup_database():
    """Set up the database connection and test collections."""
    logger = logging.getLogger(__name__)

    try:
        # Connect to the database
        db_config = IndalekoDBConfig()
        db = db_config.get_arangodb()
        logger.info("Successfully connected to ArangoDB database")

        # Create test collections if they don't exist
        collections = [
            "AblationMusicActivity",
            "AblationLocationActivity",
            "AblationTaskActivity",
            "AblationCollaborationActivity",
        ]

        for collection_name in collections:
            if not db.has_collection(collection_name):
                db.create_collection(collection_name)
                logger.info(f"Created collection {collection_name}")

        return db, db_config

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)  # Fail-stop immediately


def generate_basic_location():
    """Generate a basic location activity."""
    location_types = ["home", "gym", "cafe", "commute", "office", "park"]
    location_type = random.choice(location_types)
    location_names = {
        "home": ["Home", "Apartment", "Living Room", "Kitchen"],
        "gym": ["Fitness Center", "Gym", "Yoga Studio", "Weight Room"],
        "cafe": ["Coffee Shop", "Café", "Bistro", "Restaurant"],
        "commute": ["Car", "Train", "Bus", "Subway"],
        "office": ["Office", "Workspace", "Co-working Space", "Conference Room"],
        "park": ["Park", "Outdoor Trail", "Beach", "Garden"],
    }

    name = random.choice(location_names.get(location_type, ["Unknown Location"]))

    # Create the location using the Pydantic model
    location = LocationActivity(
        activity_type=ActivityType.LOCATION,
        location_name=name,
        location_type=location_type,
        coordinates={"latitude": random.uniform(30.0, 45.0), "longitude": random.uniform(-120.0, -70.0)},
        device_name=random.choice(["iPhone", "Android", "Laptop", "Desktop"]),
        wifi_ssid=random.choice(["Home_WiFi", "Public_WiFi", "Office_Network", None]),
        source="ablation_synthetic_generator",
    )

    # Convert to dict with serializable values (handles UUIDs)
    return json.loads(location.model_dump_json())


def generate_basic_music(location_id=None):
    """Generate a basic music activity."""
    # Sample music data
    music_samples = [
        {"artist": "Taylor Swift", "track": "Blank Space", "album": "1989", "genre": "Pop"},
        {"artist": "Ed Sheeran", "track": "Shape of You", "album": "÷", "genre": "Pop"},
        {"artist": "Drake", "track": "Hotline Bling", "album": "Views", "genre": "Hip-Hop"},
        {"artist": "Adele", "track": "Hello", "album": "25", "genre": "Pop"},
        {"artist": "Post Malone", "track": "Circles", "album": "Hollywood's Bleeding", "genre": "Pop/Hip-Hop"},
    ]

    # Select a random sample
    music_data = random.choice(music_samples)

    # Add references if location_id is provided
    references = {}
    if location_id:
        references = {"listened_at": [location_id]}

    # Create music activity using the Pydantic model
    music = MusicActivity(
        activity_type=ActivityType.MUSIC,
        artist=music_data["artist"],
        track=music_data["track"],
        album=music_data["album"],
        genre=music_data["genre"],
        duration_seconds=random.randint(180, 420),  # 3-7 minutes
        platform=random.choice(["Spotify", "Apple Music", "YouTube Music", "Amazon Music", "Pandora"]),
        source="ablation_synthetic_generator",
        references=references,
    )

    # Convert to dict with serializable values (handles UUIDs)
    return json.loads(music.model_dump_json())


def verify_cross_collection_query(db, entities):
    """Verify the cross-collection query directly using MCP ArangoDB query tool."""
    logger = logging.getLogger(__name__)
    logger.info("Verifying cross-collection query with direct AQL via MCP")

    # Get the music and location IDs
    music_key = entities["music"]["_key"]
    location_key = entities["location"]["_key"]
    music_id = f"AblationMusicActivity/{music_key}"
    location_id = f"AblationLocationActivity/{location_key}"
    artist = entities["music"]["artist"]
    location_name = entities["location"]["location_name"]

    # Log what we're looking for
    logger.info(f"Looking for music with artist '{artist}' and location '{location_name}'")
    logger.info(f"Music ID: {music_id}")
    logger.info(f"Location ID: {location_id}")

    # Check references in music document using MCP
    try:
        # First try using the MCP tool directly
        from mcp__arango_mcp import arango_query

        # Check references in music document
        music_query = """
        FOR doc IN AblationMusicActivity
        FILTER doc._key == @music_key
        RETURN {
            _id: doc._id,
            _key: doc._key,
            artist: doc.artist,
            track: doc.track,
            references: doc.references
        }
        """

        # Use MCP tool
        music_result = arango_query(query=music_query, bindVars={"music_key": music_key})
        logger.info(f"Music document: {json.dumps(music_result, indent=2)}")

        # Check references in location document
        location_query = """
        FOR doc IN AblationLocationActivity
        FILTER doc._key == @location_key
        RETURN {
            _id: doc._id,
            _key: doc._key,
            location_name: doc.location_name,
            location_type: doc.location_type,
            references: doc.references
        }
        """
        location_result = arango_query(query=location_query, bindVars={"location_key": location_key})
        logger.info(f"Location document: {json.dumps(location_result, indent=2)}")

        # Try different query formats to see what works
        logger.info("Trying different query formats:")

        # Query 1: Direct key in references.listened_at
        query1 = """
        FOR music IN AblationMusicActivity
        FILTER music.artist == @artist
        FILTER music.references.listened_at ANY == @location_id
        RETURN music
        """
        result1 = arango_query(query=query1, bindVars={"artist": artist, "location_id": location_id})
        logger.info(f"Query 1 (direct ID in references.listened_at): {len(result1)} results")

        # Query 2: Join with location
        query2 = """
        FOR music IN AblationMusicActivity
        FILTER music.artist == @artist
        FOR location IN AblationLocationActivity
        FILTER location._id == @location_id
        FILTER music.references.listened_at ANY == location._id
        RETURN music
        """
        result2 = arango_query(query=query2, bindVars={"artist": artist, "location_id": location_id})
        logger.info(f"Query 2 (join with location): {len(result2)} results")

        # Query 3: Direct search by artist
        query3 = """
        FOR music IN AblationMusicActivity
        FILTER music.artist == @artist
        RETURN music
        """
        result3 = arango_query(query=query3, bindVars={"artist": artist})
        logger.info(f"Query 3 (direct search by artist): {len(result3)} results")

        # Query 4: Direct search by _key
        query4 = """
        FOR music IN AblationMusicActivity
        FILTER music._key == @music_key
        RETURN music
        """
        result4 = arango_query(query=query4, bindVars={"music_key": music_key})
        logger.info(f"Query 4 (direct search by _key): {len(result4)} results")

    except ImportError as ie:
        logger.warning(f"Could not import MCP tools: {ie}. Falling back to direct DB API.")

        # Check music document using direct DB API
        music_cursor = db.aql.execute(
            """
            FOR doc IN AblationMusicActivity
            FILTER doc._key == @music_key
            RETURN {
                _id: doc._id,
                _key: doc._key,
                artist: doc.artist,
                track: doc.track,
                references: doc.references
            }
            """,
            bind_vars={"music_key": music_key},
        )
        music_result = [doc for doc in music_cursor]
        logger.info(f"Music document: {json.dumps(music_result, indent=2)}")

        # Check location document using direct DB API
        location_cursor = db.aql.execute(
            """
            FOR doc IN AblationLocationActivity
            FILTER doc._key == @location_key
            RETURN {
                _id: doc._id,
                _key: doc._key,
                location_name: doc.location_name,
                location_type: doc.location_type,
                references: doc.references
            }
            """,
            bind_vars={"location_key": location_key},
        )
        location_result = [doc for doc in location_cursor]
        logger.info(f"Location document: {json.dumps(location_result, indent=2)}")

        # Try different query formats
        logger.info("Trying different query formats:")

        # Query 1: Direct key in references.listened_at
        cursor1 = db.aql.execute(
            """
            FOR music IN AblationMusicActivity
            FILTER music.artist == @artist
            FILTER music.references.listened_at ANY == @location_id
            RETURN music
            """,
            bind_vars={"artist": artist, "location_id": location_id},
        )
        result1 = [doc for doc in cursor1]
        logger.info(f"Query 1 (direct ID in references.listened_at): {len(result1)} results")

        # Query 2: Join with location
        cursor2 = db.aql.execute(
            """
            FOR music IN AblationMusicActivity
            FILTER music.artist == @artist
            FOR location IN AblationLocationActivity
            FILTER location._id == @location_id
            FILTER music.references.listened_at ANY == location._id
            RETURN music
            """,
            bind_vars={"artist": artist, "location_id": location_id},
        )
        result2 = [doc for doc in cursor2]
        logger.info(f"Query 2 (join with location): {len(result2)} results")

        # Query 3: Direct search by artist
        cursor3 = db.aql.execute(
            """
            FOR music IN AblationMusicActivity
            FILTER music.artist == @artist
            RETURN music
            """,
            bind_vars={"artist": artist},
        )
        result3 = [doc for doc in cursor3]
        logger.info(f"Query 3 (direct search by artist): {len(result3)} results")

        # Query 4: Direct search by _key
        cursor4 = db.aql.execute(
            """
            FOR music IN AblationMusicActivity
            FILTER music._key == @music_key
            RETURN music
            """,
            bind_vars={"music_key": music_key},
        )
        result4 = [doc for doc in cursor4]
        logger.info(f"Query 4 (direct search by _key): {len(result4)} results")

    return True


def generate_test_data(db, entity_registry):
    """Generate minimal test data for cross-collection queries."""
    logger = logging.getLogger(__name__)
    logger.info("Generating test data with cross-collection relationships")

    # Generate location
    location = generate_basic_location()

    # Store location using MCP if available, fallback to direct DB
    try:
        # First try with MCP
        from mcp__arango_mcp import arango_insert

        # Ensure _key is set for ArangoDB
        if "_key" not in location:
            location["_key"] = str(location["id"]).replace("-", "")

        # Insert with MCP
        arango_insert(collection="AblationLocationActivity", document=location)
        logger.info(f"Inserted location with MCP: {location['location_name']}")

    except ImportError as ie:
        logger.warning(f"Could not import MCP tools: {ie}. Falling back to direct DB API.")
        try:
            # Ensure _key is set for ArangoDB
            if "_key" not in location:
                location["_key"] = str(location["id"]).replace("-", "")

            db.collection("AblationLocationActivity").insert(location)
            logger.info(f"Inserted location with DB API: {location['location_name']}")
        except Exception as e:
            logger.error(f"Failed to insert location: {e}")
            sys.exit(1)  # Fail-stop immediately

    # Generate music with location reference
    music = generate_basic_music(f"AblationLocationActivity/{location['_key']}")

    # Store music using MCP if available, fallback to direct DB
    try:
        # First try with MCP
        from mcp__arango_mcp import arango_insert

        # Ensure _key is set for ArangoDB
        if "_key" not in music:
            music["_key"] = str(music["id"]).replace("-", "")

        # Insert with MCP
        arango_insert(collection="AblationMusicActivity", document=music)
        logger.info(f"Inserted music with MCP: {music['artist']} - {music['track']}")

    except ImportError:
        logger.warning("MCP already imported or not available. Falling back to direct DB API.")
        try:
            # Ensure _key is set for ArangoDB
            if "_key" not in music:
                music["_key"] = str(music["id"]).replace("-", "")

            db.collection("AblationMusicActivity").insert(music)
            logger.info(f"Inserted music with DB API: {music['artist']} - {music['track']}")
        except Exception as e:
            logger.error(f"Failed to insert music: {e}")
            sys.exit(1)  # Fail-stop immediately

    # Register entities in the registry
    entity_registry.register_entity("Music", f"{music['artist']} - {music['track']}", "AblationMusicActivity")

    entity_registry.register_entity("Location", location["location_name"], "AblationLocationActivity")

    # Add relationship in the registry
    music_id = uuid.UUID(music["id"])
    location_id = uuid.UUID(location["id"])
    entity_registry.add_relationship(music_id, location_id, "listened_at")

    logger.info("Test data generation complete")

    # Return the entity IDs for testing
    entities = {"location": location, "music": music}

    return entities


def run_cross_collection_ablation_test(entities):
    """Run a cross-collection ablation test."""
    logger = logging.getLogger(__name__)
    logger.info("Running cross-collection ablation test")

    # Create ablation tester
    tester = AblationTester()

    # Create test query for music + location
    query_id = uuid.uuid4()
    query_text = f"Find music I listened to at {entities['location']['location_name']}"

    # Store the truth data
    tester.store_truth_data(query_id, "AblationMusicActivity", [entities["music"]["_key"]])

    # Configure the ablation test
    config = AblationConfig(
        collections_to_ablate=["AblationMusicActivity", "AblationLocationActivity"],
        query_limit=10,
        include_metrics=True,
        include_execution_time=True,
        verbose=True,
    )

    # Run the ablation test
    results = tester.run_ablation_test(config, query_id, query_text)

    # Print the results
    logger.info("\nAblation Test Results:")
    for key, result in results.items():
        logger.info(f"{key}:")
        logger.info(f"  Found: {result.result_count}")
        logger.info(f"  Precision: {result.precision:.2f}")
        logger.info(f"  Recall: {result.recall:.2f}")
        logger.info(f"  F1: {result.f1_score:.2f}")
        logger.info(f"  Impact: {result.impact:.2f}")

    return results


def test_cross_collection_relationship(db, entities):
    """Test cross-collection relationships using direct MCP query."""
    logger = logging.getLogger(__name__)
    logger.info("Testing cross-collection relationships with MCP ArangoDB query")

    try:
        # Use MCP query directly from Claude
        from mcp__arango_mcp import arango_query

        # Get the music and location IDs
        music_key = entities["music"]["_key"]
        location_key = entities["location"]["_key"]
        location_id = f"AblationLocationActivity/{location_key}"

        # Check the references array format
        check_query = """
        FOR doc IN AblationMusicActivity
        FILTER doc._key == @music_key
        RETURN doc.references
        """
        references = arango_query(query=check_query, bindVars={"music_key": music_key})
        logger.info(f"Music references format: {json.dumps(references, indent=2)}")

        # Extract keys from all records to verify structure
        extract_keys_query = """
        FOR doc IN AblationMusicActivity
        RETURN { _id: doc._id, _key: doc._key, references: doc.references }
        """
        all_music_docs = arango_query(query=extract_keys_query, bindVars={})
        logger.info(f"All music docs (first 3): {json.dumps(all_music_docs[:3], indent=2)}")

        # Try a more explicit JOIN using proper document reference format
        explicit_join_query = """
        FOR music IN AblationMusicActivity
        LET location_refs = (
            FOR ref IN music.references.listened_at || []
            FOR loc IN AblationLocationActivity
            FILTER loc._id == ref
            RETURN loc
        )
        FILTER LENGTH(location_refs) > 0
        RETURN {
            music: music,
            locations: location_refs
        }
        """
        explicit_results = arango_query(query=explicit_join_query, bindVars={})
        logger.info(f"Explicit JOIN results: {len(explicit_results)}")
        if len(explicit_results) > 0:
            logger.info(f"First result: {json.dumps(explicit_results[0], indent=2)}")

        return True

    except ImportError as ie:
        logger.warning(f"Could not import MCP tools: {ie}. Skipping direct MCP test.")
        return False


def main():
    """Run the cross-collection test."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)

    # Set up the database
    db, db_config = setup_database()

    # Create shared entity registry
    entity_registry = SharedEntityRegistry()

    # Generate test data
    entities = generate_test_data(db, entity_registry)

    # Verify the query format first using MCP ArangoDB tools
    verify_cross_collection_query(db, entities)

    # Test cross-collection relationships directly with AQL
    test_cross_collection_relationship(db, entities)

    # Run the ablation test
    results = run_cross_collection_ablation_test(entities)

    logger.info("\nCross-collection test completed successfully")


if __name__ == "__main__":
    main()
