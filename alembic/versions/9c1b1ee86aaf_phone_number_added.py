"""phone_number added

Revision ID: 9c1b1ee86aaf
Revises: 
Create Date: 2025-03-06 21:15:20.531916

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c1b1ee86aaf'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("phone_number", sa.String, nullable=True))


def downgrade() -> None:
    pass
