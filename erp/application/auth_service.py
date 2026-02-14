from __future__ import annotations

from erp.infrastructure.auth_repository import AuthRepository


class AuthService:
    def __init__(self, repository: AuthRepository):
        self.repository = repository

    def bootstrap(self) -> None:
        self.repository.ensure_default_admin()

    def login(self, username: str, password: str) -> dict[str, str] | None:
        return self.repository.authenticate(username, password)

    def list_users(self) -> list[dict[str, str]]:
        return self.repository.list_users()

    def create_user(self, username: str, password: str, role: str) -> None:
        self.repository.create_user(username=username, password=password, role=role)

