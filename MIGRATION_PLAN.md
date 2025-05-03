<!--
  Migration Plan of Record for Indaleko Project Restructuring
  Generated on $(date)
-->
# Indaleko Migration Plan of Record

This document captures the agreed‐upon steps for Phase 1 of reorganizing Indaleko into a formal Python project under `src/indaleko/`.

## Phase 1: Core Library & Query Namespace

1. Prepare `src/indaleko/` directory
   - Ensure `src/indaleko/` exists with an empty `__init__.py`.

2. Move Core Modules
   - `constants/`   → `src/indaleko/constants/`
   - `data_models/` → `src/indaleko/data_models/`
   - `db/`          → `src/indaleko/db/`
   - `utils/`       → `src/indaleko/utils/`

3. Relocate Facade & CLI Entry
   - `Indaleko.py`  → `src/indaleko/core.py`
   - Root `__main__.py` → `src/indaleko/__main__.py`
   - Update `src/indaleko/__init__.py` to expose `__version__` and façade API.

4. Incorporate Query Tooling
   - `query/`       → `src/indaleko/query/`
   - Adjust imports within `query/` to use the `indaleko.*` namespace.

5. Update Imports in Moved Code
   - Change all top‐level imports (e.g. `import utils…`) to `from indaleko.utils…`, etc.

6. Update `pyproject.toml`
   - Under `[tool.setuptools.packages.find]`:
     ```toml
     where = ["src"]
     include = ["indaleko*"]
     ```
   - Add console_scripts entry:
     ```toml
     [project.scripts]
     indaleko = "indaleko.__main__:main"
     ```
   - Document `uv` usage in the README and any install scripts.

7. Sanity Checks
   - Run `uv pip install -e .` and ensure no pip direct calls (pre‐commit will enforce).
   - Test importability:
     ```bash
     uv run python -c "import indaleko; print(indaleko.__version__)"
     ```

8. Next Steps (to be scheduled in Phase 2)
   - Centralize and formalize tests under `tests/`
   - Introduce CI pipeline (GitHub Actions)
   - Prune or archive legacy scripts (`old/`, `backup/`)
   - Carve out standalone packages for `archivist/` and `firecircle/`

---
_This plan will be updated with README_AGENT.md guidelines once provided._