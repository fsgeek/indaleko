#!/usr/bin/env python3
"""
Query Analysis Tool for Ablation Experiments

This script:
1. Extracts unique AQL queries from ablation_results_comprehensive/impact_metrics.json
2. Runs EXPLAIN on each query to analyze execution plans
3. Identifies potential index optimizations based on execution plans
4. Provides recommendations for database optimization

Usage:
    python analyze_ablation_queries.py [--input-file PATH] [--output-file PATH]
"""

import argparse
import json
import os
import re
import sys
import time

from collections import defaultdict
from icecream import ic
from pathlib import Path
from textwrap import dedent

if os.environ.get("INDALEKO_ROOT") is None:
    current_path = Path(__file__).parent.resolve()
    while not (Path(current_path) / "Indaleko.py").exists():
        current_path = Path(current_path).parent
    os.environ["INDALEKO_ROOT"] = str(current_path)
    sys.path.insert(0, str(current_path))

# pylint: disable=wrong-import-position
from db.db_config import IndalekoDBConfig


# pylint: enable=wrong-import-position

def extract_queries(input_file: str) -> list[dict[str, object]]:
    """
    Extract unique AQL queries from impact metrics file.

    Args:
        input_file: Path to impact_metrics.json

    Returns:
        List of unique query information dictionaries
    """
    ic(f"Extracting queries from {input_file}")

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Dictionary to track unique queries with their bind variables
    unique_queries = {}

    # Extract all queries from the impact metrics
    for query_id, query_data in data.items():
        query_text = query_data.get("query_text", "")
        for result_key, result_data in query_data.get("results", {}).items():
            aql_query = result_data.get("aql_query", "")

            if not aql_query:
                continue

            # Extract bind variables if present
            bind_vars = {}
            for var in re.findall(r'@(\w+)', aql_query):
                # Check typical bind variables from the test data
                if var == "truth_keys" and "truth_data" in result_data:
                    bind_vars[var] = result_data["truth_data"]
                elif var == "from_timestamp":
                    # Use a reasonable timestamp for testing
                    bind_vars[var] = int(time.time()) - 86400  # 1 day ago
                elif var == "to_timestamp":
                    bind_vars[var] = int(time.time())  # Now
                elif var == "artist" and query_text and "artist" in query_text.lower():
                    # Extract potential artist name from query text
                    bind_vars[var] = re.search(r'"([^"]+)"', query_text).group(1) if re.search(r'"([^"]+)"', query_text) else "Taylor Swift"
                elif var == "location_name" and query_text and "location" in query_text.lower():
                    bind_vars[var] = "New York"
                elif var == "location_type":
                    bind_vars[var] = "office"
                elif var == "task_type":
                    bind_vars[var] = "action_item"
                elif var == "event_type":
                    bind_vars[var] = "meeting"
                elif var == "file_type":
                    bind_vars[var] = "document"
                elif var == "path_fragment":
                    bind_vars[var] = "%documents%"
                elif var == "participant":
                    bind_vars[var] = "Sarah"
                else:
                    # Default placeholder for unknown bind vars
                    bind_vars[var] = f"test_{var}"

            # Create a unique key for this query using the stripped query text
            query_key = re.sub(r'\s+', ' ', aql_query).strip()

            # Store with collection information
            collection_match = re.search(r'FOR doc IN (\w+)', aql_query)
            collection = collection_match.group(1) if collection_match else "Unknown"

            if query_key not in unique_queries:
                unique_queries[query_key] = {
                    "query": aql_query,
                    "bind_vars": bind_vars,
                    "collection": collection,
                    "queries": [query_text],
                    "count": 1
                }
            else:
                unique_queries[query_key]["count"] += 1
                if query_text not in unique_queries[query_key]["queries"]:
                    unique_queries[query_key]["queries"].append(query_text)

    # Convert to list
    result = list(unique_queries.values())

    ic(f"Extracted {len(result)} unique queries from impact metrics")
    if os.environ.get("EXPLAIN_LOG") == "detailed":
        for item in result:
            query = " ".join(item["query"].split())
            bind_vars = item["bind_vars"]
            ic(f"Query: {query} | bind_vars: {bind_vars}")
    return result


