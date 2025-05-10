# Ablation Study Results Summary
Date: 2025-05-08 20:35:30
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 2 test queries were evaluated, generating 4 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Music | 0.778 | 0.125 | 1.000 | 0.222 |
| Location | 0.524 | 0.312 | 1.000 | 0.476 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.524 |
| Music | 0.778 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Eiffel Tower? | Music | Location | 0.778 |
| Show me every document mentioning Central Park tha... | Music | Location | 0.778 |
| Eiffel Tower? | Location | Music | 0.524 |
| Show me every document mentioning Central Park tha... | Location | Music | 0.524 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Location**: Impact score 0.524
- **Music**: Impact score 0.778

The strongest cross-collection dependencies were found between:

- **Music** → **Location**: Impact 0.778
- **Music** → **Location**: Impact 0.778
- **Location** → **Music**: Impact 0.524

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
