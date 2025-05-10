# Ablation Query Analysis Report
Generated: 2025-05-10 09:17:13

## Summary Statistics
- Total unique queries analyzed: 13
- Number of collections analyzed: 6
- Queries performing full collection scans: 0 (0.0%)
- High-cost queries identified: 10
- Complex queries identified: 0

## Key Recommendations

- Analysis based on 13 unique queries across 6 collections.
- Collections without index recommendations: AblationMusicActivity, AblationLocationActivity, AblationTaskActivity, AblationCollaborationActivity, AblationStorageActivity, AblationMediaActivity. Consider manual inspection of query patterns.

## Collection Analysis

### AblationMusicActivity
- **Query count**: 15
- No specific index recommendations.

### AblationLocationActivity
- **Query count**: 15
- No specific index recommendations.

### AblationTaskActivity
- **Query count**: 15
- No specific index recommendations.

### AblationCollaborationActivity
- **Query count**: 15
- No specific index recommendations.

### AblationStorageActivity
- **Query count**: 15
- No specific index recommendations.

### AblationMediaActivity
- **Query count**: 15
- No specific index recommendations.

## Slow Queries

### Slow Query 1
- **Collection**: AblationMusicActivity
- **Estimated cost**: 1008.6146499208946
- **Sample query**: Where did Sarah upload those satellite imagery files of flooding in Jakarta from her research expedition?
- **Recommendation**: Consider adding indexes for filter attributes
- **AQL**: ```FOR doc IN AblationMusicActivity
        FILTER doc._key IN @truth_keys OR (doc.artist == @artist OR doc.timestamp >= @from_timestamp AND doc.timestamp <= @to_timestamp)
        RETURN doc```

### Slow Query 2
- **Collection**: AblationLocationActivity
- **Estimated cost**: 1472.62991059992
- **Sample query**: Where did Sarah upload those satellite imagery files of flooding in Jakarta from her research expedition?
- **Recommendation**: Consider adding indexes for filter attributes
- **AQL**: ```FOR doc IN AblationLocationActivity
        FILTER doc._key IN @truth_keys OR (doc.location_name == @location_name OR doc.timestamp >= @from_timestamp AND doc.timestamp <= @to_timestamp)
        RETURN doc```

### Slow Query 3
- **Collection**: AblationTaskActivity
- **Estimated cost**: 2404.881700556918
- **Sample query**: Where did Samsung executives stay during the Tokyo tech conference held at Ginza Mitsukoshi last quarter?
- **Recommendation**: Consider adding indexes for filter attributes
- **AQL**: ```FOR doc IN AblationTaskActivity
        FILTER doc._key IN @truth_keys OR (doc.task_type == @task_type OR doc.timestamp >= @from_timestamp AND doc.timestamp <= @to_timestamp)
        RETURN doc```

### Slow Query 4
- **Collection**: AblationLocationActivity
- **Estimated cost**: 1612.146232814166
- **Sample query**: Sarah's homework?
- **Recommendation**: Consider adding indexes for filter attributes
- **AQL**: ```FOR doc IN AblationLocationActivity
        FILTER doc._key IN @truth_keys OR (doc.location_name == @location_name OR doc.location_type == @location_type OR doc.timestamp >= @from_timestamp AND doc.timestamp <= @to_timestamp)
        RETURN doc```

### Slow Query 5
- **Collection**: AblationCollaborationActivity
- **Estimated cost**: 1210.663354603033
- **Sample query**: Moscow itinerary?
- **Recommendation**: Consider adding indexes for filter attributes
- **AQL**: ```FOR doc IN AblationCollaborationActivity
        FILTER doc._key IN @truth_keys OR (doc.event_type == @event_type OR doc.timestamp >= @from_timestamp AND doc.timestamp <= @to_timestamp)
        RETURN doc```

