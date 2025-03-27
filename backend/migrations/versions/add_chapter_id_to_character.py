"""add chapter_id to character model and remove appearances

Revision ID: 9f82b3c92a19
Revises: 
Create Date: 2023-11-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '9f82b3c92a19'
down_revision = None  # 请根据实际情况设置上一版本的ID
branch_labels = None
depends_on = None


def upgrade():
    # 添加 chapter_id 字段
    op.add_column('characters', sa.Column('chapter_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_characters_chapter_id', 'characters', 'chapters', ['chapter_id'], ['id'])
    
    # 移除 appearances 字段
    op.drop_column('characters', 'appearances')


def downgrade():
    # 还原 appearances 字段
    op.add_column('characters', sa.Column('appearances', postgresql.JSON(astext_type=sa.Text()), nullable=True))
    
    # 移除 chapter_id 字段
    op.drop_constraint('fk_characters_chapter_id', 'characters', type_='foreignkey')
    op.drop_column('characters', 'chapter_id') 