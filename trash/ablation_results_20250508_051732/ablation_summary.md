# Ablation Study Results Summary

Generated: 2025-05-08 05:17:33

## Overview

Total Queries: 10
Collections Tested: 2

## Aggregate Metrics

| Ablated Collection | Avg Precision | Avg Recall | Avg F1 Score | Avg Impact |
|-------------------|--------------|-----------|-------------|-----------|
| AblationLocationActivity | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| AblationTaskActivity | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## Interpretation

The **Impact** score measures how much performance degrades when a collection is ablated. Higher impact scores indicate greater importance of the collection to query results.

## Recommendations

1. The **AblationLocationActivity** collection has the highest impact (1.0000) on query results. This suggests this activity type provides critical context for search relevance.

3. The **AblationLocationActivity** collection contributes most to search precision (0.0000), indicating it helps reduce false positives.

4. The **AblationLocationActivity** collection contributes most to search recall (0.0000), indicating it helps reduce false negatives.
