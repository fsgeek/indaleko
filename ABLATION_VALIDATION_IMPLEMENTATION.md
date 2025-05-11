# Ablation Validation Implementation

This document details the implementation of validation checks for ablation experiment results, designed to ensure scientific integrity of the metrics used to evaluate collection impacts.

## Implementation Overview

The validation system was implemented by adding a `validate_ablation_results` function to `analyze_results.py`, which examines ablation metrics for suspicious patterns that may indicate invalid or fabricated results.

## Key Features

1. **Comprehensive Issue Detection**: The system detects five key validity issues:
   - Precision = 1.0 with no true positives
   - Perfect metrics with no matching activity
   - F1 = 0.0 despite having false negatives > 0
   - Inconsistent metrics between result count and TP+FP
   - Identical queries for ablated and non-ablated runs

2. **Severity Classification**: Each detected issue is classified as either:
   - `critical`: Issues that seriously compromise scientific validity
   - `warning`: Issues that may indicate problems but aren't necessarily fatal

3. **Detailed Reporting**: The system adds a validation section to analysis reports including:
   - Count of issues by severity
   - Table of all detected issues
   - Detailed examination of critical issues with relevant query details
   - Risk assessment for overall experiment validity

4. **AQL Query Analysis**: For identical query detection, the system:
   - Tracks queries by collection and ablation status
   - Compares ablated vs. non-ablated query strings
   - Ignores comments and whitespace variations
   - Provides side-by-side display of problematic queries

5. **Risk Assessment**: The system provides an overall risk assessment based on:
   - Percentage of critical issues
   - Types of issues detected
   - Potential impact on experimental validity

## Implementation Details

### Analysis Entry Point

The `analyze_impact_metrics` function was modified to run the validation checks:

```python
# Run validation checks
logger.info("Running validation checks on metrics...")
validation_results = validate_ablation_results(impact_data)
```

### Validation Function

The core validation function examines the structure of impact metrics:

```python
def validate_ablation_results(results):
    """Validate ablation results for suspicious or invalid metrics."""
    flagged_cases = []

    # Handle different possible structures of results
    impact_metrics = None
    if "impact_metrics" in results:
        impact_metrics = results["impact_metrics"]
    # [...]

    # Collect all metrics and check for validity issues
    for outer_key, inner_data in impact_metrics.items():
        results_data = inner_data.get("results", inner_data)
        for inner_key, entry in results_data.items():
            # [...]

            # Check for various validity issues:
            # 1. Precision = 1.0 but no true positives
            if precision == 1.0 and tp == 0:
                # [...]

            # 2. F1 = 0.0 but false negatives > 0
            if f1 == 0.0 and fn > 0:
                # [...]

            # 3. Perfect metrics with no activity
            if precision == 1.0 and recall == 1.0 and tp == 0:
                # [...]

            # 4. Consistency checks
            if result_count != tp + fp:
                # [...]

    # 5. Compare queries between ablated and non-ablated runs
    for collection, queries in collection_queries.items():
        for query_id, query_variations in queries.items():
            if "ablated" in query_variations and "normal" in query_variations:
                # [...]
```

### Report Generation

The report generation was extended to include a validation section:

```python
if validation_results:
    f.write('## Validation Issues Detected\n\n')
    f.write(f'**⚠️ {len(validation_results)} potential issues were identified**\n\n')

    # Group by severity
    critical_issues = [issue for issue in validation_results if issue[2] == "critical"]
    warning_issues = [issue for issue in validation_results if issue[2] == "warning"]

    f.write(f'- Critical issues: {len(critical_issues)}\n')
    f.write(f'- Warning issues: {len(warning_issues)}\n\n')

    # Table of issues
    f.write('### Issue Summary\n\n')
    f.write('| Query ID | Issue | Severity |\n')
    f.write('|----------|-------|----------|\n')

    # [...]
```

## Testing

A dedicated test script `test_ablation_validation.py` was created to verify the validation functionality:

1. **Test Data Creation**: Creates synthetic data with known issues:
   - Precision = 1.0 with no true positives
   - F1 = 0.0 despite having false negatives
   - Inconsistent result count
   - Identical queries for ablated/non-ablated runs

2. **Validation Testing**: Verifies that all expected issues are detected

3. **Report Generation Testing**: Confirms that validation results are properly included in reports

## Extending the Validation System

The validation system was designed to be easily extensible. To add new validation checks:

1. Add a new detection condition in the `validate_ablation_results` function:
   ```python
   # New condition example
   if some_condition:
       flagged_cases.append((
           query_id,
           "Description of the issue",
           "severity",  # Either "critical" or "warning"
           aql_query
       ))
   ```

2. Update the test script with test cases for the new condition

3. Update documentation to explain the new check

## Next Steps

1. **Integration with Automated Workflow**: Make validation checks a standard part of ablation experiment runs

2. **Additional Validation Checks**: Consider adding detection for:
   - Invalid or missing collection references in queries
   - Unrealistic performance metrics for ablated collections
   - Truth data inconsistencies
   - Identical metrics between ablated/non-ablated cases

3. **Query Inspection Tools**: Enhance validation with:
   - Query parse tree analysis
   - Filter condition validation
   - Index usage verification

4. **Auto-fix Suggestions**: Implement suggestions for fixing common validation issues
