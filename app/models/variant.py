from sqlalchemy import Column, String, Integer, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ProductVariant(BaseModel):
    """ProductVariant model - holds size, color, stock, and pricing"""
    __tablename__ = "product_variants"

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    sku = Column(String(100), nullable=True, unique=True, index=True)
    price = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0, nullable=False)

    # Relationships
    product = relationship("Product", back_populates="variants")
    attributes = relationship(
        "VariantAttribute",
        back_populates="variant",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<ProductVariant(id={self.id}, product_id={self.product_id}, sku='{self.sku}')>"

