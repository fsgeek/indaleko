"""initializtion logic for the activity context system"""

import importlib
import os
import sys

# from icecream import ic

init_path = os.path.dirname(os.path.abspath(__file__))


# pylint: disable=wrong-import-position
from semantic.characteristics import SemanticDataCharacteristics

# pylint: enable=wrong-import-position

collector_dir = os.path.join(init_path, "collectors")
collectors = [
    x for x in os.listdir(collector_dir) if os.path.isdir(os.path.join(collector_dir, x)) and not x.startswith("_")
]
# ic(collectors)

__version__ = "0.1.0"

__all__ = ["SemanticDataCharacteristics"]
