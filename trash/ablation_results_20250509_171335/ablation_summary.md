# Ablation Study Results Summary

Generated: 2025-05-09 17:13:36

## Overview

Total Queries: 10
Collections Tested: 2

## Aggregate Metrics

| Ablated Collection | Avg Precision | Avg Recall | Avg F1 Score | Avg Impact |
|-------------------|--------------|-----------|-------------|-----------|
| AblationTaskActivity | 0.2778 | 0.5000 | 0.3571 | 0.6429 |
| AblationLocationActivity | 0.5000 | 0.5000 | 0.5000 | 0.5000 |

## Interpretation

The **Impact** score measures how much performance degrades when a collection is ablated. Higher impact scores indicate greater importance of the collection to query results.

## Recommendations

1. The **AblationTaskActivity** collection has the highest impact (0.6429) on query results. This suggests this activity type provides critical context for search relevance.

3. The **AblationTaskActivity** collection contributes most to search precision (0.2778), indicating it helps reduce false positives.

4. The **AblationTaskActivity** collection contributes most to search recall (0.5000), indicating it helps reduce false negatives.
