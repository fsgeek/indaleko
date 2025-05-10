# Ablation Study Results Summary
Date: 2025-05-08 20:54:37
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 2 test queries were evaluated, generating 4 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Music | 0.091 | 0.833 | 1.000 | 0.909 |
| Location | 0.000 | 1.000 | 1.000 | 1.000 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.000 |
| Music | 0.091 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Chicago hotels | Music | Location | 0.091 |
| Did HR approve the expense report for Tim's busine... | Music | Location | 0.091 |
| Chicago hotels | Location | Music | 0.000 |
| Did HR approve the expense report for Tim's busine... | Location | Music | 0.000 |

## Recommendations
No collections showed particularly high impact scores (>0.5). This suggests that no single activity type is critical for overall search performance.

The strongest cross-collection dependencies were found between:

- **Music** → **Location**: Impact 0.091
- **Music** → **Location**: Impact 0.091
- **Location** → **Music**: Impact 0.000

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
