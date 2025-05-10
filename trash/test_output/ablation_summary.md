# Ablation Study Results Summary
Date: 2025-05-08 18:13:01
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 2 test queries were evaluated, generating 4 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Location | 0.370 | 0.850 | 0.500 | 0.630 |
| Music | 0.370 | 0.850 | 0.500 | 0.630 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.370 |
| Music | 0.370 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Where did Jane save the PowerPoint presentation af... | Location | Music | 0.370 |
| Where did Jane save the PowerPoint presentation af... | Music | Location | 0.370 |
| Yellowstone hiking.pdf | Location | Music | 0.370 |
| Yellowstone hiking.pdf | Music | Location | 0.370 |

## Recommendations
No collections showed particularly high impact scores (>0.5). This suggests that no single activity type is critical for overall search performance.

The strongest cross-collection dependencies were found between:

- **Location** → **Music**: Impact 0.370
- **Music** → **Location**: Impact 0.370
- **Location** → **Music**: Impact 0.370

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
