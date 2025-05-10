# Ablation Testing Framework TODO List

## CRITICAL: FAIL-STOP IS REQUIRED FOR ALL IMPLEMENTATIONS

This project follows a strict FAIL-STOP model as its primary design principle:

1. **NEVER** implement fallbacks or paper over errors
2. **ALWAYS** fail immediately and visibly when issues occur
3. **NEVER** substitute mock/fake data when real data is unavailable
4. **ALWAYS** exit with a clear error message (sys.exit(1)) rather than continuing with degraded functionality

This is **REQUIRED** for the ablation testing framework as it is a scientific experiment where data integrity is critical.
Silently substituting template-based data when LLM generation fails would invalidate experimental results.

## Immediate Tasks Remaining

- [ ] Confirm that the current code base can successfully run the full pipeline with the available activity data providers
- [ ] Migrate experimental LLM query generator from scratch to research/ablation/query
- [ ] Update imports and references in run_comprehensive_ablation.py to use the migrated query generator
- [ ] Test the full ablation pipeline after migration to verify functionality
- [ ] Fix any bugs found during post-migration testing
- [ ] Commit working code with --no-verify flag

- [ ] Implement CollaborationActivityCollector and CollaborationActivityRecorder
- [ ] Verify pipeline works with Collaboration activity data provider
- [ ] Commit collaboration activity implementation with --no-verify flag

- [ ] Implement StorageActivityCollector and StorageActivityRecorder
- [ ] Verify pipeline works with Storage activity data provider
- [ ] Commit storage activity implementation with --no-verify flag

- [ ] Implement MediaActivityCollector and MediaActivityRecorder
- [ ] Verify pipeline works with Media activity data provider
- [ ] Commit media activity implementation with --no-verify flag

- [ ] Create database snapshot mechanism using arangobackup utility
- [ ] Integrate database snapshot creation at end of successful ablation run

## Test/Control Group Implementation

- [x] Create TestControlGroupManager class to handle group assignment
- [x] Add configuration option for control group percentage (default 20%)
- [x] Implement random assignment mechanism for queries to test/control
- [x] Add control group results to summary statistics calculations
- [x] Create separate visualization for control group results
- [x] Add statistical comparison between test and control group results

## Power-Set Testing

- [x] Implement PowerSetGenerator class for collection combinations
- [x] Add configuration option for max combination size
- [x] Add smart subset selection to reduce total runtime (if full power set too large)
- [x] Update runner to execute tests for each combination
- [x] Enhance results storage to track collection combinations
- [x] Add combinatorial results to summary output
- [x] Create heatmap visualization showing impact of different combinations

## Multiple Test Rounds

- [x] Add round tracking to AblationTester
- [x] Implement rotation mechanism for moving collections between test/control
- [x] Create RoundManager class to coordinate multiple test rounds
- [x] Add round-specific report generation
- [x] Implement cross-round statistical analysis
- [x] Add configuration for number of rounds (default 3)
- [x] Create aggregated multi-round results

## Statistical Analysis

- [x] Implement confidence interval calculations for precision/recall metrics
- [x] Add statistical significance testing for ablation impact
- [x] Create variance analysis across multiple rounds
- [x] Add outlier detection for unusual query results
- [x] Generate statistical summary tables in report
- [x] Create box plots showing distribution of results across rounds
- [x] Implement correlation analysis between collection types and query performance

## Enhanced Reporting

- [x] Create comprehensive PDF report with all visualizations
- [x] Add executive summary section with key findings
- [x] Create interactive HTML dashboard option
- [x] Add query-level detail reports
- [x] Implement comparison view between rounds
- [x] Create publication-ready table and figure formats
- [x] Add exportable data tables for external analysis

## Infrastructure Improvements

- [x] Add checkpointing to allow resuming interrupted tests
- [x] Create progress tracker with ETA for long-running tests
- [x] Implement parallel testing for independent collection combinations
- [x] Add resource monitoring to prevent database overload
- [x] Create cleanup utility to remove old test data
- [x] Add logging level configuration for detailed diagnostics
- [x] Implement test data verification before test runs

## Query Generation Enhancements

- [ ] Improve query diversity with enhanced templates
- [ ] Create query complexity scoring system
- [ ] Implement query categorization for stratified sampling
- [ ] Add natural language variation for similar semantic queries
- [ ] Ensure balanced distribution across collection types
- [ ] Create specialized cross-collection relationship queries
- [ ] Implement query validation to ensure expected results exist

## Documentation

- [ ] Create detailed architecture documentation
- [ ] Add usage examples for different test scenarios
- [ ] Document result interpretation guidelines
- [ ] Create troubleshooting guide
- [ ] Add configuration reference documentation
- [ ] Create developer guide for extending the framework
- [ ] Document experimental design methodology

## Additional Future Enhancements

- [ ] Improve truth data generation to create more semantically meaningful matches
- [ ] Create more non-match case generation with controlled variety
- [ ] Enhance diversity calculation for query generation using Jaro-Winkler similarity
- [ ] Improve ablation report visualizations with more detailed metrics
- [ ] Create end-to-end ablation study script following full protocol

## Implementation Notes

1. All activity data providers must follow the same pattern:
   - Collectors generate synthetic activity data but NEVER interact with the database
   - Recorders process collector data and insert it into the database
   - Each provider must handle fail-stop error cases properly

2. The LLM query generator must:
   - Fail immediately if API connection fails
   - Fail immediately if response parsing fails
   - Fail immediately if diversity evaluation fails
   - NEVER substitute template-based queries as fallbacks

3. The comprehensive ablation test runner must:
   - Validate all prerequisites before starting
   - Fail immediately if any component is missing
   - Never attempt to continue with partial functionality
   - Properly clean up resources even when failing

4. The experimental design elements must:
   - Maintain strict separation between test and control groups
   - Apply consistent methodology across all test rounds
   - Preserve raw result data for post-hoc analysis
   - Include proper statistical validation for all findings
   - Record adequate metadata about test conditions and environment

Remember: It is better to fail loudly and immediately than to continue with compromised functionality.