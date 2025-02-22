import pytest
import sys
import coverage

def run_tests():
    # Start coverage measurement
    cov = coverage.Coverage()
    cov.start()

    # Run pytest with specific options
    args = [
        "--verbose",
        "--asyncio-mode=auto",
        "--cov=rational_onion",
        "--cov-report=term-missing",
        "--cov-report=html",
        "-vv"
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