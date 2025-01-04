"""Add name column to words table

Revision ID: 75b77cdd55b6
Revises: d98aaa956862
Create Date: 2025-01-04 20:07:10.986787

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '75b77cdd55b6'
down_revision: Union[str, None] = 'd98aaa956862'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the 'name' column to the 'words' table
    op.add_column('words', sa.Column('name', sa.String(length=255), nullable=True))


def downgrade() -> None:
    # Remove the 'name' column from the 'words' table
    op.drop_column('words', 'name')
