#!/bin/bash
#
# run_tests.sh - Run all tests for the Multi-Robot Playground project
# Uses run_dev.sh for consistent virtual environment management
#

set -e  # Exit on error

echo "========================================="
echo "Running Multi-Robot Playground Test Suite"
echo "========================================="
echo ""

# Run all tests (core, pygame, and web)
echo "Running all tests..."
./run_dev.sh pytest tests/ -v --tb=short

echo ""
echo "========================================="
echo "All tests completed successfully!"
echo "========================================="