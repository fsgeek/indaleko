# Ablation Study Results Summary
Date: 2025-05-08 11:54:57
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 5 test queries were evaluated, generating 10 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Location | 0.875 | 0.091 | 0.200 | 0.125 |
| Music | 0.692 | 0.250 | 0.400 | 0.308 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.875 |
| Music | 0.692 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Starbucks files? | Location | Music | 0.875 |
| Where did Sarah create the quarterly budget propos... | Location | Music | 0.875 |
| Find all PDFs that my colleague Miguel reviewed ye... | Location | Music | 0.875 |
| Show team documents accessed during Boston confere... | Location | Music | 0.875 |
| Central Park sketches | Location | Music | 0.875 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Location**: Impact score 0.875
- **Music**: Impact score 0.692

The strongest cross-collection dependencies were found between:

- **Location** → **Music**: Impact 0.875
- **Location** → **Music**: Impact 0.875
- **Location** → **Music**: Impact 0.875

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
