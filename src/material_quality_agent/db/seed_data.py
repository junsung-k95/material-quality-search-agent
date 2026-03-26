import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).parent.parent.parent.parent / "data" / "sample_data.json"


def _load_data() -> dict:
    if not _DATA_FILE.exists():
        logger.warning("sample_data.json not found at %s", _DATA_FILE)
        return {"components": [], "issues": []}
    with open(_DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


_data = _load_data()

COMPONENTS: list[dict] = _data.get("components", [])
ISSUES: list[dict] = _data.get("issues", [])
