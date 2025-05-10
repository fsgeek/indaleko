#!/usr/bin/env python3
"""Comprehensive Scientific Ablation Experiment Runner.

This script implements a full scientific experiment framework for ablation testing
that measures the impact of different activity data types on query results.
It includes test/control groups, power-set testing, and multi-round experiments.
"""

import argparse
import logging
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

# Import experimental components
try:
    from research.ablation.experimental.experiment_runner import ExperimentRunner
    experimental_available = True
except ImportError:
    experimental_available = False
    logging.warning("Experimental components not available. Full experiment features disabled.")

from db.db_config import IndalekoDBConfig
from research.ablation.data_sanity_checker import DataSanityChecker
from research.ablation.utils.uuid_utils import generate_deterministic_uuid


def setup_logging(verbose=False):
    """Set up logging for the experiment runner."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )


def clear_existing_data():
    """Clear existing data from all activity collections."""
    logging.info("Clearing existing data...")

    collections = [
        "AblationLocationActivity",
        "AblationTaskActivity",
        "AblationMusicActivity",
        "AblationCollaborationActivity",
        "AblationStorageActivity",
        "AblationMediaActivity",
    ]

    # Following fail-stop model - let exceptions propagate
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()

    for collection_name in collections:
        if db.has_collection(collection_name):
            db.aql.execute(f"FOR doc IN {collection_name} REMOVE doc IN {collection_name}")
            logging.info(f"Cleared collection {collection_name}")

    # Always clear the truth collection to avoid duplicate key errors between runs
    truth_collection = "AblationQueryTruth"
    if db.has_collection(truth_collection):
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
        logging.info(f"Cleared collection {truth_collection}")

    logging.info("Data cleared successfully")


def main():
    """Run the comprehensive ablation experiment."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run comprehensive ablation experiments")
    parser.add_argument("--clear", action="store_true", help="Clear existing data before running")
    parser.add_argument("--output-dir", type=str, help="Output directory for results")
    parser.add_argument("--visualize", action="store_true", help="Generate visualizations")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    # Experimental design parameters
    parser.add_argument("--rounds", type=int, default=3, help="Number of experimental rounds")
    parser.add_argument("--control-pct", type=float, default=0.2, help="Control group percentage (0.0-1.0)")
    parser.add_argument("--max-combos", type=int, default=100, help="Maximum collection combinations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--no-rotation", action="store_true", help="Disable collection rotation between rounds")
    
    # Data parameters
    parser.add_argument("--count", type=int, default=100, help="Number of test records per collection")
    parser.add_argument("--queries", type=int, default=10, help="Number of test queries per round")
    
    args = parser.parse_args()

    # Set up logging
    setup_logging(verbose=args.verbose)
    logger = logging.getLogger(__name__)

    # Create output directory with timestamp if not specified
    output_dir = args.output_dir
    if not output_dir:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"ablation_results_{timestamp}"

    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Starting comprehensive ablation experiment, results will be saved to {output_dir}")

    # Check if experimental components are available
    if not experimental_available:
        logger.error("CRITICAL: Experimental components required for comprehensive testing")
        logger.error("Please ensure research.ablation.experimental module is available")
        sys.exit(1)

    # Clear existing data if requested
    if args.clear:
        clear_existing_data()

    # Run data sanity check
    logger.info("Running data sanity check...")
    checker = DataSanityChecker(fail_fast=True)
    sanity_check_passed = checker.run_all_checks()
    if not sanity_check_passed:
        logger.error("Data sanity check failed")
        sys.exit(1)

    # Define collections for testing
    collections = [
        "AblationLocationActivity",
        "AblationTaskActivity", 
        "AblationMusicActivity",
        "AblationCollaborationActivity",
        "AblationStorageActivity",
        "AblationMediaActivity",
    ]

    # Initialize experiment runner
    experiment_runner = ExperimentRunner(
        collections=collections,
        output_dir=output_dir,
        rounds=args.rounds,
        control_percentage=args.control_pct,
        combination_limit=args.max_combos,
        seed=args.seed,
    )

    # Run the experiment
    success = experiment_runner.run_experiment()

    if success:
        logger.info("Experiment completed successfully")
        
        # Generate visualizations if requested
        if args.visualize:
            experiment_runner.visualize_experiment_results()
            
        logger.info(f"See {output_dir}/experiment_summary.md for detailed results")
    else:
        logger.error("Experiment failed")
        sys.exit(1)


if __name__ == "__main__":
    main()