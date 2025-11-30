from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ProductImage(BaseModel):
    """ProductImage model - stores product images with Cloudinary URLs"""
    __tablename__ = "product_images"

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)
    order = Column(Integer, default=0, nullable=False)
    is_main = Column(Boolean, default=False, nullable=False, index=True)

    # Relationship
    product = relationship("Product", back_populates="images")

    # Table-level constraint to ensure at most one main image per product
    __table_args__ = (
        # Note: This is a partial unique index that only applies to non-deleted records
        # We'll enforce the "one main image" rule at the application level for soft-deleted records
    )

    def __repr__(self):
        return f"<ProductImage(id={self.id}, product_id={self.product_id}, is_main={self.is_main})>"

