"""Direct CLI Launcher for open-research-lite.

Run:
    python cli.py
"""

import sys
import os

# Prioritize local src
sys.path.insert(0, os.path.abspath("src"))

from open_research_lite.__main__ import main

if __name__ == "__main__":
    main()
