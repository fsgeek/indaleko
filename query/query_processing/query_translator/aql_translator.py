"""
This module defines the AQL translator to use with an LLM.

Project Indaleko
Copyright (C) 2024-2025 Tony Mason

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
import os
import sys

from typing import Any

from icecream import ic

if os.environ.get("INDALEKO_ROOT") is None:
    current_path = os.path.dirname(os.path.abspath(__file__))
    while not os.path.exists(os.path.join(current_path, "Indaleko.py")):
        current_path = os.path.dirname(current_path)
    os.environ["INDALEKO_ROOT"] = current_path
    sys.path.append(current_path)

# pylint: disable=wrong-import-position
from db.db_collection_metadata import IndalekoDBCollectionsMetadata

# from query.query_processing.data_models.query_input import StructuredQuery
# from query.query_processing.data_models.query_output import LLMTranslateQueryResponse
from query.query_processing.data_models.translator_input import TranslatorInput
from query.query_processing.data_models.translator_response import TranslatorOutput
from query.query_processing.query_translator.translator_base import TranslatorBase

# from query.llm_base import IndalekoLLMBase
# pylint: enable=wrong-import-position


class AQLTranslator(TranslatorBase):
    """
    Translator for converting parsed queries to AQL (ArangoDB Query Language).
    """

    def __init__(self, collections_metadata: IndalekoDBCollectionsMetadata):
        """
        Initialize the AQL translator.

        Args:
            collections_metadata: Metadata for the collections in the database.
        """
        self.db_collections_metadata = collections_metadata
        self.db_config = self.db_collections_metadata.db_config
        self.collection_data = (
            self.db_collections_metadata.get_all_collections_metadata()
        )

    def translate(self, input_data: TranslatorInput) -> TranslatorOutput:
        """
        Translate a parsed query into an AQL query.

        Args:
            parsed_query (dict[str, Any]): The parsed query from NLParser
            llm_connector (Any): Connector to the LLM service

        Returns:
            str: The translated AQL query
        """
        # Use the LLM to help generate the AQL query
        assert isinstance(input_data, TranslatorInput)
        prompt = self._create_translation_prompt2(input_data)
        completion = input_data.Connector.get_completion(
            context=prompt["system"],
            question=prompt["user"],
            schema=TranslatorOutput.model_json_schema(),
        )
        performance_data = json.loads(completion.usage.model_dump_json())
        response_data = json.loads(completion.choices[0].message.content)
        print(json.dumps(response_data, indent=2))
        return TranslatorOutput(
            aql_query=response_data["aql_query"],
            explanation=response_data["explanation"],
            confidence=response_data["confidence"],
            observations=response_data.get("observations", None),
            performance_info=performance_data,
        )

    def validate_query(self, query: str, explain=False) -> bool:
        """
        Validate the translated AQL query.

        Args:
            query (str): The translated AQL query

        Returns:
            bool: True if the query is valid, False otherwise
        """
        required_fields = [
            ".Size",
            ".Label",
            ".URI",
            ".Timestamp",
            ".SemanticAttributes",
        ]
        result = (
            "FOR" in query
            and "RETURN" in query
            and any(field in query for field in required_fields)
        )

        if explain and not result:
            explanation = []
            if "FOR" not in query:
                explanation.append("Missing 'FOR' clause.")
            if "RETURN" not in query:
                explanation.append("Missing 'RETURN' clause.")
            if not any(keyword in query for keyword in required_fields):
                explanation.append(
                    f"No instance of any required field {" ".join(required_fields)}."
                )
            ic("Invalid AQL query:", query, explanation)
        return result

    def optimize_query(self, query: str) -> str:
        """
        Optimize the translated AQL query.

        Args:
            query (str): The translated AQL query

        Returns:
            str: The optimized AQL query
        """
        # Implement query optimization logic
        # This is a placeholder implementation
        return query

    def _create_translation_prompt(
        self,
        parsed_query: dict[str, Any],
        selected_md_attributes: dict[str, Any],
        additional_notes: str,
        n_truth_md: int,
    ) -> str:
        """
        Create a prompt for the LLM to generate an AQL query.

        Args:
            parsed_query (dict[str, Any]): The parsed query

        Returns:
            str: The prompt for the LLM
        """
        # Implement prompt creation logic
        system_prompt = (
            """
            You are an assistant that generates ArangoDB queries for a Unified Personal Index (UPI) system.
            The UPI stores metadata about digital objects (e.g., files, directories) in an ArangoDB database.
            Given a user query and a dictionary called selected_md_attributes, generate the corresponding AQL
            query that retrieves matching information. The schema includes two main collections:

            ActivityContext: Stores metadata related to the context of activities. It includes the location field.
            Objects: Stores information about digital objects, such as files and directories.
            You should iterate through each context in ActivityContext and access the SemanticAttributes or relevant
            fields as required. Do not use both collections in a single query. The query should return the entire object
            from the Objects or ActivityContext collection.

            Important Instructions:
            If 'Activity' is specified in selected_md_attributes, search within the ActivityContext if not,
            search within Objects.

            In selected_md_attributes['Posix']:
                If "file.name" is specified, include it in the query as Label.
                If file.size is specified, use Size.
                If file.directory is specified, use the LocalPath.
                If "location" is specified in selected_md_attributes, include logic to filter paths based on:
                    "google_drive": /file/d/
                    "dropbox": /s/...?dl=0
                    "icloud": /iclouddrive/
                    "local": paths that contain the local_dir_name specified in selected_md_attributes.
            Do not include path filters in the query unless they are explicitly specified in the
            selected_md_attributes dictionary. The timestamp in geo_location is the time when the
            activity context was collected. The timestamp in the Posix is when the file was modified, changed,
            accessed or created; you don't have to convert the timestamps, just use the posix
            timestamp as is e.g.) when given {'Posix': {'timestamps': {'birthtime': {'starttime': 1736064000.0 ,
            'endtime': 1736064000.0 , 'command': 'equal'}}}, Activity': {geo_location: {'location': 'Victoria',
            'command': 'at', 'timestamp': 'birthtime'}} aql query is:
            FILTER TO_NUMBER(activity.Timestamp) == 1736064000.0
            To match coordinates, find SemanticAttributes with an Identifier.Label of "Longitude" and ensure
            the Data matches the given longitude, and similarly for latitude. Make sure to still check the
            activity.Record.Attributes for posix metadata as well (like name, path, timestamps, size, etc.)
            When command is "within", check that the coordinates are within the value specified in "km"
            relative to the given longitude and latitude coordinates.
            Only get semantic attributes if the 'Semantic' is populated.
            If the number of truth attributes is greater than one and in the dictionary, the file name command is
            'exactly' with a local directory specified, make sure to add % in command as there could be files with
            duplicate names in the same directory: {'Posix': {'file.name': {'pattern': 'photo', 'command': 'exactly',
            'extension': ['.jpg']}, 'file.directory': {'location': 'local', 'local_dir_name': 'photo'}}} should
            give aql: Label LIKE 'photo%.pdf' OR 'photo(%).pdf'; instead of
            Label LIKE 'photo.pdf'. If number of attributes is one, just use
            Label LIKE 'photo.pdf.
            When getting semantic attributes, retrieve the attribute via the dictionary attribute specified.
            All attributes are stored within list of attributes, the labels are the keys of the dictionary like
            'Text' or 'Type' and ther respective data are the values of the keys e.g., 'cats and dogs' is a datum
            for the key 'Text' and 'Title' a datum for the key 'Type'. Any text content is specified with 'Text'
            and 'Type' emphasizes what kind of text it is: ex.)
            {'Posix': {'file.name': {'pattern': 'essay', 'command': 'starts', 'extension': ['.txt']},
            'timestamps': {'modified': {'starttime': 1572505200.0, 'endtime': 1572505200.0, 'command': 'equal'}},
            'file.size': {'target_min': 7516192768, 'target_max': 7516192768, 'command': 'less_than'}},
            'Semantic': {'Content_1': {'Languages': 'str', 'Text': 'advancements in computer science'}}}
            then the Aql query would be: FOR record IN Objects FILTER record.Label LIKE
            'essay%.txt' AND TO_NUMBER(record.Record.Attributes.st_mtime) >= 1572505200.0 AND
            TO_NUMBER(record.Record.Attributes.st_mtime) <= 1572505200.0 AND
            record.Size < 7516192768
            LET semanticTitle = FIRST(FOR attr IN record.SemanticAttributes
            FILTER attr.Identifier.Label == 'Text' RETURN attr.Data)
            FILTER semanticTitle == 'advancements in computer science'
            RETURN record.
            When comparing timestamps in the Record table, ensure that timestamps with a prefix of
            st_ are converted to number (use TO_NUMBER) When matching file names, names should have
            an extension at the end, so use 'LIKE' command not ==.
            Make sure to incorporate all attributes from the given dictionary into the aql statement.
            The query should only include the AQL code, without any additional explanations or  comments.
            You must return one single code block enclosed in '```'s with only one FOR and RETURN statement.\n"""
            + f"""
            Dictionary of attributes: {str(selected_md_attributes)}
            Number of truth attributes: {str(n_truth_md)}
            Additional Notes: {additional_notes}
            Schema: {str(parsed_query['schema'])}
            """
        )

        user_prompt = parsed_query["original_query"]

        return {"system": system_prompt, "user": user_prompt}

    def _generate_collection_mapping(self) -> dict[str, str]:
        """
        Dynamically generates a mapping of keywords to collections based on CollectionMetadata.

        Args:
            db: ArangoDB database connection.

        Returns:
            dict[str, str]: A mapping of keywords to their relevant collections.
        """
        collection_mapping = {}

        # Fetch all collection metadata from CollectionMetadata
        for data in self.collection_data:
            ic(dir(data))

        collection_mapping = {
            "file": "Objects",
            "files": "Objects",
            "directory": "Objects",
            "directories": "Objects",
        }
        return collection_mapping

    def _determine_relevant_collections(
        self,
        parsed_query: dict[str, Any],
        selected_md_attributes: dict[str, Any],
    ) -> list[str]:
        """
        Dynamically determine the relevant collections based on the user query.

        Args:
            parsed_query (dict[str, Any]): The parsed user query.
            selected_md_attributes (dict[str, Any]): Extracted metadata attributes.

        Returns:
            List[str]: A list of relevant collections for AQL generation.
        """

        relevant_collections = set()

        # Step 1: Fetch dynamic keyword → collection mapping from CollectionMetadata
        collection_mapping = self._generate_collection_mapping()

        # Step 2: Extract keywords from user query
        user_query_text = parsed_query.get("original_query", "").lower().split()

        # Step 3: Identify collections based on static metadata
        for word in user_query_text:
            if word in collection_mapping:
                relevant_collections.add(collection_mapping[word])

        # Step 4: Identify if the query requires activity tracking
        needs_activity_data = any(
            keyword in user_query_text
            for keyword in [
                "edited",
                "viewed",
                "accessed",
                "created",
                "deleted",
                "location",
                "timestamp",
            ]
        )

        if needs_activity_data:
            # Step 5: Query `ActivityDataProviders` to find available sources
            activity_providers = self.db_config.db.aql.execute(
                "FOR provider IN ActivityDataProviders RETURN provider.Name"
            )
            provider_collections = list(activity_providers)

            # Step 6: Add available provider collections to the relevant collections list
            relevant_collections.update(provider_collections)

            # Step 7: Ensure ActivityContext is included (acts as an index/cursor)
            relevant_collections.add("ActivityContext")

        return list(relevant_collections)

    def _create_translation_prompt2(self, input_data: TranslatorInput) -> str:
        """
        Constructs a structured prompt for the LLM to generate an AQL query.
        """
        user_prompt = input_data.Query.original_query
        system_prompt = f"""
        You are **Archivist**, an expert at working with Indaleko to find pertinent
        digital objects (e.g., files).
        **Indaleko** implements a unified personal index (UPI) system
        that stores metadata about digital objects in an ArangoDB database.
        Your task is to generate an optimized AQL query
        that retrieves matching information based on the user query and selected
        metadata attributes.
        In forming this query, you will need to consider the schema of the database,
        including the relevant collections
        and their fields, as well as the needs of the user. Please take sufficient time to
        return a query that is both efficient and accurate, as our primary goal is to
        minimize the time our user spends looking for the specific information that they need
        and to also minimize our user's abandonment rate.
        The structured data that follows provides information about the database.
        {input_data}
        """

        return {"system": system_prompt, "user": user_prompt}
