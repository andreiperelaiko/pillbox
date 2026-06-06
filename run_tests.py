import sys
from pathlib import Path

import pytest

if __name__ == "__main__":
    root = Path(__file__).parent
    sys.exit(pytest.main([str(root / "tests"), *sys.argv[1:]]))
