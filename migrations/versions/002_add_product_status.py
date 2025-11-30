"""add product status

Revision ID: 002_add_status
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_status'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add status column to products table with default 'published'
    op.add_column('products', sa.Column('status', sa.String(length=20), nullable=False, server_default='published'))
    op.create_index(op.f('ix_products_status'), 'products', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_products_status'), table_name='products')
    op.drop_column('products', 'status')

