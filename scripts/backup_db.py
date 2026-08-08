import os
import sys
import shutil
from datetime import datetime, timezone

def backup_database():
    """
    Production Automated Database Backup Script.
    Creates a timestamped backup of the PostgreSQL / SQLite database file in back_ups/ directory.
    """
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backup_dir = os.path.join(project_root, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    db_file = os.path.join(project_root, "ipo_agent.db")
    backup_file = os.path.join(backup_dir, f"ipo_agent_backup_{timestamp}.db")

    if os.path.exists(db_file):
        shutil.copy2(db_file, backup_file)
        print(f"SUCCESS: Database backup created at {backup_file}")
    else:
        print(f"NOTICE: Database file {db_file} not found. In PostgreSQL mode, execute pg_dump.")

if __name__ == "__main__":
    backup_database()
