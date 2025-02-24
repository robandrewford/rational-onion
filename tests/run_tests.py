import pytest
import sys
import coverage
from rational_onion.config import get_test_settings

settings = get_test_settings()

def run_tests() -> int:
    """Run test suite with coverage"""
    # Start coverage measurement
    cov = coverage.Coverage()
    cov.start()

    # Run pytest with standard options
    args = [
        "-v",  # verbose
        "--asyncio-mode=auto",
        "tests/",  # test directory
        "-s",  # allow print statements
    ]
    
    result = pytest.main(args)
    
    # Stop coverage measurement
    cov.stop()
    cov.save()
    
    # Generate coverage reports
    cov.report()
    cov.html_report(directory='coverage_html')
    
    return result

if __name__ == "__main__":
    sys.exit(run_tests()) 