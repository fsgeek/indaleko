# Ablation Framework Fixes

## Deterministic Entity Selection Fixes

The ablation framework was generating inconsistent truth data for the same query ID and collection combination. This manifested as warnings like:

```
WARNING: Found different truth data for same query/collection: 55003a30-504a-5d06-b885-16ff6a51925c/AblationStorageActivity
WARNING: Existing: 5 entities, New: 5 entities
WARNING: Difference: 6 entities
```

This inconsistency undermines scientific reproducibility and causes validation failures.

### Root Cause Analysis

1. **Query ID Generation**: The `generate_cross_collection_queries` method was using inconsistent methods for generating query IDs:
   - Base query IDs did not account for collection order variations
   - Collection-specific query IDs didn't include sufficient context

2. **Entity Selection Logic**: The approach for selecting entities deterministically had flaws:
   - Used only part of the UUID (first 8 hex chars) for seed generation
   - Used a simple modulo operation (seed_value % 20) that has a high collision probability
   - Did not properly account for the current round in entity selection

3. **Cross-Collection Relationship**: The query ID generation didn't properly reflect the relationship between paired collections.

### Fixed Implementation

The following changes ensure deterministic truth data generation:

1. **Base Query ID Generation**:
   - Now sorts collections alphabetically before generating the base ID
   - Uses a consistent "cross_query" prefix
   - This ensures stable IDs even if collection processing order changes

2. **Collection-Specific Query ID Generation**:
   - Includes all context needed for proper entity selection (collection, query index, seed, round)
   - Creates truly global and consistent identifiers
   - Uses "fixed_query" prefix to clearly indicate its purpose

3. **Improved Entity Selection Logic**:
   - Uses more bits from the UUID for better seed value distribution (12 hex chars instead of 8)
   - Uses a more sophisticated formula for offset calculation to reduce collision probability
   - Properly accounts for experimental context in entity selection

### Testing and Verification

The fixes have been verified using:
1. `test_deterministic_truth_data.py` which confirms deterministic entity selection works
2. `run_verified_ablation_experiment.py` which tests the entire ablation framework pipeline

## Original Fixes

Initially, we addressed issues with the ablation framework including:

1. **Fixed Collection Access Pattern**: Changed from trying to iterate over IndalekoDBCollections to directly accessing specific collection names
2. **Direct Collection Access**: Now using `self.db.collection(collection_name)` to get collection objects by name with proper error checking
3. **Activity Collection Handling**: Explicitly defined activity collections as a list to allow proper iteration in test loops

## New Issues and Solutions

### Truth Data Integrity Problems

The ablation framework encountered additional critical issues that prevented successful test execution:

1. **Truth Data Constraint Violations**: The `AblationQueryTruth` collection had unique constraints on the `query_id` and `collection` fields, causing constraint violations when storing truth data for different collections with the same query ID.

2. **Inconsistent Truth Data Generation**: Truth data was sometimes missing or inconsistently generated, leading to failures in data sanity checks.

3. **Complex Database State**: The database accumulated state from previous runs, making it difficult to run new tests without a clean slate.

### Solution Approach

To fix these issues, we implemented a multi-step approach:

1. **Clean Database Initialization**: Added a clear step to reset the truth collection before each test run, ensuring a clean starting point.

2. **Deterministic Query IDs**: Implemented deterministic query ID generation for each collection, ensuring reproducible test results.

3. **Initial Truth Data Generation**: Created a dedicated script (`generate_initial_truth_data.py`) to ensure valid truth data exists for all collections before running tests.

4. **Enhanced Error Recovery**: Improved error handling to ensure tests can progress even when encountering non-critical issues.

5. **Simplified Test Runner**: Created a fixed test runner (`run_fixed_ablation_test.py`) that follows the correct initialization sequence.

## Implementation Details

### Truth Data Generation

The truth data generation process was modified to use collection-specific query IDs, preventing unique constraint violations:

```python
# Use collection-specific query IDs when generating truth data
query_ids = {
    "AblationMusicActivity": uuid.UUID("00000000-0000-0000-0000-000000000001"),
    "AblationLocationActivity": uuid.UUID("00000000-0000-0000-0000-000000000002"),
    # etc.
}

# Process each collection with its own query ID
for collection_name, query_id in query_ids.items():
    # Create truth data with collection-specific query ID
    tester.store_truth_data(query_id, collection_name, entity_keys)
```

### Database Cleanup

Before running tests, we clear the truth collection to avoid conflicts:

```python
def clear_truth_collection():
    """Clear the truth collection to start fresh."""
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    truth_collection = "AblationQueryTruth"
    if db.has_collection(truth_collection):
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
```

### Key Test Verification

We implemented simplified test verification to confirm the core functionality works:

1. The basic query processing with truth data functionality
2. The ablation mechanism with proper restoration 
3. Cross-collection query handling

## Running the Fixed Implementation

The new test runner (`run_fixed_ablation_test.py`) simplifies running the ablation framework:

```bash
# Run with all collections
python run_fixed_ablation_test.py --all-collections

# Run with specific collections
python run_fixed_ablation_test.py --collections AblationMusicActivity,AblationLocationActivity

# Run with fixed seed for reproducibility
python run_fixed_ablation_test.py --all-collections --fixed-seed

# Run without clearing truth data
python run_fixed_ablation_test.py --all-collections --skip-clear

# Run with custom parameters
python run_fixed_ablation_test.py --all-collections --count 100 --queries 10
```

## Next Steps

1. **Auto-verification**: Add automatic verification of test results.

2. **Enhanced Reporting**: Improve the test reports with more detailed metrics.

3. **Parallelization**: Add support for parallel test execution for larger tests.

4. **Integration with CI/CD**: Add automation for running tests as part of the CI/CD pipeline.

5. **Test Data Generation**: Improve the test data generation to create more realistic activity data with appropriate cross-collection relationships.

6. **Result Analysis**: Analyze the results to measure the impact of each collection type on query performance and visualize the results to demonstrate the impact more clearly.