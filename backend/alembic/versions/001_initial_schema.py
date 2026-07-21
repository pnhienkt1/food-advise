"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-06-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=True),
        sa.Column("license", sa.String(length=200), nullable=True),
        sa.Column("last_import_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "products",
        sa.Column("barcode", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("brand", sa.String(length=200), nullable=True),
        sa.Column("category", sa.String(length=200), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("ingredients_text", sa.Text(), nullable=True),
        sa.Column("allergens", sa.Text(), nullable=True),
        sa.Column("nutri_score", sa.String(length=5), nullable=True),
        sa.Column("nova_group", sa.Integer(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("barcode"),
    )
    op.create_table(
        "product_nutrients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.String(length=50), nullable=False),
        sa.Column("nutrient_code", sa.String(length=50), nullable=False),
        sa.Column("amount", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("per_100g", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["barcode"], ["products.barcode"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("barcode", "nutrient_code", name="uq_nutrient"),
    )
    op.create_table(
        "product_ingredients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.String(length=50), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=300), nullable=False),
        sa.Column("normalized_name", sa.String(length=300), nullable=True),
        sa.ForeignKeyConstraint(["barcode"], ["products.barcode"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product_additives",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.String(length=50), nullable=False),
        sa.Column("e_number", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=True),
        sa.Column("risk_level", sa.String(length=20), nullable=True),
        sa.Column("source_ref", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(["barcode"], ["products.barcode"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "product_alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("barcode", sa.String(length=50), nullable=False),
        sa.Column("alert_type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=500), nullable=True),
        sa.Column("valid_from", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["barcode"], ["products.barcode"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("product_alerts")
    op.drop_table("product_additives")
    op.drop_table("product_ingredients")
    op.drop_table("product_nutrients")
    op.drop_table("products")
    op.drop_table("data_sources")
