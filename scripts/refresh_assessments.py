"""Regenerate PENDING assessments with the current engine and datasets.

Run from the project root after updating the datasets or retraining the
recommenders:
    .venv\\Scripts\\python.exe scripts\\refresh_assessments.py [--dry-run]

Only assessments still awaiting physician review are rebuilt (from the stored
patient and visit, exactly as at intake), so the review queue always shows
the current foods, recipes and models. Approved and rejected assessments are
never touched: an approved report must stay exactly what the physician
signed off. Every regeneration is written to the append-only audit log, and a
SQLite database is copied to a timestamped backup before anything is written.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import select  # noqa: E402

from src.api.services import ENGINE_VERSION, build_assessment  # noqa: E402
from src.core import audit  # noqa: E402
from src.core.config import settings  # noqa: E402
from src.db.models import Assessment  # noqa: E402
from src.db.session import SessionLocal, init_db  # noqa: E402


def _backup_sqlite() -> Path | None:
    url = settings.database_url
    if not url.startswith("sqlite:///"):
        return None
    db_path = Path(url.removeprefix("sqlite:///"))
    if not db_path.is_absolute():
        db_path = PROJECT_ROOT / db_path
    if not db_path.exists():
        return None
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = db_path.with_name(f"{db_path.stem}.backup-{stamp}{db_path.suffix}")
    shutil.copy2(db_path, backup)
    return backup


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    args = parser.parse_args()

    init_db()
    with SessionLocal() as db:
        assessments = list(db.scalars(select(Assessment).order_by(Assessment.id)))
        pending = [a for a in assessments if a.status == "pending"]
        for a in assessments:
            if a.status != "pending":
                print(f"assessment #{a.id} ({a.visit.patient.name}): {a.status} on engine "
                      f"{a.engine_version} — kept as signed off")
        if not pending:
            print("no pending assessments — nothing to do")
            return 0
        if args.dry_run:
            for a in pending:
                print(f"would regenerate assessment #{a.id} ({a.visit.patient.name}): "
                      f"engine {a.engine_version} -> {ENGINE_VERSION}")
            return 0

        backup = _backup_sqlite()
        if backup:
            print(f"backup -> {backup.name}")
        for a in pending:
            old_engine = a.engine_version
            result = build_assessment(a.visit.patient, a.visit)
            a.result = result
            a.engine_version = ENGINE_VERSION
            audit.record(db, actor="refresh_assessments", action="assessment.regenerated",
                         entity="assessment", entity_id=a.id,
                         detail={"from_engine": old_engine, "to_engine": ENGINE_VERSION})
            nutrition = result["nutrition"]
            print(f"regenerated assessment #{a.id} ({a.visit.patient.name}): engine "
                  f"{old_engine} -> {ENGINE_VERSION}, {len(nutrition['top_foods'])} foods, "
                  f"{len(nutrition['top_recipes'])} recipes "
                  f"(food={nutrition['scoring_backend']}, recipe={nutrition['recipe_scoring_backend']})")
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
