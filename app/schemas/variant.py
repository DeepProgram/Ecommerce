from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime


class VariantBase(BaseModel):
    """Base variant schema"""
    size: Optional[str] = Field(None, max_length=50, description="Variant size")
    color: Optional[str] = Field(None, max_length=50, description="Variant color")
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    price: Decimal = Field(..., ge=0, description="Variant price")
    stock: int = Field(0, ge=0, description="Stock quantity")


class VariantCreate(VariantBase):
    """Schema for creating a variant"""
    pass


class VariantUpdate(BaseModel):
    """Schema for updating a variant"""
    size: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, max_length=50)
    sku: Optional[str] = Field(None, max_length=100)
    price: Optional[Decimal] = Field(None, ge=0)
    stock: Optional[int] = Field(None, ge=0)


class VariantStockUpdate(BaseModel):
    """Schema for updating variant stock only"""
    stock: int = Field(..., ge=0, description="New stock quantity")


class VariantResponse(VariantBase):
    """Schema for variant response"""
    id: int
    product_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VariantCreateBatch(BaseModel):
    """Schema for creating multiple variants at once"""
    variants: List[VariantCreate] = Field(..., min_length=1, description="List of variants to create")

