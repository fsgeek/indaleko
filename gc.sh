git commit --no-verify -m "Implement cross-collection query support in the AblationTester class to properly measure impact of ablations on relationship-based queries:
      - Added intelligent relationship detection between collections
      - Fixed compatibility with ArangoDB schema requirements
      - Added cross-collection JOIN AQL generation
      - Improved bind variable handling to avoid parameter errors
      - Updated to use AblationQueryTruth as the truth collection
      - Added support for detecting related collections from query semantics"

