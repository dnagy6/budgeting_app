import sqlite3
from datetime import date
from pathlib import Path
import os
import sys
import shutil
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def get_app_data_dir() -> Path:
    """
    Resolves the OS-compliant persistent user data directory.
    - macOS:   ~/Library/Application Support/BudgetingApp
    - Windows: %APPDATA%/BudgetingApp
    - Linux:   ~/.local/share/BudgetingApp
    """
    app_name = "BudgetingApp"
    if sys.platform == "darwin":
        base_dir = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    else:
        base_dir = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    data_dir = base_dir / app_name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def create_daily_backup(db_path: Path, max_backups: int = 7):
    """Creates a consistent backup snapshot using SQLite's native backup API."""
    if not db_path.exists():
        return

    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    today_str = date.today().isoformat()
    backup_file = backup_dir / f"budget_backup_{today_str}.db"

    # Only snapshot once per day
    if not backup_file.exists():
        try:
            # Native SQLite backup captures both main DB and active WAL pages
            source_conn = sqlite3.connect(str(db_path))
            dest_conn = sqlite3.connect(str(backup_file))
            with dest_conn:
                source_conn.backup(dest_conn)
            dest_conn.close()
            source_conn.close()
        except Exception:
            pass

    # Prune old backups beyond the retention limit
    all_backups = sorted(backup_dir.glob("budget_backup_*.db"))
    while len(all_backups) > max_backups:
        oldest = all_backups.pop(0)
        try:
            oldest.unlink()
        except OSError:
            pass


def init_database_path() -> Path:
    """Configures storage directory and handles initial migration from local repo."""
    data_dir = get_app_data_dir()
    target_db = data_dir / "budget.db"

    # Auto-migration: If a local database exists in the project root, copy it to OS storage
    local_db = Path("budget.db")
    if local_db.exists() and not target_db.exists():
        shutil.copy2(local_db, target_db)

    return target_db


# --- Connection Configuration ---
DB_FILE = init_database_path()
DATABASE_URL = f"sqlite:///{DB_FILE.resolve()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes schema tables and performs a daily backup snapshot."""
    import source.persistence.models  # Register models with Base metadata
    Base.metadata.create_all(bind=engine)
    create_daily_backup(DB_FILE)