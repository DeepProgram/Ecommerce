from sqlalchemy import Column, String, Integer, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base import BaseModel


class AttributeDataType(str, enum.Enum):
    """Enum for attribute data types"""
    STRING = "string"
    INTEGER = "integer"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"


class VariantAttributeType(BaseModel):
    """VariantAttributeType model - defines types of variant attributes (size, color, material, etc.)"""
    __tablename__ = "variant_attribute_types"

    name = Column(String(50), nullable=False, unique=True, index=True)  # e.g., "size", "color", "material"
    data_type = Column(Enum(AttributeDataType), nullable=False, default=AttributeDataType.STRING)
    display_name = Column(String(100), nullable=True)  # e.g., "Size", "Color", "Material"
    sort_order = Column(Integer, default=0, nullable=False)  # For ordering in UI
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationship
    attributes = relationship(
        "VariantAttribute",
        back_populates="attribute_type",
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self):
        return f"<VariantAttributeType(id={self.id}, name='{self.name}')>"

