# Ablation Study Results Summary
Date: 2025-05-08 21:09:24
## Overview
This report summarizes the results of ablation testing for 3 activity types: Location, Music, Task.

A total of 15 test queries were evaluated, generating 30 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Music | 0.083 | 0.857 | 1.000 | 0.917 |
| Task | 0.083 | 0.857 | 1.000 | 0.917 |
| Location | 0.000 | 1.000 | 1.000 | 1.000 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Location | Music | Task |
|---------------|---------------|---------------|---------------|
| Location | N/A | 0.000 | 0.000 |
| Music | 0.167 | N/A | 0.000 |
| Task | 0.167 | 0.000 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Madrid OR Barcelona 2014 NOT family videos | Music | Location | 0.167 |
| Can Karen's field recordings capture the soundscap... | Music | Location | 0.167 |
| Find satellite imagery showing deforestation patte... | Music | Location | 0.167 |
| Upload GPS coordinates to Garmin device | Task | Location | 0.167 |
| Sync Beatles FLAC | Music | Location | 0.167 |

## Recommendations
No collections showed particularly high impact scores (>0.5). This suggests that no single activity type is critical for overall search performance.

The strongest cross-collection dependencies were found between:

- **Music** → **Location**: Impact 0.167
- **Music** → **Location**: Impact 0.167
- **Music** → **Location**: Impact 0.167

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
