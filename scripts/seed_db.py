"""Create the database and seed it with the synthetic demo patients.

Run from the project root:  .venv\\Scripts\\python.exe scripts\\seed_db.py
Each seeded patient gets one visit with a pending assessment, ready for the
review queue in the dashboard. The patients and demo logins are in
src/db/demo.py (a hosted demo seeds the same ones: SEED_DEMO_DATA).
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.demo import seed_demo  # noqa: E402
from src.db.session import SessionLocal, init_db  # noqa: E402


def main() -> None:
    init_db()
    with SessionLocal() as db:
        if not seed_demo(db):
            print("database already has patients — nothing to do")


if __name__ == "__main__":
    main()
