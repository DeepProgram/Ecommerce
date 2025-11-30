"""add variant attributes

Revision ID: 002_variant_attributes
Revises: 001_initial
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_variant_attributes'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create variant_attribute_types table
    op.create_table(
        'variant_attribute_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('data_type', sa.Enum('STRING', 'INTEGER', 'DECIMAL', 'BOOLEAN', name='attributedatatype'), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_variant_attribute_types_id'), 'variant_attribute_types', ['id'], unique=False)
    op.create_index(op.f('ix_variant_attribute_types_is_deleted'), 'variant_attribute_types', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_variant_attribute_types_name'), 'variant_attribute_types', ['name'], unique=True)
    op.create_index(op.f('ix_variant_attribute_types_is_active'), 'variant_attribute_types', ['is_active'], unique=False)

    # Create variant_attributes table
    op.create_table(
        'variant_attributes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('variant_id', sa.Integer(), nullable=False),
        sa.Column('attribute_type_id', sa.Integer(), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['variant_id'], ['product_variants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['attribute_type_id'], ['variant_attribute_types.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('variant_id', 'attribute_type_id', name='ix_variant_attribute_variant_type')
    )
    op.create_index(op.f('ix_variant_attributes_id'), 'variant_attributes', ['id'], unique=False)
    op.create_index(op.f('ix_variant_attributes_is_deleted'), 'variant_attributes', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_variant_attributes_variant_id'), 'variant_attributes', ['variant_id'], unique=False)
    op.create_index(op.f('ix_variant_attributes_attribute_type_id'), 'variant_attributes', ['attribute_type_id'], unique=False)
    op.create_index(op.f('ix_variant_attributes_value'), 'variant_attributes', ['value'], unique=False)
    op.create_index('ix_variant_attribute_variant_type', 'variant_attributes', ['variant_id', 'attribute_type_id'], unique=True)

    # Drop size and color columns from product_variants (replaced by dynamic attributes)
    op.drop_index('ix_product_variants_color', table_name='product_variants')
    op.drop_index('ix_product_variants_size', table_name='product_variants')
    op.drop_column('product_variants', 'color')
    op.drop_column('product_variants', 'size')

    # Insert initial attribute types (size and color) for backward compatibility
    op.execute("""
        INSERT INTO variant_attribute_types (name, data_type, display_name, sort_order, is_active, is_deleted, created_at, updated_at)
        VALUES 
            ('size', 'STRING', 'Size', 1, true, false, NOW(), NOW()),
            ('color', 'STRING', 'Color', 2, true, false, NOW(), NOW())
        ON CONFLICT (name) DO NOTHING
    """)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_index('ix_variant_attribute_variant_type', table_name='variant_attributes')
    op.drop_index(op.f('ix_variant_attributes_value'), table_name='variant_attributes')
    op.drop_index(op.f('ix_variant_attributes_attribute_type_id'), table_name='variant_attributes')
    op.drop_index(op.f('ix_variant_attributes_variant_id'), table_name='variant_attributes')
    op.drop_index(op.f('ix_variant_attributes_is_deleted'), table_name='variant_attributes')
    op.drop_index(op.f('ix_variant_attributes_id'), table_name='variant_attributes')
    op.drop_table('variant_attributes')

    op.drop_index(op.f('ix_variant_attribute_types_is_active'), table_name='variant_attribute_types')
    op.drop_index(op.f('ix_variant_attribute_types_name'), table_name='variant_attribute_types')
    op.drop_index(op.f('ix_variant_attribute_types_is_deleted'), table_name='variant_attribute_types')
    op.drop_index(op.f('ix_variant_attribute_types_id'), table_name='variant_attribute_types')
    op.drop_table('variant_attribute_types')
    
    # Restore size and color columns
    op.add_column('product_variants', sa.Column('size', sa.String(length=50), nullable=True))
    op.add_column('product_variants', sa.Column('color', sa.String(length=50), nullable=True))
    op.create_index(op.f('ix_product_variants_size'), 'product_variants', ['size'], unique=False)
    op.create_index(op.f('ix_product_variants_color'), 'product_variants', ['color'], unique=False)
    
    # Drop enum type
    op.execute("DROP TYPE IF EXISTS attributedatatype")

