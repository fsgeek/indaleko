# Ablation Study Results Summary
Date: 2025-05-08 14:35:34
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 1 test queries were evaluated, generating 2 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Music | 1.000 | 0.000 | 0.000 | 0.000 |
| Location | 0.875 | 0.091 | 0.200 | 0.125 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.875 |
| Music | 1.000 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| When did Carlos edit our Yellowstone trip itinerar... | Music | Location | 1.000 |
| When did Carlos edit our Yellowstone trip itinerar... | Location | Music | 0.875 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Location**: Impact score 0.875
- **Music**: Impact score 1.000

The strongest cross-collection dependencies were found between:

- **Music** → **Location**: Impact 1.000
- **Location** → **Music**: Impact 0.875

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
