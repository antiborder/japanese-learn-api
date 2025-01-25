"""Remove romanian column from words table

Revision ID: a8dffb9afaf7
Revises: 05682287be08
Create Date: 2025-01-25 12:02:57.492462

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8dffb9afaf7'
down_revision: Union[str, None] = '05682287be08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column('words', 'romanian')


def downgrade() -> None:
    op.add_column('words', sa.Column('romanian', sa.String(length=255), nullable=True))
