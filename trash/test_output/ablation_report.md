# Ablation Test Results

*Generated on 2025-05-05 18:55:33*

## Test Configuration

- **Total Queries**: 15
- **Ablated Categories**: location
- **Test Duration**: 3.39 seconds

## Results Summary

- **Average Precision**: 1.0000
- **Average Recall**: 1.0000
- **Average F1 Score**: 1.0000
- **Average Impact Score**: 0.0000

### Impact Interpretation

The Impact Score (1.0 - F1 Score) represents how much the search quality is affected when these metadata categories are removed:

- **0.00%** reduction in search quality when ablating these categories: location

This indicates a **very low** impact of these metadata categories on search quality.

### Impact by Query Type

| Query Type | Average Impact | Sample Queries |
|------------|----------------|----------------|
| Activity-based (4 queries) | 0.0000 | find files I edited yesterday, show documents I created l... |
| Location-based (9 queries) | 0.0000 | show documents I created last week, find photos taken in ... |
| Music-based (2 queries) | 0.0000 | show music I listened to yesterday, show videos I watched... |
| Content-based (6 queries) | 0.0000 | show documents I created last week, find files with conte... |

## Individual Query Results

| Query | F1 Score | Impact Score |
|-------|----------|-------------|
| find files I edited yesterday | 1.0000 | 0.0000 |
| show documents I created last week | 1.0000 | 0.0000 |
| find photos taken in San Francisco | 1.0000 | 0.0000 |
| show music I listened to yesterday | 1.0000 | 0.0000 |
| find files with content about machine learning | 1.0000 | 0.0000 |
| show documents shared with me by John | 1.0000 | 0.0000 |
| find presentations I worked on this month | 1.0000 | 0.0000 |
| show files related to my project | 1.0000 | 0.0000 |
| find PDF documents I opened recently | 1.0000 | 0.0000 |
| show photos taken during my vacation | 1.0000 | 0.0000 |
| find emails with attachments from last week | 1.0000 | 0.0000 |
| show videos I watched yesterday | 1.0000 | 0.0000 |
| find documents containing budget information | 1.0000 | 0.0000 |
| show files I modified after the meeting | 1.0000 | 0.0000 |
| find spreadsheets with financial data | 1.0000 | 0.0000 |

## Next Steps

- Run tests with different category combinations
- Compare results across different query types
- Analyze which metadata types have the highest impact on specific query categories
