#!/usr/bin/env python3
"""
Run a complete ablation experiment with the verified fixes.

This script runs a complete ablation experiment with the fixes for deterministic
truth data generation and query execution that have been verified to work correctly.
"""

import argparse
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))


def setup_logging(log_file=None):
    """Set up logging for the experiment runner."""
    handlers = [logging.StreamHandler(sys.stdout)]

    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s", handlers=handlers,
    )

    return logging.getLogger(__name__)


def run_verification_tests():
    """Run the verification tests to make sure everything is working properly."""
    logger = logging.getLogger(__name__)
    logger.info("Running verification tests...")

    # Run deterministic truth data generation test
    logger.info("Testing deterministic truth data generation...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "research.ablation.test_deterministic_truth_data",
            "--test-generation",
            "--collection",
            "AblationMusicActivity",
        ],
        capture_output=True,
        text=True, check=False,
    )

    if result.returncode != 0:
        logger.error("Deterministic truth data generation test failed!")
        logger.error(f"Output: {result.stdout}")
        logger.error(f"Error: {result.stderr}")
        return False

    logger.info("Deterministic truth data generation test passed!")

    # Run query execution matching test
    logger.info("Testing query execution matching...")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "research.ablation.test_deterministic_truth_data",
            "--test-execution",
            "--collection",
            "AblationMusicActivity",
        ],
        capture_output=True,
        text=True, check=False,
    )

    if result.returncode != 0:
        logger.error("Query execution matching test failed!")
        logger.error(f"Output: {result.stdout}")
        logger.error(f"Error: {result.stderr}")
        return False

    logger.info("Query execution matching test passed!")

    # Run cross-run consistency test
    logger.info("Testing cross-run consistency...")
    result = subprocess.run(
        [sys.executable, "-m", "research.ablation.test_deterministic_truth_data", "--test-cross-run"],
        capture_output=True,
        text=True, check=False,
    )

    if result.returncode != 0:
        logger.error("Cross-run consistency test failed!")
        logger.error(f"Output: {result.stdout}")
        logger.error(f"Error: {result.stderr}")
        return False

    logger.info("Cross-run consistency test passed!")

    logger.info("All verification tests passed!")
    return True


def run_experiment(
    output_dir, rounds=3, clear_existing=True, visualize=True, seed=42, control_pct=0.2, count=100, queries=10,
):
    """Run the full ablation experiment."""
    logger = logging.getLogger(__name__)
    logger.info(f"Running ablation experiment with output directory: {output_dir}")

    # Create output directory with timestamp if not provided
    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"ablation_results_{timestamp}"

    os.makedirs(output_dir, exist_ok=True)

    # Set up log file in the output directory
    log_file = os.path.join(output_dir, "experiment_log.txt")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s"))

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    # Build the command for running the experiment
    cmd = [
        sys.executable,
        "-m",
        "research.ablation.run_comprehensive_experiment",
        "--output-dir",
        output_dir,
        "--rounds",
        str(rounds),
        "--seed",
        str(seed),
        "--control-pct",
        str(control_pct),
        "--count",
        str(count),
        "--queries",
        str(queries),
    ]

    if clear_existing:
        cmd.append("--clear")

    if visualize:
        cmd.append("--visualize")

    # Run the experiment
    logger.info(f"Executing command: {' '.join(cmd)}")

    try:
        start_time = time.time()
        process = subprocess.run(cmd, capture_output=True, text=True, check=False)
        end_time = time.time()

        # Check if the experiment succeeded
        if process.returncode == 0:
            logger.info(f"Experiment completed successfully in {end_time - start_time:.2f} seconds")
            logger.info(f"Results saved to {output_dir}")

            # Log the experiment output
            logger.info("Experiment output:")
            for line in process.stdout.splitlines():
                logger.info(f"  {line}")

            return True
        else:
            logger.error(f"Experiment failed with return code {process.returncode}")
            logger.error("Experiment output:")
            for line in process.stdout.splitlines():
                logger.error(f"  {line}")

            logger.error("Experiment error output:")
            for line in process.stderr.splitlines():
                logger.error(f"  {line}")

            return False

    except Exception as e:
        logger.exception(f"Error running experiment: {e}")
        return False


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run a verified ablation experiment")
    parser.add_argument("--output-dir", type=str, help="Output directory for results")
    parser.add_argument("--rounds", type=int, default=3, help="Number of experimental rounds")
    parser.add_argument("--no-clear", action="store_true", help="Don't clear existing data")
    parser.add_argument("--no-visualize", action="store_true", help="Don't generate visualizations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--control-pct", type=float, default=0.2, help="Control group percentage (0.0-1.0)")
    parser.add_argument("--count", type=int, default=100, help="Number of test records per collection")
    parser.add_argument("--queries", type=int, default=10, help="Number of test queries per round")
    parser.add_argument("--skip-verification", action="store_true", help="Skip verification tests")
    parser.add_argument("--log-file", type=str, help="Log file path")
    args = parser.parse_args()

    # Create output directory with timestamp if not provided
    if not args.output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output_dir = f"ablation_results_{timestamp}"

    os.makedirs(args.output_dir, exist_ok=True)

    # Set up logging
    log_file = args.log_file or os.path.join(args.output_dir, "experiment_log.txt")
    logger = setup_logging(log_file)

    logger.info("Starting verified ablation experiment")
    logger.info(f"Output directory: {args.output_dir}")
    logger.info(f"Rounds: {args.rounds}")
    logger.info(f"Clear existing: {not args.no_clear}")
    logger.info(f"Visualize: {not args.no_visualize}")
    logger.info(f"Seed: {args.seed}")
    logger.info(f"Control percentage: {args.control_pct}")
    logger.info(f"Record count: {args.count}")
    logger.info(f"Query count: {args.queries}")

    # Run verification tests
    if not args.skip_verification:
        logger.info("Running verification tests...")
        if not run_verification_tests():
            logger.error("Verification tests failed! Cannot proceed with the experiment.")
            return 1
    else:
        logger.info("Skipping verification tests")

    # Run the experiment
    success = run_experiment(
        output_dir=args.output_dir,
        rounds=args.rounds,
        clear_existing=not args.no_clear,
        visualize=not args.no_visualize,
        seed=args.seed,
        control_pct=args.control_pct,
        count=args.count,
        queries=args.queries,
    )

    if success:
        logger.info(f"Experiment completed successfully. Results in {args.output_dir}")
        return 0
    else:
        logger.error("Experiment failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
