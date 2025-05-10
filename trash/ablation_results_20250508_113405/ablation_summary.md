# Ablation Study Results Summary
Date: 2025-05-08 11:34:37
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
| Music | 0.846 | 0.125 | 0.200 | 0.154 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music |
|---------------|---------------|---------------|
| Location | N/A | 0.875 |
| Music | 0.846 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Find songs by Taylor Swift that I listened to at H... | Location | Music | 0.875 |
| Show me music I played while working at Office | Location | Music | 0.875 |
| Show me songs I added to my library while at Airpo... | Location | Music | 0.875 |
| What was I listening to when I was at Coffee Shop ... | Location | Music | 0.875 |
| Find tracks by Ed Sheeran from my Library playlist | Location | Music | 0.875 |

## Recommendations
Based on the ablation results, the following collections have high impact scores and should be prioritized in the search infrastructure:

- **Location**: Impact score 0.875
- **Music**: Impact score 0.846

The strongest cross-collection dependencies were found between:

- **Location** → **Music**: Impact 0.875
- **Location** → **Music**: Impact 0.875
- **Location** → **Music**: Impact 0.875

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
