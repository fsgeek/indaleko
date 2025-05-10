#!/bin/bash
# Run the fixed ablation test with improved error handling
# This script simplifies running the ablation framework with proper setup

# Default values
ALL_COLLECTIONS=false
COLLECTIONS=""
SKIP_CLEAR=false
SKIP_INIT=false
COUNT=50
QUERIES=5
FIXED_SEED=false

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --all-collections)
      ALL_COLLECTIONS=true
      shift
      ;;
    --collections)
      COLLECTIONS="$2"
      shift 2
      ;;
    --skip-clear)
      SKIP_CLEAR=true
      shift
      ;;
    --skip-initial-data)
      SKIP_INIT=true
      shift
      ;;
    --count)
      COUNT="$2"
      shift 2
      ;;
    --queries)
      QUERIES="$2"
      shift 2
      ;;
    --fixed-seed)
      FIXED_SEED=true
      shift
      ;;
    --help)
      echo "Usage: $0 [options]"
      echo "Options:"
      echo "  --all-collections     Test all available collections"
      echo "  --collections COL1,COL2  Specify collections to test (comma-separated)"
      echo "  --skip-clear          Skip clearing the truth collection"
      echo "  --skip-initial-data   Skip generating initial truth data"
      echo "  --count N             Number of synthetic records per collection (default: 50)"
      echo "  --queries N           Number of queries to generate (default: 5)"
      echo "  --fixed-seed          Use a fixed seed (42) for reproducibility"
      echo "  --help                Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Build command
CMD="python run_fixed_ablation_test.py"

if [[ "$ALL_COLLECTIONS" == true ]]; then
  CMD="$CMD --all-collections"
elif [[ ! -z "$COLLECTIONS" ]]; then
  CMD="$CMD --collections $COLLECTIONS"
else
  echo "Error: Must specify either --all-collections or --collections"
  exit 1
fi

if [[ "$SKIP_CLEAR" == true ]]; then
  CMD="$CMD --skip-clear"
fi

if [[ "$SKIP_INIT" == true ]]; then
  CMD="$CMD --skip-initial-data"
fi

if [[ "$FIXED_SEED" == true ]]; then
  CMD="$CMD --fixed-seed"
fi

CMD="$CMD --count $COUNT --queries $QUERIES"

# Run the script
echo "Running command: $CMD"
exec $CMD