from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class VideoBase(BaseModel):
    """Base video schema"""
    url: str = Field(..., description="Cloudinary video URL")
    thumbnail_url: Optional[str] = Field(None, description="Cloudinary thumbnail URL")
    duration: Optional[Decimal] = Field(None, description="Video duration in seconds")
    format: Optional[str] = Field(None, max_length=20, description="Video format (e.g., mp4, webm)")
    resolution: Optional[str] = Field(None, max_length=20, description="Video resolution (e.g., 1080p, 720p)")
    order: int = Field(0, ge=0, description="Display order")
    is_main: bool = Field(False, description="Whether this is the main video")


class VideoCreate(BaseModel):
    """Schema for creating a video (used internally)"""
    url: str
    thumbnail_url: Optional[str] = None
    duration: Optional[Decimal] = None
    format: Optional[str] = None
    resolution: Optional[str] = None
    order: int = 0
    is_main: bool = False


class VideoUpdate(BaseModel):
    """Schema for updating a video"""
    order: Optional[int] = Field(None, ge=0)


class VideoResponse(VideoBase):
    """Schema for video response"""
    id: int
    product_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