def analyze_query_patterns(queries: list[dict[str, object]]) -> dict[str, object]:
    """
    Analyze query patterns to identify optimization opportunities.

    Args:
        queries: List of unique query information dictionaries

    Returns:
        Analysis results
    """
    ic("Analyzing query patterns")

    # Initialize analysis structures
    collections_used = defaultdict(int)
    filter_attributes = defaultdict(lambda: defaultdict(int))
    filter_patterns = defaultdict(int)
    bind_vars_used = defaultdict(int)

    # Analyze each query
    for query_info in queries:
        query = query_info["query"]
        collection = query_info["collection"]
        collections_used[collection] += query_info["count"]

        # Extract FILTER conditions
        filter_clauses = re.findall(r'FILTER\s+([^)]+?)(?:\s+RETURN|\s+LIMIT|\s+SORT|$)', query, re.DOTALL)

        for filter_clause in filter_clauses:
            # Count filter patterns
            filter_pattern = re.sub(r'@\w+', '@param', filter_clause)
            filter_pattern = re.sub(r'"[^"]+"', '"value"', filter_pattern)
            filter_patterns[filter_pattern] += 1

            # Extract attributes used in filters
            for attr_match in re.finditer(r'doc\.(\w+(?:\[\*\](?:\.\w+)?)?)', filter_clause):
                attr = attr_match.group(1)
                filter_attributes[collection][attr] += 1

        # Count bind variables
        for var in query_info["bind_vars"]:
            bind_vars_used[var] += 1

    # Prepare analysis results
    analysis = {
        "collections_used": dict(collections_used),
        "filter_attributes": {k: dict(v) for k, v in filter_attributes.items()},
        "filter_patterns": dict(filter_patterns),
        "bind_vars_used": dict(bind_vars_used),
        "index_recommendations": {}
    }

    # Generate index recommendations
    for collection, attributes in filter_attributes.items():
        # Sort attributes by usage count
        sorted_attrs = sorted(attributes.items(), key=lambda x: x[1], reverse=True)

        # Recommend indices for frequently used attributes
        recommended_indices = []
        for attr, count in sorted_attrs:
            if count >= 2:  # Recommend index if used in at least 2 queries
                if '[*]' in attr:
                    # Array attribute - needs special handling
                    base_attr = attr.split('[*]')[0]
                    if '.' in attr:
                        # Array object attribute (e.g., participants[*].name)
                        subattr = attr.split('.')[-1]
                        recommended_indices.append({
                            "fields": [f"{base_attr}[*].{subattr}"],
                            "type": "persistent",
                            "reason": f"Used in {count} filter conditions"
                        })
                    else:
                        # Simple array attribute
                        recommended_indices.append({
                            "fields": [attr],
                            "type": "persistent",
                            "reason": f"Used in {count} filter conditions"
                        })
                else:
                    # Regular attribute
                    recommended_indices.append({
                        "fields": [attr],
                        "type": "persistent",
                        "reason": f"Used in {count} filter conditions"
                    })

        # Add compound indices for common filter combinations
        # This would require more sophisticated analysis of filter_patterns

        analysis["index_recommendations"][collection] = recommended_indices

    return analysis


