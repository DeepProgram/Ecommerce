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

