"""product search indexes and FTS5

Revision ID: 002
Revises: 001
Create Date: 2026-06-06
"""

from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_name ON products(name)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_products_brand ON products(brand)")

    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
            name,
            brand,
            content='products',
            content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 2'
        )
        """
    )

    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS products_fts_ai AFTER INSERT ON products BEGIN
            INSERT INTO products_fts(rowid, name, brand)
            VALUES (new.rowid, new.name, COALESCE(new.brand, ''));
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS products_fts_ad AFTER DELETE ON products BEGIN
            INSERT INTO products_fts(products_fts, rowid, name, brand)
            VALUES ('delete', old.rowid, old.name, COALESCE(old.brand, ''));
        END
        """
    )
    op.execute(
        """
        CREATE TRIGGER IF NOT EXISTS products_fts_au AFTER UPDATE ON products BEGIN
            INSERT INTO products_fts(products_fts, rowid, name, brand)
            VALUES ('delete', old.rowid, old.name, COALESCE(old.brand, ''));
            INSERT INTO products_fts(rowid, name, brand)
            VALUES (new.rowid, new.name, COALESCE(new.brand, ''));
        END
        """
    )
    op.execute("INSERT INTO products_fts(products_fts) VALUES ('rebuild')")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS products_fts_au")
    op.execute("DROP TRIGGER IF EXISTS products_fts_ad")
    op.execute("DROP TRIGGER IF EXISTS products_fts_ai")
    op.execute("DROP TABLE IF EXISTS products_fts")
    op.execute("DROP INDEX IF EXISTS ix_products_brand")
    op.execute("DROP INDEX IF EXISTS ix_products_name")
