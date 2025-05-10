#!/usr/bin/env python3
"""
Run a simple cross-collection ablation test with proper model serialization.

This script provides a focused test of the cross-collection functionality
in the ablation testing framework, with minimal setup and data generation.
"""

import logging
import os
import sys
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any

# Set up environment
current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.dirname(os.path.dirname(current_path))
os.environ["INDALEKO_ROOT"] = root_path
sys.path.insert(0, root_path)

# Import required modules
from research.ablation.models.music_activity import MusicActivity
from research.ablation.models.location_activity import LocationActivity
from research.ablation.models.task_activity import TaskActivity
from research.ablation.models.activity import ActivityType
from research.ablation.registry.shared_entity_registry import SharedEntityRegistry
from research.ablation.ablation_tester import AblationTester, AblationConfig
from db.db_config import IndalekoDBConfig


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
            "AblationCollaborationActivity"
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
        source="ablation_synthetic_generator"
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
        references=references
    )
    
    # Convert to dict with serializable values (handles UUIDs)
    return json.loads(music.model_dump_json())


def generate_test_data(db, entity_registry):
    """Generate minimal test data for cross-collection queries."""
    logger = logging.getLogger(__name__)
    logger.info("Generating test data with cross-collection relationships")
    
    # Generate location
    location = generate_basic_location()
    
    # Store location
    try:
        # Ensure _key is set for ArangoDB
        if "_key" not in location:
            location["_key"] = str(location["id"]).replace("-", "")
            
        db.collection("AblationLocationActivity").insert(location)
        logger.info(f"Inserted location: {location['location_name']}")
    except Exception as e:
        logger.error(f"Failed to insert location: {e}")
        sys.exit(1)  # Fail-stop immediately
    
    # Generate music with location reference
    music = generate_basic_music(location["id"])
    
    # Store music
    try:
        # Ensure _key is set for ArangoDB
        if "_key" not in music:
            music["_key"] = str(music["id"]).replace("-", "")
            
        db.collection("AblationMusicActivity").insert(music)
        logger.info(f"Inserted music: {music['artist']} - {music['track']}")
    except Exception as e:
        logger.error(f"Failed to insert music: {e}")
        sys.exit(1)  # Fail-stop immediately
    
    # Register entities in the registry
    entity_registry.register_entity(
        "Music", 
        f"{music['artist']} - {music['track']}", 
        "AblationMusicActivity"
    )
    
    entity_registry.register_entity(
        "Location", 
        location["location_name"], 
        "AblationLocationActivity"
    )
    
    # Add relationship in the registry
    music_id = uuid.UUID(music["id"])
    location_id = uuid.UUID(location["id"])
    entity_registry.add_relationship(music_id, location_id, "listened_at")
    
    logger.info("Test data generation complete")
    
    # Return the entity IDs for testing
    entities = {
        "location": location,
        "music": music
    }
    
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
    tester.store_truth_data(
        query_id,
        "AblationMusicActivity",
        [entities["music"]["_key"]]
    )
    
    # Configure the ablation test
    config = AblationConfig(
        collections_to_ablate=[
            "AblationMusicActivity",
            "AblationLocationActivity"
        ],
        query_limit=10,
        include_metrics=True,
        include_execution_time=True,
        verbose=True
    )
    
    # Run the ablation test
    results = tester.run_ablation_test(config, query_id, query_text)
    
    # Print the results
    logger.info("\nAblation Test Results:")
    for key, result in results.items():
        logger.info(f"{key}:")
        logger.info(f"  Found: {len(result.results)}")
        logger.info(f"  Precision: {result.metrics.precision:.2f}")
        logger.info(f"  Recall: {result.metrics.recall:.2f}")
        logger.info(f"  F1: {result.metrics.f1:.2f}")
    
    return results


def main():
    """Run the cross-collection test."""
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger(__name__)
    
    # Import random here to avoid module-level dependency
    import random
    
    # Set up the database
    db, db_config = setup_database()
    
    # Create shared entity registry
    entity_registry = SharedEntityRegistry()
    
    # Generate test data
    entities = generate_test_data(db, entity_registry)
    
    # Run the ablation test
    results = run_cross_collection_ablation_test(entities)
    
    logger.info("\nCross-collection test completed successfully")


if __name__ == "__main__":
    main()