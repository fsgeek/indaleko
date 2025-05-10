# Simple Ablation Testing Summary

**Generated on:** 2025-05-06 03:38:46

## Test Configuration

- Queries: 3
- Categories tested: activity, location, music

## Category Impact Summary

| Category | Impact Score | Precision | Recall | F1 Score |
|----------|-------------|-----------|--------|----------|
| activity | 0.2278 | 0.7366 | 0.7232 | 0.7722 |
| location | 0.1693 | 0.8234 | 0.7644 | 0.8307 |
| music | 0.0690 | 0.8653 | 0.8511 | 0.9310 |

**Overall Impact Score:** 0.1554

This indicates a **moderate** overall impact of metadata on search quality.

## Explanation

This example simulates ablation testing results without connecting to a database. In a real ablation test, each metadata category would be removed (ablated) from search queries to measure how much it affects search quality.

Impact Score is the key metric that represents how important each metadata category is. A higher impact score means that removing that category significantly degrades search quality.

## Next Steps

For real ablation testing with a database connection, use the full end-to-end example:

```bash
./run_end_to_end_ablation_example.sh
```
