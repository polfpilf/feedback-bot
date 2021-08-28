"""Create initial schema.

Create admin, target_chat and forwarded_message tables.

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

_TARGET_CHAT_TABLE = "target_chat"
_ADMIN_TABLE = "admin"
_FORWARDED_MESSAGE_TABLE = "forwarded_message"


def upgrade():
    op.create_table(
        _TARGET_CHAT_TABLE,
        sa.Column("chat_id", sa.BigInteger, primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        _ADMIN_TABLE,
        sa.Column("user_id", sa.BigInteger, primary_key=True),
        sa.Column(
            "target_chat_id",
            sa.BigInteger,
            sa.ForeignKey("target_chat.chat_id"),
            nullable=False,
        ),
    )
    op.create_table(
        _FORWARDED_MESSAGE_TABLE,
        sa.Column("forwarded_message_id", sa.Integer, primary_key=True),
        sa.Column("target_chat_id", sa.BigInteger, primary_key=True),
        sa.Column("origin_chat_id", sa.BigInteger, nullable=False),
    )


def downgrade():
    op.drop_table(_FORWARDED_MESSAGE_TABLE)
    op.drop_table(_ADMIN_TABLE)
    op.drop_table(_TARGET_CHAT_TABLE)
