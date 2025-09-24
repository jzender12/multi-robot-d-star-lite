#!/usr/bin/env python3
"""
Entry point for the Multi-Robot D* Lite demo.
This allows the package to be run as a module: python -m multi_robot_d_star_lite
"""

import sys
import os

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run main
from main import main

if __name__ == "__main__":
    main()