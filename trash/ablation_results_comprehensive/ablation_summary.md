# Ablation Study Results Summary
Date: 2025-05-08 23:24:28
## Overview
This report summarizes the results of ablation testing for 6 activity types: Collaboration, Location, Media, Music, Storage, Task.

A total of 45 test queries were evaluated, generating 90 impact measurements.
## Impact Summary
### Average Impact by Collection
Impact represents how much query performance degrades when a collection is removed.
Higher values indicate more important collections.

| Collection | Average Impact | Precision | Recall | F1 Score |
|------------|---------------|-----------|--------|----------|
| Task | 0.316 | 0.557 | 1.000 | 0.684 |
| Collaboration | 0.286 | 0.589 | 1.000 | 0.714 |
| Location | 0.229 | 0.683 | 1.000 | 0.771 |
| Music | 0.224 | 0.685 | 1.000 | 0.776 |
| Storage | 0.214 | 0.703 | 1.000 | 0.786 |
| Media | 0.197 | 0.718 | 1.000 | 0.803 |

## Cross-Collection Dependencies
This table shows how ablating each collection (rows) affects queries targeting other collections (columns).

| Source \ Target | Collaboration | Location | Media | Music | Storage | Task |
|---------------|---------------|---------------|---------------|---------------|---------------|---------------|
| Collaboration | N/A | 0.231 | 0.444 | 0.333 | 0.421 | 0.000 |
| Location | 0.000 | N/A | 0.389 | 0.333 | 0.421 | 0.000 |
| Media | 0.000 | 0.154 | N/A | 0.333 | 0.496 | 0.000 |
| Music | 0.000 | 0.231 | 0.444 | N/A | 0.444 | 0.000 |
| Storage | 0.000 | 0.154 | 0.583 | 0.333 | N/A | 0.000 |
| Task | 0.000 | 0.231 | 0.583 | 0.333 | 0.434 | N/A |

## Query Analysis
### Most Affected Queries
| Query | Source Collection | Target Collection | Impact |
|-------|-------------------|-------------------|--------|
| Where can our team find the budget spreadsheets th... | Media | Storage | 0.600 |
| Taylor Swift? | Music | Media | 0.583 |
| Tesla Q4 earnings? | Task | Media | 0.583 |
| Jenkins PR? | Collaboration | Media | 0.583 |
| Where can our team find the budget spreadsheets th... | Storage | Media | 0.583 |

## Recommendations
No collections showed particularly high impact scores (>0.5). This suggests that no single activity type is critical for overall search performance.

The strongest cross-collection dependencies were found between:

- **Media** → **Storage**: Impact 0.600
- **Music** → **Media**: Impact 0.583
- **Task** → **Media**: Impact 0.583

These dependencies suggest that optimizing collection relationships could improve search performance by leveraging cross-collection information.
