from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.variant_attribute_type import AttributeDataType


class VariantAttributeTypeBase(BaseModel):
    """Base variant attribute type schema"""
    name: str = Field(..., min_length=1, max_length=50, description="Unique name (e.g., 'size', 'color', 'material')")
    data_type: AttributeDataType = Field(..., description="Data type for the attribute")
    display_name: Optional[str] = Field(None, max_length=100, description="Display name for UI")
    sort_order: int = Field(0, ge=0, description="Sort order for display")
    is_active: bool = Field(True, description="Whether this attribute type is active")


class VariantAttributeTypeCreate(VariantAttributeTypeBase):
    """Schema for creating a variant attribute type"""
    pass


class VariantAttributeTypeUpdate(BaseModel):
    """Schema for updating a variant attribute type"""
    data_type: Optional[AttributeDataType] = None
    display_name: Optional[str] = Field(None, max_length=100)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class VariantAttributeTypeResponse(VariantAttributeTypeBase):
    """Schema for variant attribute type response"""
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

