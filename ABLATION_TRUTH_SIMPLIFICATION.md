# Ablation Truth Data Simplification

## Overview

This document describes the simplification of the truth data storage model in the ablation framework. By removing legacy methods and standardizing on the unified truth model, we have simplified the codebase, reduced duplication, and eliminated constraint violations.

## Changes Made

1. **Removed Legacy Methods**:
   - Removed `get_truth_data` (deprecated wrapper around `get_collection_truth_data`)
   - Removed `get_truth_data_legacy` (legacy method for per-collection truth data)
   - Removed `store_truth_data` (deprecated method for per-collection truth data)

2. **Simplified Truth Data Storage**:
   - Standardized on a single data storage model using the `store_unified_truth_data` method
   - This method stores a single document per query ID, with a mapping of collections to matching entities
   - Eliminates duplicate storage and potential inconsistencies

3. **Simplified Retrieval Methods**:
   - Updated `get_unified_truth_data` to only look for unified data (no reconstruction from legacy data)
   - Updated `get_collection_truth_data` to extract directly from unified data (no fallback)
   - Removed all fallback code paths for backward compatibility

4. **Fixed Database Constraint Violations**:
   - By standardizing on a single storage model, we eliminate the constraint violations
   - Previously, both storage models were trying to update the same document, causing conflicts
   - Now there's only one way to store truth data, preventing conflicts

## Benefits

1. **Cleaner Code**: Removed ~200 lines of unnecessary legacy code
2. **Fewer Warnings**: Eliminated constraint violation warnings during execution
3. **Simpler Data Model**: One unified truth set per query, rather than fragmented across collections
4. **Improved Scientific Integrity**: Ensures consistent ground truth data for experiments
5. **Better Performance**: No need to maintain compatibility with two different storage approaches

## Implementation Details

The unified truth model stores truth data in the AblationQueryTruth collection with:
- Document key = query UUID
- Each document contains a `matching_entities` object that maps collection names to lists of entity IDs

```json
{
  "_key": "8281894d-4194-5090-af90-e9dc8789ac3f",
  "query_id": "8281894d-4194-5090-af90-e9dc8789ac3f",
  "matching_entities": {
    "AblationMusicActivity": ["entity1", "entity2", "entity3"],
    "AblationLocationActivity": ["entity4", "entity5"]
  },
  "collections": ["AblationMusicActivity", "AblationLocationActivity"],
  "timestamp": 1715875600
}
```

This approach makes cross-collection queries more efficient and ensures consistent evaluation criteria across all collections involved in an experiment.
