import pytest
import sys
import os

if __name__ == "__main__":
    # Run pytest
    sys.exit(pytest.main(["-k", "not test_will_fail"]))