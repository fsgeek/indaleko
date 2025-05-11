#!/usr/bin/env python3
"""Minimal experiment runner for testing ablation framework."""

import argparse
import logging
import os
import sys
from pathlib import Path

# Set up environment
if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

def main():
    """Run minimal experiment with debug settings."""
    # Configure command-line arguments
    parser = argparse.ArgumentParser(description="Run a minimal ablation experiment")
    parser.add_argument("--count", type=int, default=2, help="Number of entities per collection")
    parser.add_argument("--queries", type=int, default=2, help="Number of queries to generate")
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(level=logging.DEBUG, 
                      format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
    logger = logging.getLogger(__name__)
    
    logger.info("Running minimal experiment with debug settings...")
    logger.info(f"Entity count: {args.count}, Queries: {args.queries}")
    
    # Run the experiment with minimal settings to see our debugging messages
    # Use python -m to ensure module imports work correctly
    cmd = f"python -m research.ablation.run_comprehensive_experiment " \
          f"--rounds 1 --control-pct 0.3 --count {args.count} --queries {args.queries} " \
          f"--max-combos 3 --clear --visualize"
    
    logger.info(f"Executing command: {cmd}")
    
    # We use os.system instead of subprocess to ensure output is streamed in real-time
    exit_code = os.system(cmd)
    
    logger.info(f"Experiment completed with exit code: {exit_code}")

if __name__ == "__main__":
    main()