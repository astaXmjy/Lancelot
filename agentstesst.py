"""
LANCELOT - Android Vulnerability Scanner
Quick run script for the vulnerability scanner
"""
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Change to project directory to ensure relative paths work
os.chdir(project_root)

from vulnerability_scanner import run_scan


if __name__ == "__main__":
    # Run the vulnerability scan
    run_scan()