def run_query_explains(queries: list[dict[str, object]]) -> list[dict[str, object]]:
    """
    Run EXPLAIN on each query to analyze execution plans.

    Args:
        queries: List of unique query information dictionaries

    Returns:
        List of queries with added explain results
    """
    ic("Running EXPLAIN on queries")

    # Connect to ArangoDB
    try:
        db_config = IndalekoDBConfig()
        db = db_config.get_arangodb()
        ic("Connected to ArangoDB")
    except Exception as e:
        ic(f"Failed to connect to ArangoDB: {e}")
        print(f"ERROR: Failed to connect to ArangoDB: {e}")
        sys.exit(1)  # Fail-stop approach as per CLAUDE.md guidelines

    # Run EXPLAIN on each query
    for query_info in queries:
        try:
            # Skip explain for empty queries
            if not query_info["query"].strip():
                ic(f"Skipping empty query")
                continue

            explain_result = db.aql.explain(
                query_info["query"],
                bind_vars=query_info.get("bind_vars", {})
            )

            query_info["explain"] = explain_result
            if "detailed" in os.environ.get("EXPLAIN_LOG", ""):
                ic(
                    "EXPLAIN result for query: %s, bind_vars: %s -> \n\t%s\n\n",
                    query_info["query"],
                    query_info.get("bind_vars", {}),
                    json.dumps(explain_result, indent=2)
                )

            # Extract key information for easier analysis
            explain_summary = {
                "estimated_cost": explain_result.get("estimatedCost", 0),
                "estimated_nr_items": explain_result.get("estimatedNrItems", 0),
                "full_collection_scan": False,
                "index_usage": [],
                "complexity": 0,
                "nodes": len(explain_result.get("plan", {}).get("nodes", [])),
            }

            # Analyze plan nodes to detect full collection scans and index usage
            nodes = explain_result.get("plan", {}).get("nodes", [])
            for node in nodes:
                # Check for collection full scans
                if node.get("type") == "EnumerateCollectionNode" and not node.get("indexId"):
                    explain_summary["full_collection_scan"] = True
                    explain_summary["complexity"] += 10  # High complexity for full scans

                # Check for index usage
                if node.get("type") == "IndexNode" or (node.get("type") == "EnumerateCollectionNode" and node.get("indexId")):
                    index_info = {
                        "index_id": node.get("indexId", "unknown"),
                        "index_type": node.get("indexType", "unknown") if "indexType" in node else "persistent",
                        "collection": node.get("collection", query_info["collection"]),
                        "fields": node.get("indexes", [{}])[0].get("fields", []) if node.get("indexes") else []
                    }
                    explain_summary["index_usage"].append(index_info)
                    explain_summary["complexity"] += 2  # Lower complexity when using indices

                # Look for expensive operations
                if node.get("type") in ["SortNode", "TraversalNode", "ShortestPathNode"]:
                    explain_summary["complexity"] += 5

                # Check for JOINs and subqueries
                if node.get("type") in ["JoinNode", "SubqueryNode"]:
                    explain_summary["complexity"] += 8

            # Store the summary
            query_info["explain_summary"] = explain_summary

            ic(f"Query complexity: {explain_summary['complexity']}, "
               f"Full scan: {explain_summary['full_collection_scan']}, "
               f"Cost: {explain_summary['estimated_cost']}")

        except Exception as e:
            ic(f"Failed to explain query: {query_info['query']}: {e}")
            # Add error info but don't stop - continue with other queries
            query_info["explain_error"] = str(e)
            query_info["explain_summary"] = {
                "error": str(e),
                "full_collection_scan": True,  # Assume worst case
                "complexity": 15,  # High complexity for failed queries
                "estimated_cost": 9999
            }

    return queries


