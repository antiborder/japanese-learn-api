"""create kanji-component and component tables

Revision ID: dc66a80e8e5a
Revises: ee0ceff2dc26
Create Date: 2025-01-31 12:00:00
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'dc66a80e8e5a'
down_revision: Union[str, None] = 'ee0ceff2dc26'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # componentsテーブルの作成
    op.create_table('components',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('character', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('en', sa.String(length=255), nullable=True),
        sa.Column('vi', sa.String(length=255), nullable=True)
    )

    # kanji-componentテーブルの作成
    op.create_table('kanji_component',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('kanji_id', sa.Integer(), sa.ForeignKey('kanjis.id'), nullable=False),
        sa.Column('component_id', sa.Integer(), sa.ForeignKey('components.id'), nullable=False)
    )

def downgrade() -> None:
    # kanji-componentテーブルの削除
    op.drop_table('kanji_component')
    
    # componentsテーブルの削除
    op.drop_table('components')