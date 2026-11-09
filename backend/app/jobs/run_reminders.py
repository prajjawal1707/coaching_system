
from app.database import SessionLocal
from app.services.automatic_reminders import run_automatic_reminders


def main():
    db = SessionLocal()

    try:
        result = run_automatic_reminders(db)
        print("FeeFlow automatic reminder job:", result)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
