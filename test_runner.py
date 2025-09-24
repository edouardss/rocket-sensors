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
    parser.add_argument("--simple", action="store_true", 
                       help="Use simplified test files (if available)")
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=xml"])
    
    # Select module and test files
    if args.simple:
        # Use simplified test files if available
        if args.module == "all":
            # Try to run simplified tests for all modules
            test_files = []
            for module in ["loadcell", "mpu", "bmp"]:
                simple_file = f"tests/{module}/test_{module}_simple.py"
                if Path(simple_file).exists():
                    test_files.append(simple_file)
            if test_files:
                cmd.extend(test_files)
            else:
                cmd.append("tests/")
        else:
            simple_file = f"tests/{args.module}/test_{args.module}_simple.py"
            if Path(simple_file).exists():
                cmd.append(simple_file)
            else:
                cmd.append(f"tests/{args.module}/")
    else:
        # Use comprehensive test files
        if args.module == "all":
            cmd.append("tests/")
        else:
            cmd.append(f"tests/{args.module}/")
    
    # Select test type
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "all":
        if not args.hardware:
            cmd.extend(["-m", "not hardware"])
    
    # Add hardware tests if requested
    if args.hardware:
        cmd.extend(["-m", "hardware"])
    
    # Run the tests
    test_type_desc = "simplified" if args.simple else "comprehensive"
    success = run_command(cmd, f"Testing {args.module} module ({args.type} tests, {test_type_desc})")
    
    if success:
        print(f"\n🎉 All tests passed!")
        if args.coverage:
            print(f"📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