def generate_optimization_recommendations(analyzed_queries: list[dict[str, object]],
                                         pattern_analysis: dict[str, object]) -> dict[str, object]:
    """
    Generate optimization recommendations based on query analysis.

    Args:
        analyzed_queries: List of queries with EXPLAIN results
        pattern_analysis: Analysis of query patterns

    Returns:
        Dictionary of recommendations
    """
    ic("Generating optimization recommendations")

    # Initialize recommendations
    recommendations = {
        "indexes_to_add": {},
        "slow_queries": [],
        "full_scan_queries": [],
        "complex_queries": [],
        "overall_suggestions": [],
        "view_recommendations": {}
    }

    # Get initial index recommendations from pattern analysis
    recommendations["indexes_to_add"] = pattern_analysis["index_recommendations"]

    # Look for fields that appear in FILTER conditions for index creation
    improved_index_recommendations = {}

    # Track query complexity by collection
    collection_complexity = defaultdict(list)
    collection_full_scans = defaultdict(int)
    collection_query_counts = defaultdict(int)

    # Find slow queries, full scan queries, and complex queries
    for query_info in analyzed_queries:
        if "explain_summary" not in query_info:
            continue

        summary = query_info["explain_summary"]
        collection = query_info["collection"]
        collection_query_counts[collection] += 1

        # Track complexity metrics by collection
        complexity = summary.get("complexity", 0)
        collection_complexity[collection].append(complexity)

        # Check for high cost queries
        if "estimated_cost" in summary and summary["estimated_cost"] > 1000:
            # Extract potential filter attributes from query to suggest indexes
            filter_attrs = extract_filter_attributes_from_query(query_info["query"], collection)
            optimization_suggestion = "Consider adding indexes for these fields: " + ", ".join(filter_attrs) if filter_attrs else "Consider adding indexes for filter attributes"

            recommendations["slow_queries"].append({
                "collection": collection,
                "cost": summary["estimated_cost"],
                "complexity": complexity,
                "query": query_info["query"],
                "sample_nl_query": query_info["queries"][0] if query_info["queries"] else "",
                "optimization_suggestion": optimization_suggestion,
                "potential_index_fields": filter_attrs
            })

            # Add suggested index to recommendations if it doesn't exist
            if collection not in improved_index_recommendations:
                improved_index_recommendations[collection] = []

            if filter_attrs:
                # Check if this would be a new index recommendation
                existing_indices = [idx["fields"] for idx in improved_index_recommendations.get(collection, [])]
                if filter_attrs not in existing_indices:
                    improved_index_recommendations[collection].append({
                        "fields": filter_attrs,
                        "type": "persistent",
                        "reason": f"Used in high-cost query (cost: {summary['estimated_cost']})"
                    })

        # Check for full collection scans
        if "full_collection_scan" in summary and summary["full_collection_scan"]:
            collection_full_scans[collection] += 1

            # Extract potential filter attributes from query
            filter_attrs = extract_filter_attributes_from_query(query_info["query"], collection)

            recommendations["full_scan_queries"].append({
                "collection": collection,
                "query": query_info["query"],
                "sample_nl_query": query_info["queries"][0] if query_info["queries"] else "",
                "potential_index_fields": filter_attrs,
                "estimated_cost": summary.get("estimated_cost", 0)
            })

            # Add suggested index to recommendations if it doesn't exist
            if collection not in improved_index_recommendations:
                improved_index_recommendations[collection] = []

            if filter_attrs:
                # Check if this would be a new index recommendation
                existing_indices = [idx["fields"] for idx in improved_index_recommendations.get(collection, [])]
                if filter_attrs not in existing_indices:
                    improved_index_recommendations[collection].append({
                        "fields": filter_attrs,
                        "type": "persistent",
                        "reason": "Used in full collection scan query"
                    })

        # Check for complex queries (high node count, joins, etc.)
        if complexity > 10:
            recommendations["complex_queries"].append({
                "collection": collection,
                "complexity": complexity,
                "query": query_info["query"],
                "sample_nl_query": query_info["queries"][0] if query_info["queries"] else "",
                "node_count": summary.get("nodes", 0),
                "estimated_cost": summary.get("estimated_cost", 0)
            })

    # Combine pattern-based and execution-plan-based index recommendations
    for collection, indices in pattern_analysis["index_recommendations"].items():
        if collection not in improved_index_recommendations:
            improved_index_recommendations[collection] = []

        for idx in indices:
            # Check if this index is already in our improved recommendations
            if idx["fields"] not in [existing_idx["fields"] for existing_idx in improved_index_recommendations[collection]]:
                improved_index_recommendations[collection].append(idx)

    # Update recommendations with improved index recommendations
    recommendations["indexes_to_add"] = improved_index_recommendations

    # Generate view recommendations for text-heavy collections
    view_candidates = {}
    for collection, attrs in pattern_analysis["filter_attributes"].items():
        text_fields = []
        for attr, count in attrs.items():
            # Look for likely text fields based on attribute name
            if any(text_indicator in attr.lower() for text_indicator in
                   ["name", "title", "description", "text", "comment", "content",
                    "message", "note", "body", "summary", "author", "artist", "track"]):
                text_fields.append(attr)

        if text_fields:
            view_candidates[collection] = text_fields

    # Generate view recommendations for collections with text fields
    for collection, fields in view_candidates.items():
        view_name = f"{collection}_view"
        recommendations["view_recommendations"][view_name] = {
            "collection": collection,
            "fields": fields,
            "analyzers": ["text_en", "identity"],  # Common analyzers
            "reason": f"Collection {collection} has text fields that could benefit from full-text search"
        }

    # Generate overall suggestions based on analysis

    # Full scan suggestion
    total_queries = len(analyzed_queries)
    full_scan_query_count = len(recommendations["full_scan_queries"])
    if full_scan_query_count > 0:
        full_scan_percentage = (full_scan_query_count / total_queries) * 100
        recommendations["overall_suggestions"].append(
            f"{full_scan_percentage:.1f}% of queries ({full_scan_query_count}/{total_queries}) "
            f"perform full collection scans. Adding the recommended indexes could significantly improve performance."
        )

    # Collection-specific suggestions
    for collection, counts in collection_query_counts.items():
        if collection in collection_full_scans and collection_full_scans[collection] > 0:
            full_scan_pct = (collection_full_scans[collection] / counts) * 100
            if full_scan_pct > 50:
                recommendations["overall_suggestions"].append(
                    f"Collection '{collection}' has {full_scan_pct:.1f}% of queries performing full scans. "
                    f"This collection is a high-priority candidate for indexing."
                )

        # Check for collections with high complexity
        if collection in collection_complexity and collection_complexity[collection]:
            avg_complexity = sum(collection_complexity[collection]) / len(collection_complexity[collection])
            if avg_complexity > 8:
                recommendations["overall_suggestions"].append(
                    f"Queries on collection '{collection}' have high average complexity ({avg_complexity:.1f}). "
                    f"Consider refactoring queries or adding specialized indexes."
                )

    # Collections without indexes
    collections_without_indexes = [
        coll for coll, queries in pattern_analysis["collections_used"].items()
        if coll not in recommendations["indexes_to_add"] or not recommendations["indexes_to_add"][coll]
    ]

    if collections_without_indexes:
        recommendations["overall_suggestions"].append(
            f"Collections without index recommendations: {', '.join(collections_without_indexes)}. "
            "Consider manual inspection of query patterns."
        )

    # Add view recommendations if needed
    if recommendations["view_recommendations"] and "ArangoDB ArangoSearch View" not in " ".join(recommendations["overall_suggestions"]):
        view_collections = ", ".join(recommendations["view_recommendations"].keys())
        recommendations["overall_suggestions"].append(
            f"Consider creating ArangoDB ArangoSearch Views for collections: {view_collections}. "
            "This could improve performance for queries involving text search or complex filtering."
        )

    # Add query count and stats to overall suggestions
    recommendations["overall_suggestions"].insert(0,
        f"Analysis based on {total_queries} unique queries across {len(pattern_analysis['collections_used'])} collections."
    )

    return recommendations


