#!/usr/bin/env python3
"""Unified test runner script for rocket-sensors project."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
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
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True


def run_module_tests(module, test_type, coverage, verbose, hardware):
    """Run tests for a specific module in a separate process to avoid registry conflicts."""
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=xml"])
    
    # Select module and test files
    cmd.append(f"tests/{module}/")
    
    # Select test type
    if test_type == "unit":
        cmd.extend(["-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "all":
        if not hardware:
            cmd.extend(["-m", "not hardware"])
    
    # Add hardware tests if requested
    if hardware:
        cmd.extend(["-m", "hardware"])
    
    # Run the tests
    return run_command(cmd, f"Testing {module} module ({test_type} tests)")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for rocket-sensors project")
    parser.add_argument("--module", choices=["loadcell", "mpu", "bmp", "all"], 
                       default="all", help="Which module to test")
    parser.add_argument("--type", choices=["unit", "integration", "all"], 
                       default="all", help="Which type of tests to run")
    parser.add_argument("--coverage", action="store_true", 
                       help="Run with coverage reporting")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="Verbose output")
    parser.add_argument("--hardware", action="store_true", 
                       help="Include hardware-dependent tests")
    
    args = parser.parse_args()
    
    # For individual modules, run in separate processes to avoid registry conflicts
    if args.module != "all":
        success = run_module_tests(args.module, args.type, args.coverage, args.verbose, args.hardware)
    else:
        # For "all", run all modules sequentially in separate processes
        modules = ["loadcell", "mpu", "bmp"]
        success = True
        
        for module in modules:
            print(f"\n🔄 Running {module} tests...")
            module_success = run_module_tests(module, args.type, args.coverage, args.verbose, args.hardware)
            if not module_success:
                success = False
                print(f"❌ {module} module tests failed")
            else:
                print(f"✅ {module} module tests passed")
    
    if success:
        print(f"\n🎉 All tests passed!")
        if args.coverage:
            print(f"📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
