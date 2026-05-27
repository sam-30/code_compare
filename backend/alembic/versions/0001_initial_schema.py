"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-05-26
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("source_type", sa.Enum("local", "git", "zip", name="sourcetype"), nullable=False, server_default="local"),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("status", sa.Enum("pending", "ingesting", "ready", "failed", name="repositorystatus"), nullable=False, server_default="pending"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "repository_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repo_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relative_path", sa.String(1024), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("line_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_repository_files_repo_id", "repository_files", ["repo_id"])

    op.create_table(
        "comparison_configs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.String(1024), nullable=False, server_default=""),
        sa.Column("method_weights", JSONB(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="false"),
    )

    op.create_table(
        "comparisons",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repo_a_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("repo_b_id", sa.Integer(), sa.ForeignKey("repositories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("status", sa.Enum("pending", "running", "complete", "failed", name="comparisonstatus"), nullable=False, server_default="pending"),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("config", JSONB(), nullable=False, server_default="{}"),
        sa.Column("error_message", sa.String(2048), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "comparison_method_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comparison_id", sa.Integer(), sa.ForeignKey("comparisons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("method_id", sa.String(64), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("details", JSONB(), nullable=False, server_default="{}"),
        sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("ix_comparison_method_results_comparison_id", "comparison_method_results", ["comparison_id"])

    op.create_table(
        "comparison_file_matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("comparison_id", sa.Integer(), sa.ForeignKey("comparisons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_a_path", sa.String(1024), nullable=False),
        sa.Column("file_b_path", sa.String(1024), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("method_id", sa.String(64), nullable=False),
        sa.Column("detail", JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_comparison_file_matches_comparison_id", "comparison_file_matches", ["comparison_id"])


def downgrade() -> None:
    op.drop_table("comparison_file_matches")
    op.drop_table("comparison_method_results")
    op.drop_table("comparisons")
    op.drop_table("comparison_configs")
    op.drop_table("repository_files")
    op.drop_table("repositories")
    op.execute("DROP TYPE IF EXISTS comparisonstatus")
    op.execute("DROP TYPE IF EXISTS repositorystatus")
    op.execute("DROP TYPE IF EXISTS sourcetype")
