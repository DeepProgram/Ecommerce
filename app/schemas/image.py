from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ImageBase(BaseModel):
    """Base image schema"""
    url: str = Field(..., description="Cloudinary image URL")
    alt_text: Optional[str] = Field(None, max_length=255, description="Alt text for the image")
    order: int = Field(0, ge=0, description="Display order")
    is_main: bool = Field(False, description="Whether this is the main image")


class ImageCreate(BaseModel):
    """Schema for creating an image (used internally)"""
    url: str
    alt_text: Optional[str] = None
    order: int = 0
    is_main: bool = False


class ImageUpdate(BaseModel):
    """Schema for updating an image"""
    alt_text: Optional[str] = Field(None, max_length=255)
    order: Optional[int] = Field(None, ge=0)


class ImageResponse(ImageBase):
    """Schema for image response"""
    id: int
    product_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ImageSizes(BaseModel):
    """Schema for image URLs in different sizes"""
    thumbnail: str = Field(..., description="Thumbnail size (200px width)")
    medium: str = Field(..., description="Medium size (600px width)")
    large: str = Field(..., description="Large size (1200px width)")
    original: str = Field(..., description="Original image URL")


class ImageWithSizesResponse(BaseModel):
    """Schema for image response with multiple sizes"""
    id: int
    product_id: int
    url: str = Field(..., description="Original Cloudinary image URL")
    sizes: ImageSizes = Field(..., description="Image URLs in different sizes")
    alt_text: Optional[str] = None
    order: int
    is_main: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
