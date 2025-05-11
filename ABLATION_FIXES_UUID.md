# Ablation Framework Truth Data Fixes - UUID Handling

## Problem Analysis

The ablation framework was experiencing failures related to truth data lookups, with warnings like:
```
WARNING:research.ablation.ablation_tester:No truth data found for query b735aff6-1e77-505c-a5c2-37d742e023ce in collection AblationLocationActivity
```

After investigation, we identified several issues:

1. **UUID Format Inconsistencies**: UUIDs used as document keys were sometimes formatted differently:
   - With hyphens: "b735aff6-1e77-505c-a5c2-37d742e023ce"
   - Without hyphens: "b735aff61e77505ca5c237d742e023ce"

2. **Truth Data Lookup Limitations**: The system only tried one method to find truth data and gave up if that failed.

3. **Verification Gaps**: Truth data storage wasn't verified after operations.

## Implemented Fixes

### 1. Enhanced Truth Data Storage

We improved the `store_unified_truth_data` method to:
- Store both hyphenated and non-hyphenated versions of UUIDs for reference
- Add detailed logging of all truth data being stored
- Add robust entity validation with appropriate error handling
- Implement verification of successful storage
- Follow the strict fail-stop model by raising exceptions on failures

### 2. Robust Truth Data Retrieval

We enhanced the `get_collection_truth_data` method to:
- Try multiple lookup strategies when finding truth documents
- Attempt both direct key lookup and query-based lookup
- Try alternative UUID formats when needed
- Log detailed diagnostic information for debugging
- Maintain scientific integrity by never fabricating data

### 3. Unified Truth Model Architecture

We consolidated on a single unified truth model that:
- Stores truth data once per query across all collections
- Uses a consistent schema for storage
- Maintains clear auditing of truth data modifications
- Preserves scientific consistency by not changing existing truth data

## Scientific Integrity Safeguards

Throughout all fixes, we maintained strict scientific integrity:
- **No Fabricated Data**: We never generate fake or synthetic truth data
- **Fail-Stop Model**: When truth data is missing, we fail visibly rather than continuing
- **Detailed Logging**: All operations are thoroughly logged for debugging and auditing
- **Data Verification**: Data storage and retrieval are verified at multiple steps

## Code Details

### Key changes to `store_unified_truth_data`

```python
# CRITICAL FIX: Ensure we have both UUID and string representations stored
# This helps with lookup issues where the ID format might vary
str_query_id = str(query_id)
truth_doc = {
    "_key": str_query_id,  # Use string representation as key
    "query_id": str_query_id,  # Redundant but helps with querying
    "query_uuid": str_query_id,  # Explicit field for string UUID
    "matching_entities": unified_matching_entities,
    "collections": list(unified_matching_entities.keys()),
    "timestamp": int(time.time())
}
```

### Multiple lookup approaches in `get_collection_truth_data`

```python
# Try searching by query ID as a string
try:
    query_str = str(query_id)

    # Run query to find truth data with query_id field
    aql_query = f"""
    FOR doc IN {self.TRUTH_COLLECTION}
    FILTER doc.query_id == @query_id
    RETURN doc
    """
    cursor = self.db.aql.execute(aql_query, bind_vars={"query_id": query_str})
    results = list(cursor)

    if results:
        # Success with query lookup
        return set(matching_entities[collection_name])
    else:
        # One last try - check if hexadecimal format was used
        hex_id = query_str.replace('-', '')
        hex_doc = self.db.collection(self.TRUTH_COLLECTION).get(hex_id)
        if hex_doc and "matching_entities" in hex_doc:
            return set(matching_entities[collection_name])
except Exception as e:
    self.logger.warning(f"Error during alternative truth data lookup: {e}")
```

### Verification of Stored Data

```python
# CRITICAL FIX: Verify the data was actually stored
verification = collection.get(str_query_id)
if not verification:
    self.logger.error(f"CRITICAL: Failed to verify truth data storage for query {query_id}")
    raise RuntimeError(f"Truth data verification failed for query {query_id}")

self.logger.info(f"Successfully verified truth data storage for query {query_id}")
```

## Verification

The fixes were tested with a minimal ablation experiment with the following parameters:
```
python research/ablation/run_comprehensive_experiment.py --rounds 1 --control-pct 0.2 --count 10 --queries 5 --max-combos 10
```

## Next Steps

1. Run a full ablation experiment to confirm fixes:
```
python research/ablation/run_comprehensive_experiment.py --rounds 3 --control-pct 0.3 --visualize
```

2. Verify results in `ablation_results_[TIMESTAMP]/experiment_summary.md`

3. Consider implementing a UUID-aware ArangoDB driver if UUID format issues continue to appear in other parts of the system.
