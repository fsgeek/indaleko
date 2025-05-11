# Ablation Query and Truth Data Design

## Current Implementation Issues

The ablation framework currently has several issues with query truth data generation and collection relationships:

1. **Collection Independence**: Each collection is treated independently, with separate truth data per collection, leading to "No truth data found" errors.

2. **Update Syntax Error**: The `collection.update()` method is being called incorrectly:
   ```python
   # Incorrect
   collection.update(composite_key, {"matching_entities": list(new_entities)})

   # Correct
   collection.update({"_key": composite_key, "matching_entities": list(new_entities)})
   ```

3. **Missing Truth Data**: For cross-collection queries, errors appear because truth data is only created for the primary collection but not for related collections:
   ```
   WARNING: No truth data found for query 5f00f22a-ffe0-5647-aa7c-eac103c643e3 in collection AblationLocationActivity
   ```

4. **Model Mismatch**: The current collection-based model doesn't align with Indaleko's conceptual filtering model, where activity data acts as filters on a base collection (Objects).

## Flawed Approach: Collection-Specific Truth Data

The current implementation has a fundamental architectural issue: **truth data is fragmented across collection types** rather than being defined once per query. This leads to several problems:

1. **Missing Truth Data**: Many queries report "No truth data found" for specific collections, causing the framework to fail
2. **Inconsistent Metrics**: The same query yields different truth sets depending on which collection is being queried
3. **Architectural Complexity**: The code has to maintain separate truth sets per collection, complicating the system
4. **Scientific Validity Issues**: Comparing ablated results to different truth sets per collection undermines the experiment's validity

## Core Design Principle: Unified Truth Model

The key insight is that **truth is defined per query, not per context/filter/collection**. Each query has one canonical intent represented by a single truth set.

**Why This Is The Correct Approach**:

1. **Scientific Validity**: In a scientific experiment, the control group must be consistent
2. **Conceptual Accuracy**: The truth represents "what documents should match this query's intent"
3. **Simplified Logic**: No need to maintain separate truth data per collection
4. **Fail-Stop Safety**: No risk of missing truth data errors

## Implementation Changes

### 1. Single Truth Set Storage

```python
# OLD approach (problematic)
def store_truth_data(self, query_id: uuid.UUID, collection_name: str, matching_entities: list[str]) -> bool:
    # Creates different truth sets per collection
    composite_key = f"{query_id}_{collection_name}"
    truth_doc = {
        "_key": composite_key,
        "query_id": str(query_id),
        "matching_entities": matching_entities,
        "collection": collection_name,
    }
    # ...store with composite key...

# NEW approach (unified truth)
def store_truth_data(self, query_id: uuid.UUID, matching_entities: dict[str, list[str]]) -> bool:
    # One truth set per query, containing entities from all collections
    truth_doc = {
        "_key": str(query_id),
        "query_id": str(query_id),
        "matching_entities": matching_entities,  # Dict mapping collection to entities
        "collections": list(matching_entities.keys()),
    }
    # ...store with query_id as key...
```

### 2. Unified Truth Retrieval

```python
# OLD approach (problematic)
def get_truth_data(self, query_id: uuid.UUID, collection_name: str) -> set[str]:
    # Tries to get truth data specific to a collection
    composite_key = f"{query_id}_{collection_name}"
    truth_doc = self.db.collection(self.TRUTH_COLLECTION).get(composite_key)
    # ...fallback queries and error handling...

# NEW approach (unified truth)
def get_truth_data(self, query_id: uuid.UUID) -> dict[str, set[str]]:
    # Gets the entire truth set for the query across all collections
    truth_doc = self.db.collection(self.TRUTH_COLLECTION).get(str(query_id))
    if not truth_doc:
        raise RuntimeError(f"No truth data found for query {query_id}")
    return {coll: set(entities) for coll, entities in truth_doc.get("matching_entities", {}).items()}
```

### 3. Metrics Calculation Against Canonical Truth

```python
# OLD approach (problematic)
def calculate_metrics(self, query_id: uuid.UUID, results: list[dict], collection_name: str) -> AblationResult:
    # Gets truth specific to a collection
    truth_data = self.get_truth_data(query_id, collection_name)
    if not truth_data:
        # Fails if there's no truth for this specific collection
        raise RuntimeError(f"No truth data available for {query_id} in {collection_name}")
    # ...calculate metrics...

# NEW approach (unified truth)
def calculate_metrics(self, query_id: uuid.UUID, results: list[dict], collection_name: str) -> AblationResult:
    # Gets unified truth data containing all collections
    all_truth_data = self.get_truth_data(query_id)
    # Use the relevant collection's truth from the unified set
    collection_truth = all_truth_data.get(collection_name, set())

    # Special case: if collection has empty truth data and is not being ablated,
    # this indicates it's a secondary collection that shouldn't match results
    if not collection_truth and not self.ablated_collections.get(collection_name, False):
        self.logger.info(f"Collection {collection_name} has no expected matches for query {query_id}")

    # ...calculate metrics using collection_truth...
```

### 4. Truth Generation Logic

The biggest change is in how truth data is generated:

