"""Stored GitHub OAuth credentials (token encrypted at rest)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, LargeBinary, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from crypto import TokenEncryptionError, decrypt_token, encrypt_token
from database import BaseModel

if TYPE_CHECKING:
    from models.user import User


class GitHubCredential(BaseModel):
    """
    One row per user: OAuth access token (Fernet-encrypted), optional GitHub App fields.
    """

    __tablename__ = "github_credentials"

    team_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    access_token_encrypted: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    refresh_token_encrypted: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    installation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scopes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="github_credential")

    @staticmethod
    def encrypt_access_token(token: str, *, fernet_key: str) -> bytes:
        return encrypt_token(token, fernet_key=fernet_key)

    @staticmethod
    def decrypt_access_token(ciphertext: bytes, *, fernet_key: str) -> str:
        return decrypt_token(ciphertext, fernet_key=fernet_key)

    def plaintext_token(self, *, fernet_key: str) -> str:
        """Decrypt token for API calls — never log or return in API responses."""
        try:
            return self.decrypt_access_token(self.access_token_encrypted, fernet_key=fernet_key)
        except TokenEncryptionError as e:
            raise RuntimeError("Stored GitHub token could not be decrypted") from e
