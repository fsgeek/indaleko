# Ablation Study Results Summary
Date: 2025-05-08 20:38:20
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 3 test queries were evaluated, generating 6 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Music | 0.792 | 0.116 | 1.000 | 0.208 |
| Location | 0.524 | 0.312 | 1.000 | 0.476 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.524 |
| Music | 0.792 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Where's that Airbnb confirmation PDF for Kyoto vac... | Music | Location | 0.792 |
| Uber receipts SFO | Music | Location | 0.792 |
| Billie Eilish unplugged? | Music | Location | 0.792 |
| Where's that Airbnb confirmation PDF for Kyoto vac... | Location | Music | 0.524 |
| Uber receipts SFO | Location | Music | 0.524 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Location**: Impact score 0.524
- **Music**: Impact score 0.792

The strongest cross-collection dependencies were found between:

- **Music** → **Location**: Impact 0.792
- **Music** → **Location**: Impact 0.792
- **Music** → **Location**: Impact 0.792

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
