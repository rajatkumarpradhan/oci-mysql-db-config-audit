"""Data model and export loading for the MySQL DB system audit."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


class ExportError(ValueError):
    """Raised when an export file is malformed."""


PROD_LABELS = ("prod", "production")


@dataclass(frozen=True)
class DbSystem:
    name: str
    labels: tuple = ()
    backups_enabled: bool = True
    retention_days: int = 7
    delete_protected: bool = False
    description: str = ""
    tags: tuple = ()

    def is_prod(self) -> bool:
        return any(c in x.lower() for x in self.labels for c in PROD_LABELS)


DEFAULT_RETENTION_DAYS = 7  # documented service default; configurable range is 1-35


def load_export(path: str) -> tuple:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ExportError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or "db_systems" not in raw:
        raise ExportError(f"{path}: top level must hold a 'db_systems' list")
    if not isinstance(raw["db_systems"], list):
        raise ExportError(f"{path}: 'db_systems' must be a list")
    systems = []
    for i, d in enumerate(raw["db_systems"]):
        where = f"db_systems[{i}]"
        if not isinstance(d, dict):
            raise ExportError(f"{where}: must be an object")
        if "name" not in d:
            raise ExportError(f"{where}: missing required field 'name'")
        retention = d.get("retention_days", 7)
        if not isinstance(retention, int) or isinstance(retention, bool) or retention < 1:
            raise ExportError(f"{where}: 'retention_days' must be a positive integer")
        systems.append(DbSystem(
            name=d["name"],
            labels=tuple(d.get("labels", [])),
            backups_enabled=bool(d.get("backups_enabled", True)),
            retention_days=retention,
            delete_protected=bool(d.get("delete_protected", False)),
            description=str(d.get("description", "")),
            tags=tuple(d.get("tags", [])),
        ))
    return tuple(systems)
