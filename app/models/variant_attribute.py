from sqlalchemy import Column, String, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class VariantAttribute(BaseModel):
    """VariantAttribute model - stores dynamic attribute values for variants"""
    __tablename__ = "variant_attributes"

    variant_id = Column(Integer, ForeignKey("product_variants.id", ondelete="CASCADE"), nullable=False, index=True)
    attribute_type_id = Column(Integer, ForeignKey("variant_attribute_types.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(String(255), nullable=False, index=True)  # Store as string, convert based on data_type

    # Relationships
    variant = relationship("ProductVariant", back_populates="attributes")
    attribute_type = relationship("VariantAttributeType", back_populates="attributes")

    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_variant_attribute_variant_type', 'variant_id', 'attribute_type_id', unique=True),
    )

    def __repr__(self):
        return f"<VariantAttribute(id={self.id}, variant_id={self.variant_id}, value='{self.value}')>"

