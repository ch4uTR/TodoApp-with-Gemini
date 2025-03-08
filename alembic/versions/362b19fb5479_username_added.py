"""username  added

Revision ID: 362b19fb5479
Revises: 9c1b1ee86aaf
Create Date: 2025-03-06 23:21:51.743400

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '362b19fb5479'
down_revision: Union[str, None] = '9c1b1ee86aaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String, nullable=True))


def downgrade() -> None:
    pass
