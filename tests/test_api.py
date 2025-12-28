import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from api.index import app

def test_app_exists():
    assert app is not None

