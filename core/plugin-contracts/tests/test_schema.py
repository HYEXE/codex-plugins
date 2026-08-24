import json
from pathlib import Path


def test_schema_exists():
    assert Path('core/plugin-contracts/schema.json').exists()
