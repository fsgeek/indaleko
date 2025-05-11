#!/usr/bin/env python3
"""Validates ablation test results to identify potential data issues.

This script analyzes ablation test results and validates the metrics for potential
issues that could compromise scientific integrity. It helps identify cases where
metrics may be invalid or fabricated, such as precision=1.0 with no true positives,
or identical queries for ablated and non-ablated runs.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Import the validation function from analyze_results
from analyze_results import validate_ablation_results

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def validate_metrics_file(metrics_file, output_file=None):
    """Validate a metrics file for suspicious values.

    Args:
        metrics_file: Path to the impact_metrics.json file
        output_file: Path to write validation report (optional)

    Returns:
        list: List of validation issues
    """
    logger.info(f"Validating metrics file: {metrics_file}")

    # Load the metrics file
    try:
        with open(metrics_file, 'r') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metrics file: {e}")
        return None

    # Run validation
    validation_results = validate_ablation_results(data)

    # Count issues by severity
    critical_issues = [issue for issue in validation_results if issue[2] == "critical"]
    warning_issues = [issue for issue in validation_results if issue[2] == "warning"]

    logger.info(f"Found {len(validation_results)} validation issues:")
    logger.info(f"- Critical issues: {len(critical_issues)}")
    logger.info(f"- Warning issues: {len(warning_issues)}")

    # Generate validation report
    if output_file:
        with open(output_file, 'w') as f:
            f.write('# Ablation Results Validation Report\n\n')

            if validation_results:
                f.write(f'## Validation Issues Detected: {len(validation_results)}\n\n')
                f.write(f'- Critical issues: {len(critical_issues)}\n')
                f.write(f'- Warning issues: {len(warning_issues)}\n\n')

                # Table of issues
                f.write('## Issue Summary\n\n')
                f.write('| Query ID | Issue | Severity |\n')
                f.write('|----------|-------|----------|\n')

                for query_id, issue, severity, _ in validation_results:
                    # Truncate very long query IDs for table formatting
                    display_id = query_id if len(query_id) < 40 else query_id[:37] + "..."
                    f.write(f'| {display_id} | {issue} | {severity} |\n')

                f.write('\n')

                # Show detailed critical issues with queries
                if critical_issues:
                    f.write('## Critical Issues Details\n\n')
                    for i, (query_id, issue, severity, aql) in enumerate(critical_issues, 1):
                        f.write(f'### Critical Issue {i}: {issue}\n\n')
                        f.write(f'**Query ID:** {query_id}\n\n')
                        f.write('**AQL Query:**\n')
                        f.write('```aql\n')
                        f.write(aql)
                        f.write('\n```\n\n')

                # Scientific impact assessment
                f.write('## Impact on Experiment Validity\n\n')

                critical_pct = (len(critical_issues) / len(validation_results)) * 100 if validation_results else 0

                if critical_pct > 20:
                    f.write('⚠️ **HIGH RISK**: A significant percentage of results contain critical validation issues. ')
                    f.write('The experiment results may not be scientifically valid without addressing these issues.\n\n')
                elif critical_issues:
                    f.write('⚠️ **MODERATE RISK**: Some critical validation issues were detected. ')
                    f.write('These should be addressed before drawing final conclusions from the experiment results.\n\n')
                elif warning_issues:
                    f.write('⚠️ **LOW RISK**: Only warning-level validation issues were detected. ')
                    f.write('The experiment results are likely valid, but these issues should be reviewed to ensure full integrity.\n\n')

                # Recommendations
                f.write('## Recommendations\n\n')

                if critical_issues:
                    f.write('### Critical Issues to Address\n\n')
                    f.write('1. **Fix precision/recall calculation**: Address cases where precision=1.0 with no true positives\n')
                    f.write('2. **Investigate identical queries**: Fix cases where ablated and non-ablated queries are identical\n')
                    f.write('3. **Address metrics consistency issues**: Ensure metrics calculations follow expected formulas\n')
                    f.write('4. **Review ablation implementation**: Verify that collections are properly ablated during testing\n')
                    f.write('5. **Check truth data handling**: Ensure truth data is properly managed for all collections\n\n')

                if warning_issues:
                    f.write('### Warning Issues to Review\n\n')
                    f.write('1. **Review metrics calculation**: Ensure metrics calculations follow expected formulas\n')
                    f.write('2. **Check edge case handling**: Ensure edge cases are properly handled in the metrics calculation\n')
                    f.write('3. **Verify query execution**: Ensure queries are properly executed for ablated collections\n\n')
            else:
                f.write('✅ **No validation issues detected.**\n\n')
                f.write('The ablation results appear to be free from common data integrity problems.\n\n')

            logger.info(f"Validation report saved to {output_file}")

    return validation_results


def scan_results_directory(results_dir, output_dir=None):
    """Scan a directory of ablation results and validate all metrics files.

    Args:
        results_dir: Directory containing ablation results
        output_dir: Directory to write validation reports (optional)

    Returns:
        dict: Mapping of metrics file paths to validation issues
    """
    logger.info(f"Scanning results directory: {results_dir}")

    # Find all metrics files
    metrics_files = []
    for root, _, files in os.walk(results_dir):
        for file in files:
            if file in ["impact_metrics.json", "round_results.json"]:
                metrics_files.append(os.path.join(root, file))

    logger.info(f"Found {len(metrics_files)} metrics files")

    # Create output directory if needed
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Validate all metrics files
    results = {}
    for metrics_file in metrics_files:
        # Determine output file path if needed
        output_file = None
        if output_dir:
            # Extract relative path from metrics_file
            rel_path = os.path.relpath(metrics_file, results_dir)
            # Get directory and file parts
            rel_dir = os.path.dirname(rel_path)
            rel_name = os.path.basename(rel_path)
            # Create validation report filename
            rel_output = os.path.join(rel_dir, "validation_report.md")
            # Join with output_dir
            output_file = os.path.join(output_dir, rel_output)
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)

        validation_results = validate_metrics_file(metrics_file, output_file)
        results[metrics_file] = validation_results

    # Generate summary report
    if output_dir:
        with open(os.path.join(output_dir, "validation_summary.md"), 'w') as f:
            f.write('# Ablation Validation Summary Report\n\n')
            f.write(f'Validated {len(metrics_files)} metrics files\n\n')

            # Count issues across all files
            total_issues = sum(len(issues) if issues else 0 for issues in results.values())
            total_critical = sum(len([i for i in issues if i[2] == "critical"]) if issues else 0 for issues in results.values())
            total_warning = sum(len([i for i in issues if i[2] == "warning"]) if issues else 0 for issues in results.values())

            f.write(f'Total issues detected: {total_issues}\n')
            f.write(f'- Critical issues: {total_critical}\n')
            f.write(f'- Warning issues: {total_warning}\n\n')

            # Table of files with issue counts
            f.write('## Validation Results by File\n\n')
            f.write('| Metrics File | Total Issues | Critical | Warning |\n')
            f.write('|-------------|--------------|----------|--------|\n')

            for metrics_file, issues in results.items():
                rel_path = os.path.relpath(metrics_file, results_dir)
                total = len(issues) if issues else 0
                critical = len([i for i in issues if i[2] == "critical"]) if issues else 0
                warning = len([i for i in issues if i[2] == "warning"]) if issues else 0

                f.write(f'| {rel_path} | {total} | {critical} | {warning} |\n')

            f.write('\n')

            # Overall assessment
            f.write('## Overall Assessment\n\n')

            if total_critical > 0:
                f.write('⚠️ **ISSUES DETECTED**: The ablation results contain validation issues that should be addressed.\n\n')
                f.write('Please review the individual validation reports for each file to address specific issues.\n\n')
            else:
                f.write('✅ **NO CRITICAL ISSUES**: The ablation results appear to be free from critical data integrity problems.\n\n')
                if total_warning > 0:
                    f.write('However, some warning-level issues were detected that should be reviewed.\n\n')

            logger.info(f"Validation summary saved to {os.path.join(output_dir, 'validation_summary.md')}")

    return results


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Validate ablation test results")
    parser.add_argument(
        "--input-file",
        type=str,
        help="Path to a single impact_metrics.json file to validate"
    )
    parser.add_argument(
        "--results-dir",
        type=str,
        help="Path to a directory containing ablation results to validate"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        help="Directory to save validation reports"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Path to save validation report for a single file"
    )
    args = parser.parse_args()

    # Validate input
    if not args.input_file and not args.results_dir:
        logger.error("Either --input-file or --results-dir must be provided")
        parser.print_help()
        return 1

    # Validate a single metrics file
    if args.input_file:
        validate_metrics_file(args.input_file, args.output_file)

    # Scan a directory of ablation results
    if args.results_dir:
        scan_results_directory(args.results_dir, args.output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
