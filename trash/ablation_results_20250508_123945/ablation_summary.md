# Ablation Study Results Summary
Date: 2025-05-08 12:40:08
## Overview
This report summarizes the results of ablation testing for 2 activity types: Location, Music.

A total of 5 test queries were evaluated, generating 10 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Location | 1.000 | 0.000 | 0.000 | 0.000 |
| Music | 0.750 | 0.333 | 0.200 | 0.250 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 1.000 |
| Music | 0.750 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Find location files | Location | Music | 1.000 |
| Search for location documents | Location | Music | 1.000 |
| location files from yesterday | Location | Music | 1.000 |
| Show me location data | Location | Music | 1.000 |
| What location information do I have? | Location | Music | 1.000 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Location**: Impact score 1.000
- **Music**: Impact score 0.750

The strongest cross-collection dependencies were found between:

- **Location** → **Music**: Impact 1.000
- **Location** → **Music**: Impact 1.000
- **Location** → **Music**: Impact 1.000

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
