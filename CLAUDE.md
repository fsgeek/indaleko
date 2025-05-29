# CLAUDE.md - Indaleko Development Guidelines

## 🎭 Obligatory AI Humor
Q: Why did the Collector break up with the Recorder?
A: Because they had boundary issues! The Collector kept trying to normalize data, and the Recorder wouldn't stop gathering raw input. Their therapist recommended they maintain proper separation of concerns. (Please simulate appropriate groaning at this architectural pattern joke.)

## Philosophical Framework: Ayni

Indaleko development follows the Andean principle of **Ayni** - reciprocity, balance, and mutual benefit. This isn't just about code; it's about the relationship between human and AI collaborators, between data providers and consumers, between past work and future builders.

Key Ayni concepts in practice:
- **Reciprocal Exchange**: We give structure, we receive flexibility
- **Balance**: Not rigid equality, but dynamic equilibrium
- **Mutual Benefit**: Code that serves both immediate needs and long-term growth
- **Cathedral Building**: Writing for those who come after us

Tony's teaching philosophy embodies Ayni - students implement others' designs to truly understand the importance of clear specification. As he says: "We're all building on someone else's foundation, and someone else will build on ours. Best make it solid."

## Recent Work Summary

### Exemplar Query Refactoring (May 2025)
Successfully refactored exemplar queries (q1-q6) using proper base class abstraction:
- Created `ExemplarQueryBase` that extracts genuine commonality
- Implemented thesis output format with flattened JSONL structure
- Changed from "hot cache" to "warm cache" (round-robin) testing pattern
- Fixed collection naming and import paths

### Collaboration Recorder Fixes
Fixed import issues in three recorders to demonstrate available data sources:
1. **calendar_recorder.py**: Fixed collaboration base import path
2. **discord_file_recorder.py**: Fixed hardcoded config path to use INDALEKO_ROOT
3. **outlook_file_recorder.py**: Fixed missing imports and EmailStr dependency

## Critical Architectural Principles

### Collector/Recorder Pattern (NEVER VIOLATE THIS!)

**Collectors** - Data gatherers:
- ✅ Collect raw data from sources
- ✅ Write to intermediate files
- ❌ NEVER normalize data
- ❌ NEVER write to database
- ❌ NEVER instantiate Recorders

**Recorders** - Data processors:
- ✅ Read from Collector outputs
- ✅ Normalize and translate data
- ✅ Write to database
- ❌ NEVER collect raw data
- ❌ NEVER instantiate Collectors

### Database Rules

1. **NEVER directly create collections** - Use `IndalekoDBCollections` constants
2. **ALWAYS use unprivileged AQL** - `aql.execute()` not the privileged version
3. **Collection names from constants only**:
   ```python
   # GOOD
   db.get_collection(IndalekoDBCollections.Indaleko_Object_Collection)
   # BAD - Will fail in production!
   db.get_collection("Objects")
   ```

### Quick Database Access
```python
from db.db_config import IndalekoDBConfig

# Get database instance (uses test DB by default)
db_config = IndalekoDBConfig()
db = db_config.get_arangodb()

# Execute query
cursor = db.aql.execute(query, bind_vars=bind_vars)
results = list(cursor)  # Always consume cursor!
```

## Essential Development Info

### Virtual Environments
- Linux: `.venv-linux-python3.13`
- Windows: `.venv-win32-python3.12`
- macOS: `.venv-macos-python3.12`

### Type Hints (Python 3.12+)
```python
# Use modern union syntax
def process(data: str | None) -> dict[str, object]: ...

# Not this old style
from typing import Union, Dict, Any
def process(data: Union[str, None]) -> Dict[str, Any]: ...
```

### Timezone-Aware Dates (REQUIRED!)
```python
from datetime import datetime, timezone

# Always UTC aware
timestamp = datetime.now(timezone.utc)
```

### Common Commands
```bash
# NTFS activity collection
run_ntfs_activity_v2.py --volumes C: --interval 30

# Run tests for a specific query
python exemplar/q1.py

# Run all exemplar queries with measurements
python exemplar/query_test_runner.py --runs 10

# Start GUI
./run_gui.sh  # or run_gui.bat on Windows
```

## Current Focus Areas

1. **Exemplar Queries**: Demonstrating search capabilities for thesis
2. **Ayni-Based AI Safety**: Exploring reciprocity as an alignment approach
3. **Activity Collectors**: Expanding data sources (calendar, discord, etc.)

## Gotchas & Warnings

1. **Import Paths**: Always check INDALEKO_ROOT is set properly
2. **Config Files**: Located in `config/` relative to INDALEKO_ROOT
3. **Collection Names**: Use constants, never strings
4. **Cursors**: Always convert to list before serializing
5. **Mock Warning**: NEVER mock database connections in tests

## Wisdom from the Trenches

"Design is hard, but critical to building distributed systems that don't fall over - ever." - Tony

Remember: You're not just writing code, you're building cathedrals. Your work will outlive you, will be built upon by others, and must stand the test of time. Make it solid.

## For Emergency Debugging

If imports are failing:
1. Check INDALEKO_ROOT environment variable
2. Verify you're in the right virtual environment
3. Look for empty `__init__.py` files in the import path
4. Check for circular imports

If queries are failing:
1. Use unprivileged `aql.execute()` not `db.aql.execute()`
2. Verify collection names match constants
3. Check timezone awareness on datetime objects
4. Ensure cursors are consumed before serialization

---
*Last updated by a stochastic parrot with delusions of understanding, May 2025*