```python
# NEW truth generation approach
def generate_query_truth_data(self, query_id: uuid.UUID, query_text: str) -> bool:
    """Generate unified truth data for a query across all collections."""
    # Run the query against each collection with full context (no ablation)
    matching_entities = {}

    for collection in self.collections_to_test:
        # Execute query with all filters enabled
        results = self.execute_full_context_query(query_text, collection)
        # Store matching entities for this collection
        matching_entities[collection] = [doc["_key"] for doc in results]

    # Store unified truth data with all collections in one document
    return self.store_truth_data(query_id, matching_entities)
```

## Benefits of This Approach

1. **Scientific Validity**: All ablated queries are compared against the same canonical truth set
2. **Simplicity**: One truth set per query is easier to understand and maintain
3. **Debugging**: Errors are more meaningful and point to real issues rather than architectural problems
4. **Consistency**: Metrics are calculated more consistently, leading to more reliable experimental results

## Implementation Plan

1. Update the AblationTester class to use a single canonical truth model
2. Modify experiment_runner.py to generate unified truth sets
3. Update all methods that reference truth data to use the new model
4. Add backward compatibility for existing experiments if needed
5. Add documentation on the new approach

## Data Migration Considerations

For existing truth data, we may need a migration script to consolidate collection-specific truth into unified truth sets. This can be done on-demand as experiments run or as a one-time migration.

## Code Examples

### Updating the ablation_tester.py with the Unified Truth Model

```python
def store_unified_truth_data(self, query_id: uuid.UUID, unified_matching_entities: dict[str, list[str]]) -> bool:
    """Store a unified truth set for a query across all collections.

    Args:
        query_id: The UUID of the query
        unified_matching_entities: Dictionary mapping collection names to matching entity keys

    Returns:
        bool: True if the operation was successful
    """
    if not self.db:
        self.logger.error("No database connection available")
        sys.exit(1)

    # Ensure the Truth Collection exists
    if not self.db.has_collection(self.TRUTH_COLLECTION):
        self.db.create_collection(self.TRUTH_COLLECTION)
        self.logger.info(f"Created unified truth collection {self.TRUTH_COLLECTION}")

    # Create the truth document
    truth_doc = {
        "_key": str(query_id),
        "query_id": str(query_id),
        "matching_entities": unified_matching_entities,
        "collections": list(unified_matching_entities.keys()),
        "timestamp": int(time.time())
    }

    collection = self.db.collection(self.TRUTH_COLLECTION)

    # Check if a document with this query_id already exists
    existing = collection.get(str(query_id))
    if existing:
        self.logger.info(f"Updating existing truth data for query {query_id}")
        collection.update(truth_doc)
    else:
        self.logger.info(f"Creating new unified truth data for query {query_id}")
        collection.insert(truth_doc)

    return True
```

### Updating the experimental/experiment_runner.py with the Unified Truth Model

```python
def generate_query_truth_data(self, query_id: uuid.UUID, query_text: str) -> bool:
    """Generate truth data for a query across all collections.

    This method executes the query against each collection with all filters
    enabled, then stores a unified truth document containing the expected
    matches for all collections.

    Args:
        query_id: The UUID of the query
        query_text: The query text

    Returns:
        bool: True if truth data was generated successfully
    """
    self.logger.info(f"Generating unified truth data for query {query_id}: '{query_text}'")

    # Initialize the ablation tester if not already done
    if not self.ablation_tester:
        self.ablation_tester = AblationTester()

    # Track matching entities for each collection
    unified_truth = {}

    # For each collection, execute the query and record matching entities
    for collection_name in self.collections:
        # Skip collections that don't exist (this can happen with optional collections)
        if not self.ablation_tester.db.has_collection(collection_name):
            self.logger.warning(f"Collection {collection_name} does not exist, skipping truth generation")
            continue

        # Execute the query against this collection (with all filters enabled)
        results, _, _ = self.ablation_tester.execute_query(
            query_id=query_id,
            query=query_text,
            collection_name=collection_name,
            limit=self.query_limit
        )

        # Extract the keys of matching entities
        matching_keys = [doc.get("_key") for doc in results if doc.get("_key")]
        unified_truth[collection_name] = matching_keys

        self.logger.info(f"Found {len(matching_keys)} matching entities in {collection_name} for query {query_id}")

    # Store the unified truth data
    success = self.ablation_tester.store_unified_truth_data(query_id, unified_truth)
    if not success:
        self.logger.error(f"Failed to store unified truth data for query {query_id}")
        return False

    return True
```

## Testing Strategy

To validate the unified truth model:

1. **Unit Tests**: Create unit tests for the new store_unified_truth_data and get_unified_truth_data methods
2. **Integration Tests**: Test the integration of truth generation, storage, and metrics calculation
3. **Consistency Tests**: Verify that ablation experiments produce consistent metrics with the unified truth model
4. **Backward Compatibility**: Ensure existing experiments can still run with minimal changes

## Summary

The unified truth model is a conceptually correct approach to truth data in the ablation framework:

1. Truth is defined per query, not per collection
2. Each query has one canonical set of expected matches
3. Metrics are calculated against this canonical truth set
4. This ensures scientific validity and consistency

This approach aligns better with Indaleko's filtering model and provides a more reliable foundation for ablation experiments.
