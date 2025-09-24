#!/usr/bin/env python3
"""Run all tests in a single process with registry clearing."""

import sys
import subprocess
import os

def main():
    """Run all tests with registry clearing."""
    # Clear Viam registry before any imports
    try:
        from viam.resource.registry import Registry
        Registry._resources.clear()
        Registry._apis.clear()
    except Exception:
        pass
    
    # Run pytest with all tests
    cmd = ["python", "-m", "pytest", "-v", "tests/", "-m", "unit"]
    
    print(f"\n{'='*60}")
    print(f"Running: All module tests (unit tests)")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Tests failed with return code {result.returncode}")
        sys.exit(1)
    else:
        print(f"✅ All tests completed successfully")

if __name__ == "__main__":
    main()