def extract_filter_attributes_from_query(query_text: str, collection: str) -> list[str]:
    """
    Extract potential filter attributes from a query.

    Args:
        query_text: The AQL query text
        collection: The collection being queried

    Returns:
        List of attribute names that might benefit from indexing
    """
    # Look for doc.attribute patterns in FILTER clauses
    filter_attrs = []

    # First, extract FILTER clauses
    filter_clauses = re.findall(r'FILTER\s+([^)]+?)(?:\s+RETURN|\s+LIMIT|\s+SORT|$)', query_text, re.DOTALL)

    for filter_clause in filter_clauses:
        # Find all doc.attribute patterns
        for attr_match in re.finditer(r'doc\.(\w+(?:\.\w+)*)', filter_clause):
            attr = attr_match.group(1)
            # Skip array access like doc.items[0]
            if '[' not in attr and attr not in filter_attrs:
                filter_attrs.append(attr)

    return filter_attrs


def format_output(queries: list[dict[str, object]],
                 analysis: dict[str, object],
                 recommendations: dict[str, object]) -> dict[str, object]:
    """
    Format the analysis results for output.

    Args:
        queries: List of unique queries with explain results
        analysis: Query pattern analysis results
        recommendations: Optimization recommendations

    Returns:
        Formatted output dictionary
    """
    # Prepare summary statistics
    collections_summary = []
    for collection, count in analysis["collections_used"].items():
        collection_summary = {
            "collection": collection,
            "query_count": count,
            "attributes_used": analysis["filter_attributes"].get(collection, {}),
            "recommended_indexes": recommendations["indexes_to_add"].get(collection, [])
        }
        collections_summary.append(collection_summary)

    # Sort collections by query count
    collections_summary.sort(key=lambda x: x["query_count"], reverse=True)

    # Calculate query statistics
    query_stats = {
        "total_unique_queries": len(queries),
        "queries_with_full_scans": len(recommendations["full_scan_queries"]),
        "slow_queries": len(recommendations["slow_queries"]),
        "complex_queries": len(recommendations["complex_queries"]),
        "collections_analyzed": len(analysis["collections_used"]),
        "filter_patterns_found": len(analysis["filter_patterns"]),
        "bind_variables_used": len(analysis["bind_vars_used"])
    }

    # Generate index creation script
    index_script = "// ArangoDB index creation script\n"
    for collection, indexes in recommendations["indexes_to_add"].items():
        for idx in indexes:
            if not idx.get("fields"):
                continue
            fields_str = ", ".join([f'"{field}"' for field in idx["fields"]])
            index_script += f'db.{collection}.ensureIndex({{ type: "{idx["type"]}", fields: [{fields_str}] }});\n'

    # Generate view creation script
    view_script = "// ArangoDB view creation script\n"
    for view_name, view_config in recommendations["view_recommendations"].items():
        collection = view_config["collection"]
        fields = view_config["fields"]
        analyzers = view_config["analyzers"]

        view_script += f'// Create view for collection {collection}\n'
        view_script += f'db._createView("{view_name}", "arangosearch", {{\n'
        view_script += f'  "links": {{\n'
        view_script += f'    "{collection}": {{\n'
        view_script += f'      "includeAllFields": false,\n'
        view_script += f'      "fields": {{\n'

        for field in fields:
            view_script += f'        "{field}": {{\n'
            view_script += f'          "analyzers": ["' + '", "'.join(analyzers) + '"],\n'
            view_script += f'          "includeAllFields": false\n'
            view_script += f'        }},\n'

        view_script += f'      }}\n'
        view_script += f'    }}\n'
        view_script += f'  }}\n'
        view_script += f'}});\n\n'

    # Generate markdown summary report
    markdown_report = f"""# Ablation Query Analysis Report
Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}

## Summary Statistics
- Total unique queries analyzed: {query_stats['total_unique_queries']}
- Number of collections analyzed: {query_stats['collections_analyzed']}
- Queries performing full collection scans: {query_stats['queries_with_full_scans']} ({query_stats['queries_with_full_scans']/query_stats['total_unique_queries']*100:.1f}%)
- High-cost queries identified: {query_stats['slow_queries']}
- Complex queries identified: {query_stats['complex_queries']}

## Key Recommendations

"""
    for suggestion in recommendations["overall_suggestions"]:
        markdown_report += f"- {suggestion}\n"

    markdown_report += "\n## Collection Analysis\n\n"

    for collection in collections_summary:
        markdown_report += f"### {collection['collection']}\n"
        markdown_report += f"- **Query count**: {collection['query_count']}\n"

        if collection["recommended_indexes"]:
            markdown_report += "- **Recommended indexes**:\n"
            for idx in collection["recommended_indexes"]:
                fields_str = ", ".join(idx["fields"])
                reason = idx.get("reason", "frequently used in queries")
                markdown_report += f"  - Fields: `{fields_str}` ({reason})\n"
        else:
            markdown_report += "- No specific index recommendations.\n"

        # Add most used attributes
        if collection["attributes_used"]:
            markdown_report += "- **Top filter attributes**:\n"
            sorted_attrs = sorted(collection["attributes_used"].items(), key=lambda x: x[1], reverse=True)[:5]
            for attr, count in sorted_attrs:
                markdown_report += f"  - `{attr}` (used in {count} queries)\n"

        markdown_report += "\n"

    # Add slow query section if we have any
    if recommendations["slow_queries"]:
        markdown_report += "## Slow Queries\n\n"
        for i, query in enumerate(recommendations["slow_queries"][:5]):  # Show top 5
            markdown_report += f"### Slow Query {i+1}\n"
            markdown_report += f"- **Collection**: {query['collection']}\n"
            markdown_report += f"- **Estimated cost**: {query['cost']}\n"
            markdown_report += f"- **Sample query**: {query['sample_nl_query']}\n"
            markdown_report += f"- **Recommendation**: {query['optimization_suggestion']}\n"
            markdown_report += f"- **AQL**: ```{query['query']}```\n\n"

    # Add view recommendations if we have any
    if recommendations["view_recommendations"]:
        markdown_report += "## View Recommendations\n\n"
        for view_name, config in recommendations["view_recommendations"].items():
            markdown_report += f"### {view_name}\n"
            markdown_report += f"- **Collection**: {config['collection']}\n"
            markdown_report += f"- **Fields**: {', '.join(config['fields'])}\n"
            markdown_report += f"- **Reason**: {config['reason']}\n\n"

    # Prepare formatted output
    output = {
        "query_analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "query_statistics": query_stats,
        "collections_summary": collections_summary,
        "recommendations": {
            "overall_suggestions": recommendations["overall_suggestions"],
            "slow_queries": recommendations["slow_queries"],
            "full_scan_queries": recommendations["full_scan_queries"],
            "complex_queries": recommendations["complex_queries"],
            "view_recommendations": recommendations["view_recommendations"]
        },
        "index_creation_script": index_script,
        "view_creation_script": view_script,
        "markdown_report": markdown_report,
        "detailed_queries": [
            {
                "query": q["query"],
                "collection": q["collection"],
                "sample_nl_query": q["queries"][0] if q["queries"] else "",
                "usage_count": q["count"],
                "complexity": q.get("explain_summary", {}).get("complexity", 0),
                "estimated_cost": q.get("explain_summary", {}).get("estimated_cost", 0),
                "full_collection_scan": q.get("explain_summary", {}).get("full_collection_scan", False),
                "bind_vars": q.get("bind_vars", {})
            }
            for q in queries
        ]
    }

    return output


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Analyze AQL queries from ablation experiments and recommend optimizations"
    )
    parser.add_argument(
        "--input-file",
        default="/mnt/c/Users/TonyMason/source/repos/indaleko/claude/ablation_results_comprehensive/impact_metrics.json",
        help="Path to impact_metrics.json file"
    )
    parser.add_argument(
        "--output-file",
        default="ablation_query_analysis.json",
        help="Path to output analysis file"
    )
    parser.add_argument(
        "--markdown-report",
        default="ablation_query_analysis.md",
        help="Path to markdown report file"
    )
    parser.add_argument(
        "--index-script",
        default="create_ablation_indices.js",
        help="Path to output ArangoDB index creation script"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--skip-explain",
        action="store_true",
        help="Skip running EXPLAIN on queries (faster but less detailed analysis)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit analysis to top N queries (useful for testing)"
    )
    args = parser.parse_args()

    if args.verbose:
        os.environ["EXPLAIN_LOG"] = "detailed"

    print(f"Starting analysis of AQL queries from {args.input_file}")

    # Step 1: Extract unique queries from impact metrics
    unique_queries = extract_queries(args.input_file)
    if not unique_queries:
        print("ERROR: No queries found in impact metrics file")
        return 1

    print(f"Extracted {len(unique_queries)} unique queries for analysis")

    # Apply limit if specified
    if args.limit and args.limit > 0 and args.limit < len(unique_queries):
        print(f"Limiting analysis to top {args.limit} queries")
        # Sort by count to get most frequent queries first
        unique_queries.sort(key=lambda x: x.get("count", 0), reverse=True)
        unique_queries = unique_queries[:args.limit]

    # Step 2: Analyze query patterns
    print("Analyzing query patterns...")
    pattern_analysis = analyze_query_patterns(unique_queries)
    print(f"Found patterns across {len(pattern_analysis['collections_used'])} collections")

    # Step 3: Run EXPLAIN on queries (if not skipped)
    if not args.skip_explain:
        print("Running EXPLAIN analysis on queries (this may take a while)...")
        analyzed_queries = run_query_explains(unique_queries)
        scan_count = sum(1 for q in analyzed_queries if q.get("explain_summary", {}).get("full_collection_scan", False))
        print(f"EXPLAIN analysis complete. Found {scan_count} queries with full collection scans.")
    else:
        analyzed_queries = unique_queries
        print("Skipping EXPLAIN analysis as requested (recommendations will be less detailed)")

    # Step 4: Generate optimization recommendations
    print("Generating optimization recommendations...")
    recommendations = generate_optimization_recommendations(analyzed_queries, pattern_analysis)

    # Count recommendations by type
    index_count = sum(len(indices) for collection, indices in recommendations["indexes_to_add"].items())
    view_count = len(recommendations["view_recommendations"])
    print(f"Generated {index_count} index recommendations and {view_count} view recommendations")

    # Step 5: Format output
    print("Formatting analysis results...")
    output = format_output(analyzed_queries, pattern_analysis, recommendations)

    # Step 6: Write output files
    print(f"Writing detailed JSON analysis to {args.output_file}...")
    with open(args.output_file, 'w') as f:
        json.dump(output, f, indent=2)

    # Write markdown report
    print(f"Writing markdown report to {args.markdown_report}...")
    with open(args.markdown_report, 'w') as f:
        f.write(output["markdown_report"])

    # Write index creation script
    print(f"Writing index creation script to {args.index_script}...")
    with open(args.index_script, 'w') as f:
        f.write(output["index_creation_script"])
        f.write("\n\n")
        f.write(output["view_creation_script"])

    print(f"\n=== Ablation Query Analysis Complete ===\n")

    # Print summary to console
    print("Summary Statistics:")
    print(f"- Total unique queries analyzed: {output['query_statistics']['total_unique_queries']}")
    print(f"- Collections analyzed: {output['query_statistics']['collections_analyzed']}")
    print(f"- Queries performing full collection scans: {output['query_statistics']['queries_with_full_scans']} " +
          f"({output['query_statistics']['queries_with_full_scans']/output['query_statistics']['total_unique_queries']*100:.1f}%)")
    print(f"- High-cost queries identified: {output['query_statistics']['slow_queries']}")
    print(f"- Complex queries identified: {output['query_statistics']['complex_queries']}")

    print("\nTop collections by query count:")
    for coll in output['collections_summary'][:3]:
        print(f"  - {coll['collection']}: {coll['query_count']} queries")

        # Show top index recommendations for this collection
        if coll.get("recommended_indexes"):
            top_index = coll["recommended_indexes"][0]
            fields_str = ", ".join(top_index["fields"])
            print(f"    * Top index recommendation: {fields_str}")

    print("\nKey Recommendations:")
    # Print top 3 recommendations
    for suggestion in output['recommendations']['overall_suggestions'][:3]:
        print(f"  - {suggestion}")

    if len(output['recommendations']['overall_suggestions']) > 3:
        print(f"  - Plus {len(output['recommendations']['overall_suggestions']) - 3} more recommendations in the full report")

    print(f"\nOutput Files:")
    print(f"- Detailed JSON analysis: {args.output_file}")
    print(f"- Markdown report: {args.markdown_report}")
    print(f"- Index creation script: {args.index_script}")

    print("\nTo apply the recommended indexes, run this command in the ArangoDB shell:")
    print(f"  arangosh --javascript.execute {args.index_script}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
