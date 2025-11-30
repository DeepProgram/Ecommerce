from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Product(BaseModel):
    """Product model - main entity for products"""
    __tablename__ = "products"

    title = Column(String(255), nullable=False, index=True)
    brand = Column(String(100), nullable=True, index=True)
    category = Column(String(100), nullable=True, index=True)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default='published', index=True, server_default='published')

    # Relationships
    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )
    images = relationship(
        "ProductImage",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductImage.order",
        lazy="dynamic"
    )
    videos = relationship(
        "ProductVideo",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductVideo.order",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title}')>"

