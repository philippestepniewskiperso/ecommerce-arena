"""add products search_vector tsvector

Revision ID: f5509f12253c
Revises: 97bff57edc6f
Create Date: 2026-04-24 19:55:20.754000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'f5509f12253c'
down_revision: Union[str, None] = '97bff57edc6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('products', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    op.create_index('ix_products_search_vector', 'products', ['search_vector'], postgresql_using='gin')

    op.execute("""
        CREATE OR REPLACE FUNCTION products_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('simple', coalesce(NEW.name, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(NEW.short_description, '')), 'B') ||
                setweight(to_tsvector('simple', coalesce(NEW.description, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER products_search_vector_trigger
        BEFORE INSERT OR UPDATE OF name, short_description, description
        ON products
        FOR EACH ROW EXECUTE FUNCTION products_search_vector_update();
    """)

    op.execute("""
        UPDATE products SET
            search_vector =
                setweight(to_tsvector('simple', coalesce(name, '')), 'A') ||
                setweight(to_tsvector('simple', coalesce(short_description, '')), 'B') ||
                setweight(to_tsvector('simple', coalesce(description, '')), 'C');
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS products_search_vector_trigger ON products")
    op.execute("DROP FUNCTION IF EXISTS products_search_vector_update")
    op.drop_index('ix_products_search_vector', table_name='products')
    op.drop_column('products', 'search_vector')
