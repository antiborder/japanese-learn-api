"""Add level field to kanjis table

Revision ID: ee0ceff2dc26
Revises: a8dffb9afaf7
Create Date: 2025-01-26 16:05:31.360025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee0ceff2dc26'
down_revision: Union[str, None] = 'a8dffb9afaf7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # kanjisテーブルにlevelカラムを追加
    op.add_column('kanjis', sa.Column('level', sa.String(length=50), nullable=True))

def downgrade() -> None:
    # levelカラムを削除
    op.drop_column('kanjis', 'level')
