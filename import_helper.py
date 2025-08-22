"""
Import helper to fix path issues in Streamlit Cloud deployment.
This file ensures that local modules can be imported correctly.
"""

import sys
import os
from pathlib import Path

def setup_import_paths():
    """Setup import paths to include the project root directory"""
    # Get the current file's directory
    current_dir = Path(__file__).parent.absolute()
    
    # Add the project root to Python path if not already there
    if str(current_dir) not in sys.path:
        sys.path.insert(0, str(current_dir))
    
    # Also add the parent directory (in case we're in a subdirectory)
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    # Add the current working directory as well
    cwd = os.getcwd()
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
    
    # For Streamlit Cloud, also try to add common deployment paths
    # Streamlit Cloud often uses /mount/src/ as the source directory
    mount_src = "/mount/src"
    if os.path.exists(mount_src) and mount_src not in sys.path:
        sys.path.insert(0, mount_src)
    
    # Also try the parent of mount_src
    mount_src_parent = "/mount/src/kalshi-analytics"
    if os.path.exists(mount_src_parent) and mount_src_parent not in sys.path:
        sys.path.insert(0, mount_src_parent)
    
    # Debug: print current paths
    print(f"🔍 DEBUG: Python path setup complete")
    print(f"🔍 DEBUG: Current directory: {current_dir}")
    print(f"🔍 DEBUG: Parent directory: {parent_dir}")
    print(f"🔍 DEBUG: Working directory: {cwd}")
    print(f"🔍 DEBUG: Mount src: {mount_src} (exists: {os.path.exists(mount_src)})")
    print(f"🔍 DEBUG: Mount src parent: {mount_src_parent} (exists: {os.path.exists(mount_src_parent)})")
    print(f"🔍 DEBUG: First few sys.path entries: {sys.path[:5]}")

# Call this function when the module is imported
setup_import_paths()

# Now we can safely import local modules
try:
    from utils import *
    UTILS_IMPORTED = True
    print("✅ Successfully imported utils module")
except ImportError as e:
    UTILS_IMPORTED = False
    print(f"❌ Warning: Could not import utils: {e}")
    # Try alternative import paths
    try:
        import utils
        UTILS_IMPORTED = True
        print("✅ Successfully imported utils module (alternative method)")
    except ImportError as e2:
        print(f"❌ Alternative import also failed: {e2}")
        # Try one more time with absolute import
        try:
            sys.path.insert(0, "/mount/src/kalshi-analytics")
            from utils import *
            UTILS_IMPORTED = True
            print("✅ Successfully imported utils module (absolute path method)")
        except ImportError as e3:
            print(f"❌ Absolute path import also failed: {e3}")

try:
    from shared_sidebar import *
    SIDEBAR_IMPORTED = True
    print("✅ Successfully imported shared_sidebar module")
except ImportError as e:
    SIDEBAR_IMPORTED = False
    print(f"❌ Warning: Could not import shared_sidebar: {e}")

try:
    from kalshi_client import KalshiClient
    KALSHI_IMPORTED = True
    print("✅ Successfully imported kalshi_client module")
except ImportError as e:
    KALSHI_IMPORTED = False
    print(f"❌ Warning: Could not import kalshi_client: {e}")

try:
    from polymarket_client import PolymarketClient
    POLYMARKET_IMPORTED = True
    print("✅ Successfully imported polymarket_client module")
except ImportError as e:
    POLYMARKET_IMPORTED = False
    print(f"❌ Warning: Could not import polymarket_client: {e}")

print(f"🔍 DEBUG: Import status - Utils: {UTILS_IMPORTED}, Sidebar: {SIDEBAR_IMPORTED}, Kalshi: {KALSHI_IMPORTED}, Polymarket: {POLYMARKET_IMPORTED}")
