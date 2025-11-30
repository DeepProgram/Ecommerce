from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ProductBase(BaseModel):
    """Base product schema"""
    title: str = Field(..., min_length=1, max_length=255, description="Product title")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    description: Optional[str] = Field(None, description="Product description")


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """Schema for paginated product list response"""
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

