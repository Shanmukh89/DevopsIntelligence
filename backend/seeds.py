"""Seed local PostgreSQL with sample teams and repositories.

Usage (from backend/):

    python seeds.py

Requires DATABASE_URL pointing at PostgreSQL with migrations applied
(`python -m alembic upgrade head`).
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from database import SessionLocal
from models import CodeEmbedding, Repository, Team, TeamMember


def main() -> None:
    session = SessionLocal()
    try:
        existing = session.execute(
            select(Repository).where(Repository.github_repo_id == 123456789)
        ).scalar_one_or_none()
        if existing is not None:
            print("Sample data already present (github_repo_id=123456789). Skipping.")
            return

        team = Team(
            id=uuid.uuid4(),
            name="Auditr Dev Team",
        )
        session.add(team)
        session.flush()

        session.add(
            TeamMember(
                id=uuid.uuid4(),
                team_id=team.id,
                email="dev@example.com",
                github_login="devuser",
                role="owner",
            )
        )

        repo = Repository(
            id=uuid.uuid4(),
            team_id=team.id,
            github_repo_id=123456789,
            full_name="auditr/sample-app",
            default_branch="main",
            webhook_secret=None,
        )
        session.add(repo)
        session.flush()

        zero_embedding = [0.0] * 1536
        session.add(
            CodeEmbedding(
                id=uuid.uuid4(),
                repository_id=repo.id,
                file_path="src/main.py",
                start_line=1,
                end_line=40,
                chunk_text="def main():\n    print('hello')\n",
                embedding=zero_embedding,
                language="python",
            )
        )

        session.commit()
        print(f"Seeded team {team.name!r} and repository {repo.full_name!r}.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
