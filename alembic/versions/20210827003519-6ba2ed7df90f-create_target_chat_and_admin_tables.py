"""Create target_chat and admin tables

Revision ID: 6ba2ed7df90f
Revises: 3fcf475aa60c
Create Date: 2021-08-27 00:35:19.941085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6ba2ed7df90f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "target_chat",
        sa.Column("chat_id", sa.BigInteger, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "admin",
        sa.Column("user_id", sa.BigInteger, primary_key=True),
        sa.Column(
            "target_chat_id",
            sa.BigInteger,
            sa.ForeignKey("target_chat.chat_id"),
            nullable=False,
        )
    )


def downgrade():
    op.drop_table("admin")
    op.drop_table("target_chat")