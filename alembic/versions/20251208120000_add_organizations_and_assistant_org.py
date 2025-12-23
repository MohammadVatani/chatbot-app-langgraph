"""add organizations and assistant org relationships

Revision ID: 4f8dfe7c3c12
Revises: d042a0ca1cb5
Create Date: 2025-12-08 12:00:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "4f8dfe7c3c12"
down_revision = "d042a0ca1cb5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("org_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("org_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(
        "idx_organizations_name", "organizations", ["name"], unique=True
    )

    op.create_table(
        "organization_members",
        sa.Column("org_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("invited_by", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["org_id"], ["organizations.org_id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("org_id", "user_id"),
    )
    op.create_index(
        "idx_org_member_role", "organization_members", ["org_id", "role"], unique=False
    )

    op.add_column(
        "assistant", sa.Column("org_id", sa.Text(), nullable=True)
    )
    op.create_foreign_key(
        "assistant_org_id_fkey",
        "assistant",
        "organizations",
        ["org_id"],
        ["org_id"],
        ondelete="SET NULL",
    )
    op.create_index("idx_assistant_org", "assistant", ["org_id"], unique=False)



def downgrade() -> None:
    op.drop_index("idx_assistant_org", table_name="assistant")
    op.drop_constraint("assistant_org_id_fkey", "assistant", type_="foreignkey")
    op.drop_column("assistant", "org_id")
    op.drop_index("idx_org_member_role", table_name="organization_members")
    op.drop_table("organization_members")
    op.drop_index("idx_organizations_name", table_name="organizations")
    op.drop_table("organizations")
