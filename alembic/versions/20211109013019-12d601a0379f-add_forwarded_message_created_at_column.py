"""Add forwarded_message.created_at column

Revision ID: 12d601a0379f
Revises: 6ba2ed7df90f
Create Date: 2021-11-09 01:30:19.723751

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '12d601a0379f'
down_revision = '6ba2ed7df90f'
branch_labels = None
depends_on = None

_TARGET_TABLE = "forwarded_message"
_COLUMN_NAME = "created_at"


def upgrade():
    op.add_column(
        _TARGET_TABLE,
        sa.Column(_COLUMN_NAME, sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_column(_TARGET_TABLE, _COLUMN_NAME)
