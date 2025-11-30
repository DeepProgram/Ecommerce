from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from decimal import Decimal
import io
from app.core.database import get_db
from app.models.product import Product
from app.models.video import ProductVideo
from app.schemas.video import VideoResponse
from app.utils.cloudinary_utils import (
    upload_video_to_cloudinary,
    upload_large_video_to_cloudinary,
    delete_from_cloudinary,
    extract_cloudinary_public_id
)
from app.services.elasticsearch_service import index_product

router = APIRouter(prefix="/products", tags=["videos"])

# Maximum video file size: 500MB (for regular upload)
MAX_VIDEO_SIZE_MB = 500
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024

# Allowed video MIME types
ALLOWED_VIDEO_TYPES = [
    "video/mp4",
    "video/webm",
    "video/quicktime",  # .mov
    "video/x-msvideo",  # .avi
    "video/x-matroska",  # .mkv
]


def validate_video_file(file: UploadFile, max_size_bytes: int = MAX_VIDEO_SIZE_BYTES) -> None:
    """
    Validate video file before upload.
    
    Args:
        file: UploadFile to validate
        max_size_bytes: Maximum file size in bytes
    
    Raises:
        HTTPException: If validation fails
    """
    # Check MIME type
    if not file.content_type or file.content_type not in ALLOWED_VIDEO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid video format. Allowed types: {', '.join(ALLOWED_VIDEO_TYPES)}"
        )
    
    # Note: File size validation should be done after reading the file
    # since UploadFile doesn't expose size before reading


@router.post("/{product_id}/upload-video", response_model=VideoResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_video(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a product video.
    - Validates MIME type and size
    - Uploads to Cloudinary (uses upload_large for files > 100MB)
    - Cloudinary handles transcoding and generates thumbnails
    - Stores ProductVideo record with URL and metadata
    """
    # Verify product exists and is not deleted
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Validate MIME type
    validate_video_file(file)
    
    # Read file bytes
    video_bytes = await file.read()
    
    # Validate file size
    if len(video_bytes) > MAX_VIDEO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video file too large. Maximum size: {MAX_VIDEO_SIZE_MB}MB"
        )
    
    # Convert bytes to BytesIO for Cloudinary
    video_file = io.BytesIO(video_bytes)
    video_file.seek(0)
    
    # Upload to Cloudinary
    try:
        public_id = f"products/{product_id}/videos/{file.filename or 'video'}"
        
        # Use upload_large for files > 100MB, otherwise use regular upload
        if len(video_bytes) > 100 * 1024 * 1024:  # 100MB
            cloudinary_result = upload_large_video_to_cloudinary(
                video_file,
                public_id=public_id,
                folder="products/videos"
            )
        else:
            cloudinary_result = upload_video_to_cloudinary(
                video_file,
                public_id=public_id,
                folder="products/videos"
            )
        
        # Extract metadata from Cloudinary response
        video_url = cloudinary_result.get("secure_url")
        thumbnail_url = None
        
        # Get thumbnail from eager transformations or generate one
        if "eager" in cloudinary_result and cloudinary_result["eager"]:
            # Use the first eager transformation as thumbnail
            thumbnail_url = cloudinary_result["eager"][0].get("secure_url")
        elif "thumbnail_url" in cloudinary_result:
            thumbnail_url = cloudinary_result.get("thumbnail_url")
        
        # Extract duration, format, resolution
        duration = cloudinary_result.get("duration")
        if duration:
            duration = Decimal(str(duration))
        
        format_type = cloudinary_result.get("format")
        resolution = cloudinary_result.get("width") and cloudinary_result.get("height")
        if resolution:
            resolution = f"{cloudinary_result.get('height')}p"
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video to Cloudinary: {str(e)}"
        )
    
    # Check if this is the first video for the product
    existing_videos_count = db.query(ProductVideo).filter(
        ProductVideo.product_id == product_id,
        ProductVideo.is_deleted == False
    ).count()
    
    is_main = existing_videos_count == 0
    
    # If setting as main, unset other main videos
    if is_main:
        db.query(ProductVideo).filter(
            ProductVideo.product_id == product_id,
            ProductVideo.is_main == True,
            ProductVideo.is_deleted == False
        ).update({"is_main": False})
    
    # Get the next order value
    max_order = db.query(ProductVideo).filter(
        ProductVideo.product_id == product_id,
        ProductVideo.is_deleted == False
    ).order_by(ProductVideo.order.desc()).first()
    
    next_order = (max_order.order + 1) if max_order else 0
    
    # Create ProductVideo record
    product_video = ProductVideo(
        product_id=product_id,
        url=video_url,
        thumbnail_url=thumbnail_url,
        duration=duration,
        format=format_type,
        resolution=resolution,
        order=next_order,
        is_main=is_main,
        is_deleted=False
    )
    
    db.add(product_video)
    db.commit()
    db.refresh(product_video)
    
    # Re-index product in Elasticsearch (video added)
    await index_product(product_id, db)
    
    return product_video


@router.delete("/{product_id}/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_video(
    product_id: int,
    video_id: int,
    delete_from_cloudinary_flag: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete a product video.
    - Soft deletes the video record
    - Optionally deletes from Cloudinary
    """
    # Verify product exists
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Get video
    video = db.query(ProductVideo).filter(
        ProductVideo.id == video_id,
        ProductVideo.product_id == product_id,
        ProductVideo.is_deleted == False
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with id {video_id} not found for product {product_id}"
        )
    
    # Optionally delete from Cloudinary
    if delete_from_cloudinary_flag:
        try:
            public_id = extract_cloudinary_public_id(video.url)
            if public_id:
                delete_from_cloudinary(public_id, resource_type="video")
        except Exception as e:
            # Log error but don't fail the request
            pass
    
    # If this was the main video, set another video as main (if available)
    if video.is_main:
        # Find another video to set as main
        other_video = db.query(ProductVideo).filter(
            ProductVideo.product_id == product_id,
            ProductVideo.id != video_id,
            ProductVideo.is_deleted == False
        ).order_by(ProductVideo.order).first()
        
        if other_video:
            other_video.is_main = True
    
    # Soft delete
    video.is_deleted = True
    db.commit()
    
    # Re-index product in Elasticsearch (video deleted)
    await index_product(product_id, db)
    
    return None


@router.patch("/{product_id}/videos/{video_id}/set-main", response_model=VideoResponse)
async def set_main_video(
    product_id: int,
    video_id: int,
    db: Session = Depends(get_db)
):
    """
    Set a video as the main video for a product.
    - Unsets all other main videos for the product
    - Sets the specified video as main
    """
    # Verify product exists
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Get video
    video = db.query(ProductVideo).filter(
        ProductVideo.id == video_id,
        ProductVideo.product_id == product_id,
        ProductVideo.is_deleted == False
    ).first()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with id {video_id} not found for product {product_id}"
        )
    
    # Unset all other main videos for this product
    db.query(ProductVideo).filter(
        ProductVideo.product_id == product_id,
        ProductVideo.id != video_id,
        ProductVideo.is_main == True,
        ProductVideo.is_deleted == False
    ).update({"is_main": False})
    
    # Set this video as main
    video.is_main = True
    db.commit()
    db.refresh(video)
    
    # Re-index product in Elasticsearch (main video changed)
    await index_product(product_id, db)
    
    return video

