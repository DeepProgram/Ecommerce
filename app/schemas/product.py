from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from app.schemas.variant import VariantCreate, VariantResponse
from app.schemas.image import ImageWithSizesResponse


class ProductBase(BaseModel):
    """Base product schema"""
    title: str = Field(..., min_length=1, max_length=255, description="Product title")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    category: Optional[str] = Field(None, max_length=100, description="Product category")
    description: Optional[str] = Field(None, description="Product description")


class ProductCreate(ProductBase):
    """Schema for creating a product with variants and image"""
    variants: List[VariantCreate] = Field(..., min_length=1, description="At least one variant is required")


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    brand: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class ProductStatusUpdate(BaseModel):
    """Schema for updating product status"""
    status: str = Field(..., description="Product status: 'published' or 'archived'")


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: int
    is_deleted: bool
    status: str = Field(..., description="Product status: published or archived")
    thumbnail_url: Optional[str] = Field(None, description="Thumbnail image URL (200px width)")
    min_price: Optional[Decimal] = Field(None, description="Minimum price across all variants")
    images: List[ImageWithSizesResponse] = Field(default_factory=list, description="Product images with sizes (main image first)")
    variants: List[VariantResponse] = Field(default_factory=list, description="Product variants")
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

