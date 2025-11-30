from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class ProductVideo(BaseModel):
    """ProductVideo model - stores product videos with Cloudinary URLs and metadata"""
    __tablename__ = "product_videos"

    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    thumbnail_url = Column(String(500), nullable=True)
    duration = Column(Numeric(10, 2), nullable=True)  # Duration in seconds
    format = Column(String(20), nullable=True)  # e.g., mp4, webm
    resolution = Column(String(20), nullable=True)  # e.g., 1080p, 720p
    order = Column(Integer, default=0, nullable=False)
    is_main = Column(Boolean, default=False, nullable=False, index=True)

    # Relationship
    product = relationship("Product", back_populates="videos")

    def __repr__(self):
        return f"<ProductVideo(id={self.id}, product_id={self.product_id}, format='{self.format}')>"

