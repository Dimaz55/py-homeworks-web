"""init

Revision ID: 402f6aa9ebcd
Revises: 
Create Date: 2022-07-26 11:51:26.868789

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '402f6aa9ebcd'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'sw_persons',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('birth_year', sa.Integer(), nullable=False),
        sa.Column('eye_color', sa.String(), nullable=False),
        sa.Column('films', sa.String(), nullable=False),
        sa.Column('gender', sa.String(), nullable=False),
        sa.Column('hair_color', sa.String(), nullable=False),
        sa.Column('height', sa.Integer(), nullable=False),
        sa.Column('homeworld', sa.String(), nullable=False),
        sa.Column('mass', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('skin_color', sa.String(), nullable=False),
        sa.Column('species', sa.String(), nullable=False),
        sa.Column('starships', sa.String(), nullable=False),
        sa.Column('vehicles', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('sw_persons')

