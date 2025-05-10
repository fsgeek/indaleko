# Ablation Study Results Summary
Date: 2025-05-08 21:07:23
## Overview
This report summarizes the results of ablation testing for 3 activity types: Location, Music, Task.

A total of 6 test queries were evaluated, generating 12 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Location | 0.000 | 1.000 | 1.000 | 1.000 |
| Music | 0.000 | 1.000 | 1.000 | 1.000 |
| Task | 0.000 | 1.000 | 1.000 | 1.000 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music | Task |
|---------------|---------------|---------------|---------------|
| Location | N/A | 0.000 | 0.000 |
| Music | 0.000 | N/A | 0.000 |
| Task | 0.000 | 0.000 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Where did Johnson save the satellite imagery of Ho... | Location | Music | 0.000 |
| Where did Johnson save the satellite imagery of Ho... | Music | Location | 0.000 |
| Disneyland meetup | Location | Music | 0.000 |
| Disneyland meetup | Music | Location | 0.000 |
| Where's that Excel spreadsheet John shared after t... | Location | Task | 0.000 |

## Recommendations
No collections showed particularly high impact scores (>0.5). This suggests that no single activity type is critical for overall search performance.

The strongest cross-collection dependencies were found between:

- **Location** → **Music**: Impact 0.000
- **Music** → **Location**: Impact 0.000
- **Location** → **Music**: Impact 0.000

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
