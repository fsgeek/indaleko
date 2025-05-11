#!/usr/bin/env python3
"""
Convert JSON ablation result files to JSONL format.

This script takes a JSON file containing an array of objects
and converts it to JSONL format (one JSON object per line).
This makes it easier to process large result files and allows
for random access sampling of the data.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def json_to_jsonl(input_file, output_file=None):
    """
    Convert a JSON file containing an array to JSONL format.

    Args:
        input_file: Path to the input JSON file
        output_file: Path to the output JSONL file (default: input_file + '.jsonl')

    Returns:
        bool: True if conversion was successful
    """
    if output_file is None:
        output_file = str(input_file) + '.jsonl'

    logger.info(f"Converting {input_file} to JSONL format at {output_file}")

    try:
        # Read the JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)

        # Ensure the data is an array
        if not isinstance(data, list):
            # Special case: If the JSON contains a dict with a 'results' key containing an array
            if isinstance(data, dict) and 'results' in data and isinstance(data['results'], list):
                logger.info(f"Found results array in dictionary, extracting...")
                data = data['results']
            else:
                logger.error(f"JSON file does not contain an array at the top level")
                return False

        # Write each object as a separate line in the output file
        with open(output_file, 'w') as f:
            for obj in data:
                f.write(json.dumps(obj) + '\n')

        logger.info(f"Successfully converted {len(data)} objects to JSONL")
        logger.info(f"Output written to {output_file}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        return False

    except Exception as e:
        logger.error(f"Error during conversion: {e}")
        return False

def find_json_files(directory):
    """
    Find all JSON files in a directory and its subdirectories.

    Args:
        directory: Directory to search

    Returns:
        list: List of JSON file paths
    """
    json_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.json') and not file.endswith('.jsonl'):
                json_files.append(os.path.join(root, file))

    return json_files

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='Convert JSON files to JSONL format')
    parser.add_argument('input', help='Input JSON file or directory')
    parser.add_argument('--output', help='Output JSONL file (ignored when input is a directory)')
    parser.add_argument('--recursive', '-r', action='store_true',
                       help='Process all JSON files in directory recursively')

    args = parser.parse_args()

    # Check if the input exists
    if not os.path.exists(args.input):
        logger.error(f"Input does not exist: {args.input}")
        sys.exit(1)

    # Process a single file
    if os.path.isfile(args.input):
        success = json_to_jsonl(args.input, args.output)
        if not success:
            sys.exit(1)

    # Process a directory
    elif os.path.isdir(args.input):
        if args.recursive:
            # Find all JSON files
            json_files = find_json_files(args.input)
            logger.info(f"Found {len(json_files)} JSON files to convert")

            # Convert each file
            for json_file in json_files:
                json_to_jsonl(json_file)
        else:
            # Process only JSON files in the top level directory
            for file in os.listdir(args.input):
                file_path = os.path.join(args.input, file)
                if os.path.isfile(file_path) and file.endswith('.json') and not file.endswith('.jsonl'):
                    json_to_jsonl(file_path)

    logger.info("Conversion complete")

if __name__ == "__main__":
    main()
