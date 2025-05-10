"""Fixed relationship patterns for cross-collection references in ablation testing.

This module provides relationship pattern generators that properly use Pydantic models
to ensure schema compliance when inserting documents into the database.
"""

import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Tuple, Optional

from research.ablation.models.activity import ActivityType
from research.ablation.models.music_activity import MusicActivity
from research.ablation.models.location_activity import LocationActivity
from research.ablation.models.task_activity import TaskActivity
from research.ablation.models.collaboration_activity import CollaborationActivity
from research.ablation.registry import SharedEntityRegistry
from research.ablation.models.relationship_patterns import (
    RelationshipPatternGenerator,
)


class FixedRelationshipPatternBase(RelationshipPatternGenerator):
    """Base class for fixed relationship pattern generators.

    Adds support for proper UUID handling when preparing documents for ArangoDB.
    """

    def prepare_for_arango(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare a document for insertion into ArangoDB with proper UUID handling.

        Ensures the document has a valid _key field and references
        are properly formatted for ArangoDB.

        Args:
            document: The document to prepare

        Returns:
            Dict: The prepared document
        """
        # Make a copy to avoid modifying the original
        doc = document.copy()

        # Make sure the document has a _key field (derived from id if available)
        if "id" in doc and "_key" not in doc:
            # Handle UUID objects properly by using .hex to get a string without dashes
            if isinstance(doc["id"], uuid.UUID):
                doc["_key"] = doc["id"].hex  # Use .hex instead of str().replace("-", "")
            else:
                doc["_key"] = str(doc["id"]).replace("-", "")  # Remove dashes for valid ArangoDB keys

        # Ensure references use proper _id format if needed
        if "references" in doc:
            refs = doc["references"]
            for field, values in refs.items():
                # Skip empty references
                if not values:
                    continue

                # Ensure values is a list
                if not isinstance(values, list):
                    refs[field] = [values]

        return doc


class FixedMusicLocationPattern(FixedRelationshipPatternBase):
    """Generator for Music+Location relationship patterns using Pydantic models."""

    def generate_music_at_location(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate a music activity at a specific location using proper models.

        Returns:
            Tuple: (location_data, music_data)
        """
        # Generate location data
        location_raw = self._generate_basic_location_data()
        
        # Create proper LocationActivity model instance
        location_model = LocationActivity(**location_raw)
        location = location_model.model_dump()

        # Generate music data
        music_raw = self._generate_basic_music_data()
        
        # Add references to connect entities
        if "references" not in music_raw:
            music_raw["references"] = {}
        music_raw["references"]["listened_at"] = [str(location["id"])]

        if "references" not in location:
            location["references"] = {}
        if "music_activities" not in location["references"]:
            location["references"]["music_activities"] = []
        location["references"]["music_activities"].append(music_raw["id"])

        # Create proper MusicActivity model instance
        music_model = MusicActivity(**music_raw)
        music = music_model.model_dump()

        # Register entities
        self.register_entities([location], "Location")
        self.register_entities([music], "Music")

        # Add relationships in the registry
        location_id = uuid.UUID(str(location["id"]))
        music_id = uuid.UUID(str(music["id"]))

        # Music listened at location
        self.entity_registry.add_relationship(music_id, location_id, "listened_at")

        # Location has music activity
        self.entity_registry.add_relationship(location_id, music_id, "music_activities")
        
        # Prepare documents for ArangoDB
        location = self.prepare_for_arango(location)
        music = self.prepare_for_arango(music)

        return location, music

    def _generate_basic_location_data(self) -> Dict[str, Any]:
        """
        Generate basic location data for a LocationActivity model.

        Returns:
            Dict: Location data
        """
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

        return {
            "id": self.generate_uuid(),
            "activity_type": ActivityType.LOCATION,
            "location_name": name,
            "location_type": location_type,
            "coordinates": {"latitude": random.uniform(30.0, 45.0), "longitude": random.uniform(-120.0, -70.0)},
            "device_name": random.choice(["iPhone", "Android", "Laptop", "Desktop"]),
            "wifi_ssid": random.choice(["Home_WiFi", "Public_WiFi", "Office_Network", None]),
            "source": "ablation_synthetic_generator",
            "timestamp": self.generate_timestamp(days_back=30),
            "semantic_attributes": {},
        }

    def _generate_basic_music_data(self) -> Dict[str, Any]:
        """
        Generate basic music data for a MusicActivity model.

        Returns:
            Dict: Music activity data
        """
        # Sample music data with popular artists and tracks
        music_samples = [
            {"artist": "Taylor Swift", "track": "Blank Space", "album": "1989", "genre": "Pop"},
            {"artist": "Ed Sheeran", "track": "Shape of You", "album": "÷", "genre": "Pop"},
            {"artist": "Drake", "track": "Hotline Bling", "album": "Views", "genre": "Hip-Hop"},
            {"artist": "Adele", "track": "Hello", "album": "25", "genre": "Pop"},
            {"artist": "The Weeknd", "track": "Blinding Lights", "album": "After Hours", "genre": "R&B"},
            {"artist": "Billie Eilish", "track": "Bad Guy", "album": "When We All Fall Asleep", "genre": "Alternative"},
            {"artist": "Kendrick Lamar", "track": "HUMBLE.", "album": "DAMN.", "genre": "Hip-Hop"},
            {"artist": "Dua Lipa", "track": "Don't Start Now", "album": "Future Nostalgia", "genre": "Pop"},
            {"artist": "Post Malone", "track": "Circles", "album": "Hollywood's Bleeding", "genre": "Pop/Hip-Hop"},
            {"artist": "BTS", "track": "Dynamite", "album": "BE", "genre": "K-Pop"},
        ]

        # Select a random sample
        music_data = random.choice(music_samples)

        return {
            "id": self.generate_uuid(),
            "activity_type": ActivityType.MUSIC,
            "artist": music_data["artist"],
            "track": music_data["track"],
            "album": music_data["album"],
            "genre": music_data["genre"],
            "duration_seconds": random.randint(180, 420),  # 3-7 minutes
            "platform": random.choice(["Spotify", "Apple Music", "YouTube Music", "Amazon Music", "Pandora"]),
            "source": "ablation_synthetic_generator",
            "timestamp": self.generate_timestamp(),
            "semantic_attributes": {},
        }


class FixedMusicTaskPattern(FixedRelationshipPatternBase):
    """Generator for Music+Task relationship patterns using Pydantic models."""

    def generate_music_during_task(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate music listened to during a task using proper models.

        Returns:
            Tuple: (task_data, music_data)
        """
        # Generate a basic task
        task_raw = self._generate_basic_task_data()
        
        # Create proper TaskActivity model instance
        task_model = TaskActivity(**task_raw)
        task = task_model.model_dump()

        # Generate music activity that occurred during the task
        music_raw = self._generate_basic_music_data()

        # Align timestamps (music during task)
        task_start = task["timestamp"]
        task_end = task_start + task["duration_seconds"]
        music_raw["timestamp"] = random.randint(task_start, max(task_start, task_end - music_raw["duration_seconds"]))

        # Add references to connect entities
        if "references" not in music_raw:
            music_raw["references"] = {}
        music_raw["references"]["played_during"] = [str(task["id"])]

        if "references" not in task:
            task["references"] = {}
        if "background_music" not in task["references"]:
            task["references"]["background_music"] = []
        task["references"]["background_music"].append(music_raw["id"])

        # Create proper MusicActivity model instance
        music_model = MusicActivity(**music_raw)
        music = music_model.model_dump()

        # Register entities
        self.register_entities([task], "Task")
        self.register_entities([music], "Music")

        # Add relationships in the registry
        task_id = uuid.UUID(str(task["id"]))
        music_id = uuid.UUID(str(music["id"]))

        # Music played during task
        self.entity_registry.add_relationship(music_id, task_id, "played_during")

        # Task has background music
        self.entity_registry.add_relationship(task_id, music_id, "background_music")
        
        # Prepare documents for ArangoDB
        task = self.prepare_for_arango(task)
        music = self.prepare_for_arango(music)

        return task, music

    def _generate_basic_task_data(self) -> Dict[str, Any]:
        """
        Generate basic task data for a TaskActivity model.

        Returns:
            Dict: Task data
        """
        task_types = ["coding", "writing", "reading", "design", "study", "research"]
        task_type = random.choice(task_types)
        applications = ["VS Code", "Word", "Chrome", "Figma", "PDF Reader", "Excel"]

        return {
            "id": self.generate_uuid(),
            "activity_type": ActivityType.TASK,
            "task_name": f"{task_type.title()} task",
            "application": random.choice(applications),
            "window_title": f"{task_type.title()} - Project Work",
            "duration_seconds": random.randint(1800, 7200),  # 30-120 minutes
            "active": True,
            "source": "ablation_synthetic_generator",
            "timestamp": self.generate_timestamp(),
            "semantic_attributes": {},
        }

    def _generate_basic_music_data(self) -> Dict[str, Any]:
        """
        Generate basic music data for a MusicActivity model.

        Returns:
            Dict: Music activity data
        """
        # Music genres for productivity
        productivity_music = [
            {"artist": "Lo-Fi Beats", "track": "Study Session", "album": "Focus Playlist", "genre": "Lo-Fi"},
            {"artist": "Hans Zimmer", "track": "Time", "album": "Inception", "genre": "Soundtrack"},
            {"artist": "Bonobo", "track": "Cirrus", "album": "The North Borders", "genre": "Electronic"},
            {"artist": "Tycho", "track": "Awake", "album": "Awake", "genre": "Ambient"},
            {
                "artist": "Max Richter",
                "track": "On the Nature of Daylight",
                "album": "The Blue Notebooks",
                "genre": "Classical",
            },
            {"artist": "Brian Eno", "track": "An Ending (Ascent)", "album": "Apollo", "genre": "Ambient"},
            {
                "artist": "Explosions in the Sky",
                "track": "Your Hand in Mine",
                "album": "The Earth Is Not a Cold Dead Place",
                "genre": "Post-Rock",
            },
            {"artist": "Nils Frahm", "track": "Says", "album": "Spaces", "genre": "Modern Classical"},
            {"artist": "Four Tet", "track": "Angel Echoes", "album": "There Is Love in You", "genre": "Electronic"},
            {"artist": "Ludovico Einaudi", "track": "Experience", "album": "In a Time Lapse", "genre": "Classical"},
        ]

        # Select a random sample
        music_data = random.choice(productivity_music)

        return {
            "id": self.generate_uuid(),
            "activity_type": ActivityType.MUSIC,
            "artist": music_data["artist"],
            "track": music_data["track"],
            "album": music_data["album"],
            "genre": music_data["genre"],
            "duration_seconds": random.randint(180, 600),  # 3-10 minutes
            "platform": random.choice(["Spotify", "Apple Music", "YouTube Music", "Amazon Music", "Pandora"]),
            "source": "ablation_synthetic_generator",
            "timestamp": self.generate_timestamp(),
            "semantic_attributes": {},
        }


class FixedTaskCollaborationPattern(FixedRelationshipPatternBase):
    """Generator for Task+Collaboration relationship patterns using Pydantic models."""

    def generate_meeting_with_tasks(self) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Generate a meeting with assigned tasks using proper models.

        Returns:
            Tuple: (meeting_data, list_of_tasks)
        """
        # Generate a basic meeting
        meeting_raw = self._generate_basic_meeting_data()
        
        # Create proper CollaborationActivity model instance
        meeting_model = CollaborationActivity(**meeting_raw)
        meeting = meeting_model.model_dump()
        
        tasks = []

        # Generate 1-5 tasks from this meeting
        for i in range(random.randint(1, 5)):
            task_raw = {
                "id": self.generate_uuid(),
                "activity_type": ActivityType.TASK,
                "task_name": f"Task {i+1} from {meeting['event_type']}",
                "application": "Task Management System",
                "window_title": f"{meeting['event_type']} - Task {i+1}",
                "duration_seconds": random.randint(300, 1800),
                "active": True,
                "source": "ablation_synthetic_generator",
                "timestamp": meeting["timestamp"] + random.randint(300, 1800),
                "semantic_attributes": {},
                "references": {"created_in": [str(meeting["id"])]},
            }
            
            # Create proper TaskActivity model instance
            task_model = TaskActivity(**task_raw)
            task = task_model.model_dump()
            tasks.append(task)

        # Add references to meeting
        if "references" not in meeting:
            meeting["references"] = {}
        meeting["references"]["has_tasks"] = [str(t["id"]) for t in tasks]

        # Register entities
        self.register_entities([meeting], "Collaboration")
        self.register_entities(tasks, "Task")

        # Add relationships in the registry
        meeting_id = uuid.UUID(str(meeting["id"]))
        for task in tasks:
            task_id = uuid.UUID(str(task["id"]))
            # Task was created in meeting
            self.entity_registry.add_relationship(task_id, meeting_id, "created_in")
            # Meeting has task
            self.entity_registry.add_relationship(meeting_id, task_id, "has_tasks")
            
        # Prepare documents for ArangoDB
        meeting = self.prepare_for_arango(meeting)
        prepared_tasks = [self.prepare_for_arango(task) for task in tasks]

        return meeting, prepared_tasks

    def _generate_basic_meeting_data(self) -> Dict[str, Any]:
        """
        Generate basic meeting data for a CollaborationActivity model.

        Returns:
            Dict: Meeting data
        """
        meeting_types = ["standup", "planning", "retrospective", "1on1", "team_meeting", "customer_call"]
        meeting_type = random.choice(meeting_types)

        return {
            "id": self.generate_uuid(),
            "activity_type": ActivityType.COLLABORATION,
            "platform": random.choice(["Teams", "Zoom", "Slack", "Meet"]),
            "event_type": meeting_type,
            "participants": self._generate_participants(2, 8),
            "content": f"{meeting_type} meeting with team",
            "duration_seconds": random.randint(900, 7200),  # 15-120 minutes
            "source": "ablation_synthetic_generator",
            "timestamp": self.generate_timestamp(),
            "semantic_attributes": {},
        }

    def _generate_participants(self, min_count: int = 2, max_count: int = 8) -> List[Dict[str, str]]:
        """
        Generate a list of meeting participants.

        Args:
            min_count: Minimum number of participants
            max_count: Maximum number of participants

        Returns:
            List: Participant data
        """
        participants_list = [
            {"name": "John Smith", "email": "john.smith@example.com"},
            {"name": "Jane Doe", "email": "jane.doe@example.com"},
            {"name": "Alice Johnson", "email": "alice.johnson@example.com"},
            {"name": "Bob Brown", "email": "bob.brown@example.com"},
            {"name": "Charlie Davis", "email": "charlie.davis@example.com"},
            {"name": "Diana Wilson", "email": "diana.wilson@example.com"},
            {"name": "Edward Garcia", "email": "edward.garcia@example.com"},
            {"name": "Fiona Martinez", "email": "fiona.martinez@example.com"},
            {"name": "George Lee", "email": "george.lee@example.com"},
            {"name": "Hannah Kim", "email": "hannah.kim@example.com"},
        ]

        count = random.randint(min_count, min(max_count, len(participants_list)))
        return random.sample(participants_list, count)


class FixedLocationCollaborationPattern(FixedRelationshipPatternBase):
    """Generator for Location+Collaboration relationship patterns using Pydantic models."""

    def generate_meeting_at_location(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Generate a meeting at a specific location using proper models.

        Returns:
            Tuple: (location_data, meeting_data)
        """
        # Generate a basic location
        location_raw = self._generate_basic_location_data()
        
        # Create proper LocationActivity model instance
        location_model = LocationActivity(**location_raw)
        location = location_model.model_dump()

        # Generate a meeting at this location
        meeting_raw = {
            "id": self.generate_uuid(),
            "activity_type": ActivityType.COLLABORATION,
            "platform": "In-person",
            "event_type": random.choice(["meeting", "workshop", "conference", "team_building"]),
            "participants": self._generate_participants(2, 8),
            "content": f"Meeting at {location['location_name']}",
            "duration_seconds": random.randint(1800, 7200),  # 30-120 minutes
            "source": "ablation_synthetic_generator",
            "timestamp": self.generate_timestamp(),
            "semantic_attributes": {},
            "references": {"located_at": [str(location["id"])]},
        }
        
        # Create proper CollaborationActivity model instance
        meeting_model = CollaborationActivity(**meeting_raw)
        meeting = meeting_model.model_dump()

        # Add references to location
        if "references" not in location:
            location["references"] = {}
        if "hosted_meetings" not in location["references"]:
            location["references"]["hosted_meetings"] = []
        location["references"]["hosted_meetings"].append(str(meeting["id"]))

        # Register entities
        self.register_entities([location], "Location")
        self.register_entities([meeting], "Collaboration")

        # Add relationships in the registry
        location_id = uuid.UUID(str(location["id"]))
        meeting_id = uuid.UUID(str(meeting["id"]))
        # Meeting located at location
        self.entity_registry.add_relationship(meeting_id, location_id, "located_at")
        # Location hosted meeting
        self.entity_registry.add_relationship(location_id, meeting_id, "hosted_meetings")
        
        # Prepare documents for ArangoDB
        location = self.prepare_for_arango(location)
        meeting = self.prepare_for_arango(meeting)

        return location, meeting

    def _generate_basic_location_data(self) -> Dict[str, Any]:
        """
        Generate basic location data for a LocationActivity model.

        Returns:
            Dict: Location data
        """
        location_types = ["office", "meeting_room", "conference_center", "coffee_shop", "home_office"]
        location_type = random.choice(location_types)
        location_names = {
            "office": ["Headquarters", "Downtown Office", "Tech Park Office", "Corporate Office"],
            "meeting_room": ["Board Room", "Main Conference Room", "Meeting Room A", "Collaboration Space"],
            "conference_center": ["Convention Center", "Tech Hub", "Innovation Center", "Summit Hall"],
            "coffee_shop": ["Coffee Shop", "Café Central", "Espresso Bar", "Bean & Brew"],
            "home_office": ["Home Office", "Remote Workspace", "Home Study", "Remote Setup"],
        }

        name = random.choice(location_names.get(location_type, ["Unknown Location"]))

        return {
            "id": self.generate_uuid(),
            "activity_type": ActivityType.LOCATION,
            "location_name": name,
            "location_type": location_type,
            "coordinates": {"latitude": random.uniform(30.0, 45.0), "longitude": random.uniform(-120.0, -70.0)},
            "device_name": random.choice(["iPhone", "Android", "Laptop", "Desktop"]),
            "wifi_ssid": random.choice(["Office_WiFi", "Guest_Network", "Home_Network", None]),
            "source": "ablation_synthetic_generator",
            "timestamp": self.generate_timestamp(days_back=90),  # Locations exist longer
            "semantic_attributes": {},
        }

    def _generate_participants(self, min_count: int = 2, max_count: int = 8) -> List[Dict[str, str]]:
        """
        Generate a list of meeting participants.

        Args:
            min_count: Minimum number of participants
            max_count: Maximum number of participants

        Returns:
            List: Participant data
        """
        participants_list = [
            {"name": "John Smith", "email": "john.smith@example.com"},
            {"name": "Jane Doe", "email": "jane.doe@example.com"},
            {"name": "Alice Johnson", "email": "alice.johnson@example.com"},
            {"name": "Bob Brown", "email": "bob.brown@example.com"},
            {"name": "Charlie Davis", "email": "charlie.davis@example.com"},
            {"name": "Diana Wilson", "email": "diana.wilson@example.com"},
            {"name": "Edward Garcia", "email": "edward.garcia@example.com"},
            {"name": "Fiona Martinez", "email": "fiona.martinez@example.com"},
            {"name": "George Lee", "email": "george.lee@example.com"},
            {"name": "Hannah Kim", "email": "hannah.kim@example.com"},
        ]

        count = random.randint(min_count, min(max_count, len(participants_list)))
        return random.sample(participants_list, count)