# Ablation Study Results Summary
Date: 2025-05-08 20:36:48
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 1 test queries were evaluated, generating 2 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Music | 0.783 | 0.122 | 1.000 | 0.217 |
| Location | 0.524 | 0.312 | 1.000 | 0.476 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.524 |
| Music | 0.783 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Nearest metro stations to Park Hotel Ljubljana for... | Music | Location | 0.783 |
| Nearest metro stations to Park Hotel Ljubljana for... | Location | Music | 0.524 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Location**: Impact score 0.524
- **Music**: Impact score 0.783

The strongest cross-collection dependencies were found between:

- **Music** → **Location**: Impact 0.783
- **Location** → **Music**: Impact 0.524

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
