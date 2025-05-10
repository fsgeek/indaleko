#!/usr/bin/env python3
"""
Fixed ablation test runner with enhanced error handling.

This script runs the ablation experiment with proper initialization and error recovery,
ensuring that the test can complete successfully even with complex database state.
"""

import logging
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

# Set up path
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

from db.db_config import IndalekoDBConfig
from research.ablation.ablation_tester import AblationTester
from research.ablation.data_sanity_checker import DataSanityChecker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

def clear_truth_collection():
    """Clear the truth collection to start fresh."""
    logger.info("Clearing existing truth data...")
    db_config = IndalekoDBConfig()
    db = db_config.get_arangodb()
    
    truth_collection = "AblationQueryTruth"
    if db.has_collection(truth_collection):
        db.aql.execute(f"FOR doc IN {truth_collection} REMOVE doc IN {truth_collection}")
        logger.info(f"Cleared collection {truth_collection}")
    else:
        logger.info(f"Truth collection {truth_collection} does not exist yet")

def setup_initial_truth_data():
    """Generate initial truth data for all collections."""
    logger.info("Generating initial truth data...")
    
    # Import the generator script and run it
    from research.ablation.generate_initial_truth_data import generate_initial_truth_data
    
    success = generate_initial_truth_data()
    if success:
        logger.info("Successfully generated initial truth data")
        return True
    else:
        logger.error("Failed to generate initial truth data")
        return False

def run_ablation_tests(args):
    """Run the actual ablation tests."""
    logger.info("Running ablation tests...")
    
    # Define collections for testing based on args
    collections = []
    if args.all_collections:
        collections = [
            "AblationMusicActivity",
            "AblationLocationActivity",
            "AblationTaskActivity",
            "AblationCollaborationActivity",
            "AblationStorageActivity",
            "AblationMediaActivity",
        ]
    elif args.collections:
        collections = args.collections.split(",")
    else:
        logger.error("No collections specified. Use --all-collections or --collections")
        return False
    
    # Use command from run_comprehensive_ablation.py but with proper collection selection
    try:
        # Create output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"ablation_results_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Run the experiment
        from research.ablation.run_comprehensive_ablation import main as run_ablation
        
        # Build the command line arguments
        sys.argv = [
            "run_comprehensive_ablation.py",
            "--output-dir", output_dir,
            "--visualize",
            "--collections", ",".join(collections),
            "--count", str(args.count),
            "--queries", str(args.queries),
        ]
        
        if args.fixed_seed:
            sys.argv.extend(["--seed", "42"])
            
        logger.info(f"Running ablation with arguments: {sys.argv}")
        
        # Run the experiment
        run_ablation()
        
        logger.info(f"Ablation experiment completed successfully. Results in {output_dir}")
        return True
    
    except Exception as e:
        logger.exception(f"Error running ablation experiment: {e}")
        return False

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Run ablation tests with enhanced error handling")
    parser.add_argument("--all-collections", action="store_true", help="Test all available collections")
    parser.add_argument("--collections", type=str, help="Comma-separated list of collections to test")
    parser.add_argument("--skip-clear", action="store_true", help="Skip clearing the truth collection")
    parser.add_argument("--skip-initial-data", action="store_true", help="Skip generating initial truth data")
    parser.add_argument("--count", type=int, default=50, help="Number of synthetic records per collection")
    parser.add_argument("--queries", type=int, default=5, help="Number of queries to generate")
    parser.add_argument("--fixed-seed", action="store_true", help="Use a fixed seed (42) for reproducibility")
    args = parser.parse_args()
    
    logger.info("Starting fixed ablation test run")
    
    try:
        # Step 1: Clear truth collection (optional)
        if not args.skip_clear:
            clear_truth_collection()
        
        # Step 2: Set up initial truth data (optional)
        if not args.skip_initial_data:
            if not setup_initial_truth_data():
                logger.error("Failed to set up initial truth data, proceeding anyway")
        
        # Step 3: Run the ablation tests
        success = run_ablation_tests(args)
        
        if success:
            logger.info("Ablation tests completed successfully")
            return 0
        else:
            logger.error("Ablation tests failed")
            return 1
    
    except Exception as e:
        logger.exception(f"Unhandled exception during ablation test run: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())