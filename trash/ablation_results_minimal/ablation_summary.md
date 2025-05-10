# Ablation Study Results Summary
Date: 2025-05-08 22:53:40
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Storage.

A total of 2 test queries were evaluated, generating 4 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Location | 0.226 | 0.635 | 1.000 | 0.774 |
| Storage | 0.091 | 0.833 | 1.000 | 0.909 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Storage |
|---------------|---------------|---------------|
| Location | N/A | 0.226 |
| Storage | 0.091 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Dropbox sync? | Location | Storage | 0.286 |
| Can someone help me track down Sarah's quarterly p... | Location | Storage | 0.167 |
| Dropbox sync? | Storage | Location | 0.091 |
| Can someone help me track down Sarah's quarterly p... | Storage | Location | 0.091 |

## Recommendations
No collections showed particularly high impact scores (>0.5). This suggests that no single activity type is critical for overall search performance.

The strongest cross-collection dependencies were found between:

- **Location** → **Storage**: Impact 0.286
- **Location** → **Storage**: Impact 0.167
- **Storage** → **Location**: Impact 0.091

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
