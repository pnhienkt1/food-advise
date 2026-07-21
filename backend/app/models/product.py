from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    url: Mapped[str | None] = mapped_column(String(500))
    license: Mapped[str | None] = mapped_column(String(200))
    last_import_at: Mapped[datetime | None] = mapped_column(DateTime)


class Product(Base):
    __tablename__ = "products"

    barcode: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(200))
    category: Mapped[str | None] = mapped_column(String(200))
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    image_url: Mapped[str | None] = mapped_column(String(500))
    ingredients_text: Mapped[str | None] = mapped_column(Text)
    allergens: Mapped[str | None] = mapped_column(Text)
    nutri_score: Mapped[str | None] = mapped_column(String(5))
    nova_group: Mapped[int | None] = mapped_column(Integer)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime)

    nutrients: Mapped[list["ProductNutrient"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    ingredients: Mapped[list["ProductIngredient"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    additives: Mapped[list["ProductAdditive"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    alerts: Mapped[list["ProductAlert"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class ProductNutrient(Base):
    __tablename__ = "product_nutrients"
    __table_args__ = (UniqueConstraint("barcode", "nutrient_code", name="uq_nutrient"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(50), ForeignKey("products.barcode", ondelete="CASCADE"))
    nutrient_code: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(20))
    per_100g: Mapped[bool] = mapped_column(default=True)

    product: Mapped["Product"] = relationship(back_populates="nutrients")


class ProductIngredient(Base):
    __tablename__ = "product_ingredients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(50), ForeignKey("products.barcode", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(300))

    product: Mapped["Product"] = relationship(back_populates="ingredients")


class ProductAdditive(Base):
    __tablename__ = "product_additives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(50), ForeignKey("products.barcode", ondelete="CASCADE"))
    e_number: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200))
    risk_level: Mapped[str | None] = mapped_column(String(20))
    source_ref: Mapped[str | None] = mapped_column(String(200))

    product: Mapped["Product"] = relationship(back_populates="additives")


class ProductAlert(Base):
    __tablename__ = "product_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    barcode: Mapped[str] = mapped_column(String(50), ForeignKey("products.barcode", ondelete="CASCADE"))
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500))
    valid_from: Mapped[datetime | None] = mapped_column(DateTime)

    product: Mapped["Product"] = relationship(back_populates="alerts")
