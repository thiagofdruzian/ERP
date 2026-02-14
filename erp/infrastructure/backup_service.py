from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil


class BackupService:
    def __init__(self, db_path: Path, backup_dir: Path):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self) -> Path | None:
        if not self.db_path.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = self.backup_dir / f"erp_backup_{timestamp}.db"
        shutil.copy2(self.db_path, target)
        return target

