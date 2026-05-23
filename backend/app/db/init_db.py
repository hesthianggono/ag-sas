from sqlmodel import SQLModel
from app.db.session import engine
from app.models import user, project, calculation, steel_profile, report, figure_snapshot, full_report  # noqa: F401 — registers tables
from app.services.steel_profile_service import seed_steel_profiles
from sqlmodel import Session


def init_db():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        seed_steel_profiles(session)
    print("Database initialized.")


if __name__ == "__main__":
    init_db()
