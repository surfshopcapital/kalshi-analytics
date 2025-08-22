"""
Main Streamlit application entry point.
This file ensures proper import paths for Streamlit Cloud deployment.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.absolute()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run the main dashboard
from Dashboard import main

if __name__ == "__main__":
    main()
