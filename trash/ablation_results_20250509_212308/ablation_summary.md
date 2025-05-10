# Ablation Study Results Summary
Date: 2025-05-09 21:31:35
## Overview
This report summarizes the results of ablation testing for 6 activity types: Collaboration, Location, Media, Music, Storage, Task.

A total of 75 test queries were evaluated, generating 150 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Collaboration | 0.560 | 0.371 | 0.720 | 0.440 |
| Music | 0.550 | 0.386 | 0.720 | 0.450 |
| Task | 0.521 | 0.412 | 0.720 | 0.479 |
| Storage | 0.468 | 0.477 | 0.760 | 0.532 |
| Location | 0.430 | 0.518 | 0.760 | 0.570 |
| Media | 0.416 | 0.522 | 0.800 | 0.584 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Collaboration | Location | Media | Music | Storage | Task |
|---------------|---------------|---------------|---------------|---------------|---------------|---------------|
| Collaboration | N/A | 0.600 | 0.733 | 0.846 | 0.619 | 0.000 |
| Location | 0.200 | N/A | 0.667 | 0.273 | 0.610 | 0.400 |
| Media | 0.200 | 0.667 | N/A | 0.301 | 0.514 | 0.400 |
| Music | 0.800 | 0.600 | 0.733 | N/A | 0.619 | 0.000 |
| Storage | 0.400 | 0.733 | 0.733 | 0.273 | N/A | 0.200 |
| Task | 0.200 | 0.800 | 0.800 | 0.091 | 0.714 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Show me all Excel spreadsheets containing employee... | Location | Music | 1.000 |
| Show me all PDF files containing "budget forecast"... | Location | Task | 1.000 |
| Convert all 2021 business trip coordinates from do... | Location | Task | 1.000 |
| Convert all 2021 business trip coordinates from do... | Task | Location | 1.000 |
| Show me all PDF files containing "budget forecast"... | Task | Location | 1.000 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Collaboration**: Impact score 0.560
- **Music**: Impact score 0.550
- **Task**: Impact score 0.521

The strongest cross-collection dependencies were found between:

- **Location** → **Music**: Impact 1.000
- **Location** → **Task**: Impact 1.000
- **Location** → **Task**: Impact 1.000

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
