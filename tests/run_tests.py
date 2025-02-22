import pytest
import sys
import coverage
from rational_onion.config import get_test_settings

settings = get_test_settings()

def run_tests():
    """Run test suite with coverage"""
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
        "-vv",
        # Use settings from centralized config
        f"--neo4j-uri={settings.NEO4J_URI}",
        f"--neo4j-user={settings.NEO4J_USER}",
        f"--neo4j-password={settings.NEO4J_PASSWORD}",
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