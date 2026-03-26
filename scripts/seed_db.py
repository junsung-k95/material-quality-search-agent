"""Seed script: initialize SQLite DB and ChromaDB with sample data."""
import logging
import sys
from pathlib import Path

# Ensure src is on the path when run directly
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from material_quality_agent.config import settings
from material_quality_agent.db.seed_data import COMPONENTS, ISSUES
from material_quality_agent.db.issue_db import init_db, insert_issues
from material_quality_agent.vector.store import seed_components, seed_issues

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Seeding SQLite database at: %s", settings.db_path)
    init_db(settings.db_path)
    insert_issues(settings.db_path, ISSUES)
    logger.info("Inserted %d issues into SQLite", len(ISSUES))

    logger.info("Seeding ChromaDB at: %s", settings.chroma_path)
    seed_components(settings.chroma_path, COMPONENTS)
    seed_issues(settings.chroma_path, ISSUES)

    logger.info("Seed complete. Components: %d, Issues: %d", len(COMPONENTS), len(ISSUES))


if __name__ == "__main__":
    main()
