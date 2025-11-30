from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class VariantAttributeBase(BaseModel):
    """Base variant attribute schema"""
    attribute_type_id: int = Field(..., description="ID of the attribute type")
    value: str = Field(..., max_length=255, description="Attribute value")


class VariantAttributeCreate(VariantAttributeBase):
    """Schema for creating a variant attribute"""
    pass


class VariantAttributeUpdate(BaseModel):
    """Schema for updating a variant attribute"""
    value: Optional[str] = Field(None, max_length=255)


class VariantAttributeResponse(VariantAttributeBase):
    """Schema for variant attribute response"""
    id: int
    variant_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    # Include attribute type info for convenience
    attribute_type_name: Optional[str] = None
    attribute_type_display_name: Optional[str] = None

    class Config:
        from_attributes = True

