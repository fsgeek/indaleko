#!/usr/bin/env python3
"""
Enhanced query generator for the Indaleko ablation study.

This module provides advanced query generation functionality that targets
specific activity metadata types for ablation testing.

Project Indaleko
Copyright (C) 2024-2025 Tony Mason
"""

import os
import sys
import random
import logging
import json
import datetime
import uuid
from typing import Dict, List, Any, Optional, Set, Union
from dataclasses import dataclass

# Add the Indaleko root to the path
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, "Indaleko.py")):
        current_path = os.path.dirname(current_path)
    os.environ["INDALEKO_ROOT"] = current_path
    sys.path.append(current_path)

# Import Indaleko modules
from tools.data_generator_enhanced.testing.cluster_generator import ActivitySource

# Import LLM client
def import_llm_connector():
    """Import LLM client following strict fail-stop principles."""
    # Import the working client directly
    from research.ablation.query.enhanced.llm_client import SimpleLLMClient

    # Return a dictionary for backwards compatibility with the rest of the code
    # This ensures we use the properly working client instead of broken connectors
    return {"anthropic": SimpleLLMClient, "openai": SimpleLLMClient}


@dataclass
class QueryTemplate:
    """Template for generating natural language queries."""
    
    template: str
    categories: List[str]
    placeholders: Dict[str, List[str]]
    description: str = ""
    
    def __post_init__(self):
        """Validate the template after initialization."""
        # Check that all placeholders in the template have values
        for placeholder in self._get_template_placeholders():
            if placeholder not in self.placeholders:
                raise ValueError(f"Missing values for placeholder '{placeholder}' in template")
    
    def _get_template_placeholders(self) -> List[str]:
        """Extract placeholders from the template string.
        
        Returns:
            List of placeholder names
        """
        import re
        pattern = r'\[([^\]]+)\]'
        return re.findall(pattern, self.template)
    
    def fill(self, fixed_values: Dict[str, str] = None) -> str:
        """Fill the template with random values.
        
        Args:
            fixed_values: Dictionary of fixed values for specific placeholders
        
        Returns:
            Filled query string
        """
        fixed_values = fixed_values or {}
        result = self.template
        
        for placeholder in self._get_template_placeholders():
            if placeholder in fixed_values:
                value = fixed_values[placeholder]
            else:
                value = random.choice(self.placeholders[placeholder])
            
            result = result.replace(f"[{placeholder}]", value)
        
        return result


