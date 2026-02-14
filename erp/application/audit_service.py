from __future__ import annotations

from erp.infrastructure.audit_repository import AuditRepository


class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def log(self, username: str, action: str, entity_type: str, entity_id: str, details: str) -> None:
        self.repository.log(
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )

    def list_recent(self, limit: int = 300) -> list[dict[str, str]]:
        return self.repository.list_recent(limit=limit)

