import importlib, sys
# Import the real package under the src.* namespace and alias it to the top-level name
_src_mod = importlib.import_module('src.data_bus')
# Ensure that `data_bus` refers to the same module object as `src.data_bus`
sys.modules['data_bus'] = _src_mod
# Re-export submodules for convenience
from src.data_bus import *