class QueryGenerator:
    """Generator for natural language queries targeting specific metadata types."""
    
    def __init__(self, seed: int = None):
        """Initialize the query generator.
        
        Args:
            seed: Random seed for reproducible results (default: None)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Set random seed if provided
        if seed is not None:
            random.seed(seed)
            self.logger.info(f"QueryGenerator initialized with seed {seed}")
        else:
            self.logger.info("QueryGenerator initialized with system random seed")
        
        # Initialize templates
        self._initialize_templates()
    
    def _initialize_templates(self):
        """Initialize query templates for different activity types."""
        # Define common placeholders
        file_types = ["documents", "PDF files", "Excel files", "Word documents", 
                     "presentations", "images", "spreadsheets", "text files"]
        
        actions = ["worked on", "edited", "created", "viewed", "shared", 
                  "commented on", "deleted", "opened", "modified"]
        
        time_periods = ["yesterday", "last week", "last month", "this morning",
                       "on Monday", "during the weekend", "in January",
                       "between 2 and 4 PM", "after lunch"]
        
        locations = ["at home", "in Seattle", "at the office", "in the conference room",
                    "at Starbucks", "while traveling", "in New York", "at the airport"]
        
        collaborators = ["with John", "shared with the marketing team", 
                        "with colleagues", "with external partners",
                        "during the team meeting", "with my manager"]
        
        keywords = ["budget", "quarterly report", "project plan", "marketing strategy",
                   "financial analysis", "presentation", "meeting notes", "conference"]
        
        tools = ["in Microsoft Word", "using PowerPoint", "in Excel", 
                "with Adobe Acrobat", "in Google Docs", "using Notepad"]
        
        music = ["while listening to Spotify", "while playing music", 
                "with jazz playing", "with my playlist running",
                "while listening to Taylor Swift", "with background music"]
        
        temperatures = ["when it was hot", "during the cold spell", 
                       "while the heat was on", "with the air conditioning running"]
        
        calendars = ["during my meeting", "before the conference call", 
                    "after our standup", "while I was in the quarterly review",
                    "during my lunch break", "while in the team sync"]
        
        social_media = ["while checking Twitter", "after posting on LinkedIn",
                       "while browsing Facebook", "during my Instagram session",
                       "after sharing on social media"]
        
        # Initialize template groups
        self.templates = {
            "temporal": [
                QueryTemplate(
                    template="Find [file_type] I [action] [time_period]",
                    categories=["temporal", "activity"],
                    placeholders={
                        "file_type": file_types,
                        "action": actions,
                        "time_period": time_periods
                    },
                    description="Basic temporal query"
                ),
                QueryTemplate(
                    template="Show me [file_type] created [time_period]",
                    categories=["temporal", "content"],
                    placeholders={
                        "file_type": file_types,
                        "time_period": time_periods
                    },
                    description="Content creation with time period"
                ),
                QueryTemplate(
                    template="List files I accessed [time_period] that contain [keyword]",
                    categories=["temporal", "activity", "content"],
                    placeholders={
                        "time_period": time_periods,
                        "keyword": keywords
                    },
                    description="Temporal access with content filtering"
                )
            ],
            "activity": [
                QueryTemplate(
                    template="Find [file_type] I [action] [tool]",
                    categories=["activity", "content"],
                    placeholders={
                        "file_type": file_types,
                        "action": actions,
                        "tool": tools
                    },
                    description="Activity with specific tool"
                ),
                QueryTemplate(
                    template="Show me files I [action] [collaborator]",
                    categories=["activity", "collaborator"],
                    placeholders={
                        "action": actions,
                        "collaborator": collaborators
                    },
                    description="Activity with collaborator"
                ),
                QueryTemplate(
                    template="What [file_type] did I [action] [calendar]?",
                    categories=["activity", "temporal", "calendar"],
                    placeholders={
                        "file_type": file_types,
                        "action": actions,
                        "calendar": calendars
                    },
                    description="Activity during calendar event"
                )
            ],
            "spatial": [
                QueryTemplate(
                    template="Find [file_type] I [action] [location]",
                    categories=["spatial", "activity", "content"],
                    placeholders={
                        "file_type": file_types,
                        "action": actions,
                        "location": locations
                    },
                    description="Activity at specific location"
                ),
                QueryTemplate(
                    template="Show me files accessed [location] [time_period]",
                    categories=["spatial", "temporal"],
                    placeholders={
                        "location": locations,
                        "time_period": time_periods
                    },
                    description="Location with time period"
                ),
                QueryTemplate(
                    template="Find documents I created [location] about [keyword]",
                    categories=["spatial", "content", "activity"],
                    placeholders={
                        "location": locations,
                        "keyword": keywords
                    },
                    description="Content creation at location"
                )
            ],
            "music": [
                QueryTemplate(
                    template="Find [file_type] I [action] [music]",
                    categories=["activity", "ambient", "music"],
                    placeholders={
                        "file_type": file_types,
                        "action": actions,
                        "music": music
                    },
                    description="Activity with music context"
                ),
                QueryTemplate(
                    template="Show me files I worked on [music] [time_period]",
                    categories=["ambient", "temporal", "music"],
                    placeholders={
                        "music": music,
                        "time_period": time_periods
                    },
                    description="Music with time period"
                ),
                QueryTemplate(
                    template="Find documents I edited [music] [location]",
                    categories=["ambient", "spatial", "music"],
                    placeholders={
                        "music": music,
                        "location": locations
                    },
                    description="Music with location"
                )
            ],
            "environmental": [
                QueryTemplate(
                    template="Find [file_type] I [action] [temperature]",
                    categories=["activity", "ambient", "environmental"],
                    placeholders={
                        "file_type": file_types,
                        "action": actions,
                        "temperature": temperatures
                    },
                    description="Activity with temperature context"
                ),
                QueryTemplate(
                    template="Show me files I worked on [temperature] [time_period]",
                    categories=["ambient", "temporal", "environmental"],
                    placeholders={
                        "temperature": temperatures,
                        "time_period": time_periods
                    },
                    description="Temperature with time period"
                ),
                QueryTemplate(
                    template="Find documents I edited [temperature] [location]",
                    categories=["ambient", "spatial", "environmental"],
                    placeholders={
                        "temperature": temperatures,
                        "location": locations
                    },
                    description="Temperature with location"
                )
            ],
            "social": [
                QueryTemplate(
                    template="Find [file_type] I [action] [social_media]",
                    categories=["activity", "social"],
                    placeholders={
                        "file_type": file_types,
                        "action": actions,
                        "social_media": social_media
                    },
                    description="Activity with social media context"
                ),
                QueryTemplate(
                    template="Show me files I shared [social_media] [time_period]",
                    categories=["social", "temporal"],
                    placeholders={
                        "social_media": social_media,
                        "time_period": time_periods
                    },
                    description="Social media with time period"
                ),
                QueryTemplate(
                    template="Find documents I commented on [social_media] [collaborator]",
                    categories=["social", "collaborator"],
                    placeholders={
                        "social_media": social_media,
                        "collaborator": collaborators
                    },
                    description="Social media with collaborator"
                )
            ],
            "calendar": [
                QueryTemplate(
                    template="Find [file_type] related to [calendar]",
                    categories=["activity", "temporal", "calendar"],
                    placeholders={
                        "file_type": file_types,
                        "calendar": calendars
                    },
                    description="Files related to calendar event"
                ),
                QueryTemplate(
                    template="Show me files I shared [calendar] [collaborator]",
                    categories=["calendar", "collaborator"],
                    placeholders={
                        "calendar": calendars,
                        "collaborator": collaborators
                    },
                    description="Files shared during calendar event"
                ),
                QueryTemplate(
                    template="Find documents I created [calendar] about [keyword]",
                    categories=["calendar", "content"],
                    placeholders={
                        "calendar": calendars,
                        "keyword": keywords
                    },
                    description="Content created during calendar event"
                )
            ]
        }
        
        # Flatten all templates for convenience
        self.all_templates = []
        for template_list in self.templates.values():
            self.all_templates.extend(template_list)
    
    def generate_query(self, category: str = None, fixed_values: Dict[str, str] = None) -> Dict[str, Any]:
        """Generate a random query, optionally from a specific category.
        
        Args:
            category: Category to select template from (default: random)
            fixed_values: Dictionary of fixed values for specific placeholders
        
        Returns:
            Dictionary with query text and metadata
        """
        if category and category in self.templates:
            template = random.choice(self.templates[category])
        else:
            template = random.choice(self.all_templates)
        
        query_text = template.fill(fixed_values)
        
        return {
            "text": query_text,
            "template": template.template,
            "categories": template.categories,
            "description": template.description,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def generate_queries_for_cluster(
        self,
        cluster: Dict[str, Any],
        num_queries: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate queries specifically for testing a cluster.

        This method creates a balanced set of queries that target both
        experimental and control sources in the cluster.

        Args:
            cluster: Cluster dictionary from ClusterGenerator
            num_queries: Number of queries to generate (default: 10)

        Returns:
            Dictionary with 'experimental' and 'control' query lists

        Following fail-stop principles - exits on failure rather than returning empty results.
        """
        # Validate cluster format
        if not isinstance(cluster, dict):
            self.logger.error("CRITICAL: Invalid cluster format - must be a dictionary")
            sys.exit(1)  # Fail-stop immediately

        # Extract categories from cluster with validation
        if "experimental_categories" not in cluster:
            self.logger.error("CRITICAL: Cluster missing 'experimental_categories' key")
            sys.exit(1)  # Fail-stop immediately

        if "control_categories" not in cluster:
            self.logger.error("CRITICAL: Cluster missing 'control_categories' key")
            sys.exit(1)  # Fail-stop immediately

        experimental_categories = set(cluster["experimental_categories"])
        control_categories = set(cluster["control_categories"])

        if not experimental_categories:
            self.logger.error("CRITICAL: Empty experimental categories list")
            sys.exit(1)  # Fail-stop immediately

        if not control_categories:
            self.logger.error("CRITICAL: Empty control categories list")
            sys.exit(1)  # Fail-stop immediately

        # Find templates that match these categories
        experimental_templates = []
        for template in self.all_templates:
            if any(cat in experimental_categories for cat in template.categories):
                experimental_templates.append(template)

        if not experimental_templates:
            self.logger.error(f"CRITICAL: No templates found for experimental categories: {experimental_categories}")
            sys.exit(1)  # Fail-stop immediately

        control_templates = []
        for template in self.all_templates:
            if any(cat in control_categories for cat in template.categories):
                control_templates.append(template)

        if not control_templates:
            self.logger.error(f"CRITICAL: No templates found for control categories: {control_categories}")
            sys.exit(1)  # Fail-stop immediately

        # Generate queries
        queries = {
            "experimental": [],
            "control": []
        }

        # Split queries evenly between experimental and control
        exp_count = num_queries // 2
        control_count = num_queries - exp_count

        # Generate experimental queries
        for _ in range(exp_count):
            template = random.choice(experimental_templates)
            query_text = template.fill()

            queries["experimental"].append({
                "text": query_text,
                "template": template.template,
                "categories": template.categories,
                "description": template.description,
                "timestamp": datetime.datetime.now().isoformat()
            })

        # Generate control queries
        for _ in range(control_count):
            template = random.choice(control_templates)
            query_text = template.fill()

            queries["control"].append({
                "text": query_text,
                "template": template.template,
                "categories": template.categories,
                "description": template.description,
                "timestamp": datetime.datetime.now().isoformat()
            })

        # Verify we generated the expected number of queries
        if len(queries["experimental"]) != exp_count:
            self.logger.error(f"CRITICAL: Failed to generate {exp_count} experimental queries")
            sys.exit(1)  # Fail-stop immediately

        if len(queries["control"]) != control_count:
            self.logger.error(f"CRITICAL: Failed to generate {control_count} control queries")
            sys.exit(1)  # Fail-stop immediately

        self.logger.info(f"Generated {len(queries['experimental'])} experimental queries and "
                         f"{len(queries['control'])} control queries for cluster")

        return queries
        
        return queries
    
    def generate_queries_with_llm(
        self,
        cluster: Dict[str, Any],
        num_queries: int = 10,
        llm_provider: str = "openai"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Generate queries using an LLM based on cluster metadata categories.
        
        Args:
            cluster: Cluster dictionary from ClusterGenerator
            num_queries: Number of queries to generate (default: 10)
            llm_provider: LLM provider to use ('openai' or 'anthropic')
        
        Returns:
            Dictionary with 'experimental' and 'control' query lists
        """
        # Import LLM connector - follows fail-stop principles
        connectors = import_llm_connector()
        if not connectors or llm_provider not in connectors:
            self.logger.error(f"CRITICAL: LLM provider '{llm_provider}' not available")
            self.logger.error("This is required for proper ablation testing")
            sys.exit(1)  # Fail-stop immediately

        # Initialize LLM connector
        connector_class = connectors[llm_provider]
        connector = connector_class()
        
        # Extract categories from cluster
        experimental_categories = sorted(list(set(cluster.get("experimental_categories", []))))
        control_categories = sorted(list(set(cluster.get("control_categories", []))))
        
        # Generate experimental queries
        experimental_prompt = f"""
        Generate {num_queries // 2} natural language queries for a file search system that specifically utilize metadata from these categories: {', '.join(experimental_categories)}.

        Query format should be plain text natural language questions seeking files based on:
        - Temporal information (when files were created, modified, or accessed)
        - Activity context (what the user was doing when interacting with files)
        - Location information (where the user was when working with files)
        - Content metadata (file types, keywords, tags)

        Example queries:
        - "Find all documents I worked on yesterday during my Zoom meeting"
        - "Show me PDFs I edited while listening to Spotify last week"
        - "Find files I accessed at the office that contain 'quarterly report'"

        Return exactly {num_queries // 2} queries as a JSON array with this format:
        [
          {{
            "query": "Find documents I edited yesterday",
            "categories": ["temporal", "activity"]
          }},
          ...
        ]
        """
        
        # Generate control queries
        control_prompt = f"""
        Generate {num_queries - (num_queries // 2)} natural language queries for a file search system that specifically utilize metadata from these categories: {', '.join(control_categories)}.

        Query format should be plain text natural language questions seeking files based on:
        - Temporal information (when files were created, modified, or accessed)
        - Activity context (what the user was doing when interacting with files)
        - Location information (where the user was when working with files)
        - Content metadata (file types, keywords, tags)

        Example queries:
        - "Find all documents I worked on yesterday during my Zoom meeting"
        - "Show me PDFs I edited while listening to Spotify last week"
        - "Find files I accessed at the office that contain 'quarterly report'"

        Return exactly {num_queries - (num_queries // 2)} queries as a JSON array with this format:
        [
          {{
            "query": "Find documents I edited yesterday",
            "categories": ["temporal", "activity"]
          }},
          ...
        ]
        """
        
        # Get experimental queries directly following fail-stop principles
        experimental_response = connector.get_completion(experimental_prompt)
        if not experimental_response:
            self.logger.error("CRITICAL: Failed to get experimental query response from LLM")
            sys.exit(1)  # Fail-stop immediately

        # Get control queries
        control_response = connector.get_completion(control_prompt)
        if not control_response:
            self.logger.error("CRITICAL: Failed to get control query response from LLM")
            sys.exit(1)  # Fail-stop immediately

        # Parse responses - following fail-stop principles
        import re

        def extract_json(text):
            """Extract JSON array from response text."""
            json_pattern = r'(\[.*\])'
            match = re.search(json_pattern, text, re.DOTALL)
            if match:
                return match.group(1)
            return None

        experimental_json = extract_json(experimental_response)
        if not experimental_json:
            self.logger.error("CRITICAL: Failed to extract experimental JSON from LLM response")
            self.logger.error(f"Response received: {experimental_response}")
            sys.exit(1)  # Fail-stop immediately

        control_json = extract_json(control_response)
        if not control_json:
            self.logger.error("CRITICAL: Failed to extract control JSON from LLM response")
            self.logger.error(f"Response received: {control_response}")
            sys.exit(1)  # Fail-stop immediately

        # Parse JSON data
        try:
            experimental_queries = json.loads(experimental_json)
        except json.JSONDecodeError as e:
            self.logger.error(f"CRITICAL: Failed to parse experimental JSON: {e}")
            self.logger.error(f"JSON data: {experimental_json}")
            sys.exit(1)  # Fail-stop immediately

        try:
            control_queries = json.loads(control_json)
        except json.JSONDecodeError as e:
            self.logger.error(f"CRITICAL: Failed to parse control JSON: {e}")
            self.logger.error(f"JSON data: {control_json}")
            sys.exit(1)  # Fail-stop immediately

        # Add timestamp to each query
        now = datetime.datetime.now().isoformat()
        for query in experimental_queries:
            query["timestamp"] = now
        for query in control_queries:
            query["timestamp"] = now

        return {
            "experimental": experimental_queries,
            "control": control_queries
        }
    
    def save_queries_to_file(self, queries: Dict[str, List[Dict[str, Any]]], file_path: str) -> None:
        """Save generated queries to a JSON file.

        Args:
            queries: Dictionary with query lists
            file_path: Path to save the JSON file

        Follows fail-stop principles - exits on failure instead of returning boolean.
        """
        try:
            with open(file_path, 'w') as f:
                json.dump(queries, f, indent=2)
        except Exception as e:
            self.logger.error(f"CRITICAL: Error saving queries to file {file_path}: {e}")
            sys.exit(1)  # Fail-stop immediately

        total_queries = len(queries.get("experimental", [])) + len(queries.get("control", []))
        self.logger.info(f"Saved {total_queries} queries to {file_path}")
    
    def load_queries_from_file(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Load queries from a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Dictionary with query lists

        Follows fail-stop principles - exits on failure rather than returning empty results.
        """
        try:
            with open(file_path, 'r') as f:
                queries = json.load(f)
        except FileNotFoundError:
            self.logger.error(f"CRITICAL: Query file not found: {file_path}")
            sys.exit(1)  # Fail-stop immediately
        except json.JSONDecodeError as e:
            self.logger.error(f"CRITICAL: Invalid JSON in query file {file_path}: {e}")
            sys.exit(1)  # Fail-stop immediately
        except Exception as e:
            self.logger.error(f"CRITICAL: Error loading queries from file {file_path}: {e}")
            sys.exit(1)  # Fail-stop immediately

        # Validate query structure
        if "experimental" not in queries or "control" not in queries:
            self.logger.error(f"CRITICAL: Invalid query file format in {file_path}")
            self.logger.error("Query file must contain 'experimental' and 'control' keys")
            sys.exit(1)  # Fail-stop immediately

        total_queries = len(queries.get("experimental", [])) + len(queries.get("control", []))
        if total_queries == 0:
            self.logger.error(f"CRITICAL: No queries found in {file_path}")
            sys.exit(1)  # Fail-stop immediately

        self.logger.info(f"Loaded {total_queries} queries from {file_path}")
        return queries
    
    def get_available_categories(self) -> List[str]:
        """Get a list of all available query categories.
        
        Returns:
            List of category names
        """
        return sorted(list(self.templates.keys()))


def main():
    """Test the QueryGenerator following fail-stop principles."""
    logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")

    # Create a generator with a fixed seed for reproducibility
    generator = QueryGenerator(seed=42)

    print("\nAvailable Query Categories:")
    categories = generator.get_available_categories()
    if not categories:
        print("CRITICAL: No query categories available")
        sys.exit(1)  # Fail-stop immediately

    for category in categories:
        print(f"- {category}")

    # Generate some random queries
    print("\nRandom Queries:")
    for i in range(5):
        query = generator.generate_query()
        # Validate query structure
        if 'text' not in query or 'categories' not in query:
            print(f"CRITICAL: Generated query {i+1} missing required fields")
            sys.exit(1)  # Fail-stop immediately

        print(f"- {query['text']}")
        print(f"  Categories: {', '.join(query['categories'])}")

    # Generate category-specific queries
    print("\nCategory-Specific Queries:")
    for category in categories:
        query = generator.generate_query(category)
        # Validate category-specific query
        if 'text' not in query or 'categories' not in query:
            print(f"CRITICAL: Generated category-specific query for '{category}' missing required fields")
            sys.exit(1)  # Fail-stop immediately

        print(f"- [{category}] {query['text']}")
        print(f"  Categories: {', '.join(query['categories'])}")

    # Test with a mock cluster
    mock_cluster = {
        "experimental_categories": ["activity", "temporal", "calendar"],
        "control_categories": ["spatial", "environmental"]
    }

    print("\nCluster-Specific Queries:")
    cluster_queries = generator.generate_queries_for_cluster(mock_cluster, num_queries=6)

    # Validate queries to ensure they exist (fail-stop approach)
    if not cluster_queries.get("experimental"):
        print("CRITICAL: Failed to generate experimental queries")
        sys.exit(1)  # Fail-stop immediately

    if not cluster_queries.get("control"):
        print("CRITICAL: Failed to generate control queries")
        sys.exit(1)  # Fail-stop immediately

    print("Experimental Queries:")
    for query in cluster_queries["experimental"]:
        print(f"- {query['text']}")
        print(f"  Categories: {', '.join(query['categories'])}")

    print("\nControl Queries:")
    for query in cluster_queries["control"]:
        print(f"- {query['text']}")
        print(f"  Categories: {', '.join(query['categories'])}")

    # Save queries to file - will fail-stop if there's an error
    generator.save_queries_to_file(cluster_queries, "test_queries.json")
    print("\nQueries saved to test_queries.json")


if __name__ == "__main__":
    main()