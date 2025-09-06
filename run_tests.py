#!/usr/bin/env python3
"""
Test runner for EVE Copilot
"""

import sys
import os
import subprocess
from pathlib import Path


def main():
    """Run the test suite."""
    print("🧪 Running EVE Copilot tests...")
    print("=" * 50)
    
    # Add the current directory to Python path
    current_dir = Path(__file__).parent
    sys.path.insert(0, str(current_dir))
    
    try:
        # Check if pytest is available
        try:
            import pytest
            print(f"✅ pytest {pytest.__version__} found")
        except ImportError:
            print("❌ pytest not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest"], check=True)
            print("✅ pytest installed successfully")
        
        # Run pytest with coverage
        print("\n🚀 Starting test execution...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/", 
            "-v", 
            "--tb=short",
            "--cov=evetalk",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ], capture_output=False)
        
        print("\n" + "=" * 50)
        if result.returncode == 0:
            print("🎉 All tests passed!")
            print("📊 Coverage report generated in htmlcov/ directory")
        else:
            print(f"💥 Tests failed with exit code {result.returncode}")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
