from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.models.product import Product
from app.models.image import ProductImage
from app.schemas.image import ImageResponse, ImageWithSizesResponse, ImageSizes
from app.utils.image_processing import process_product_image, validate_image_file
from app.utils.cloudinary_utils import (
    upload_image_to_cloudinary, 
    delete_from_cloudinary, 
    extract_cloudinary_public_id,
    get_image_sizes
)
from typing import List
from app.services.elasticsearch_service import index_product
import io

router = APIRouter(prefix="/products", tags=["images"])


@router.post("/{product_id}/upload-image", response_model=ImageResponse, status_code=status.HTTP_201_CREATED)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    alt_text: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Upload and process a product image.
    - Validates the image file
    - Processes preserving aspect ratio (no cropping, no white padding), max 1200px, WebP format
    - Portrait images stay portrait, landscape stays landscape
    - Uploads to Cloudinary
    - Creates ProductImage record
    - Sets as main image if it's the first image for the product
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
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Read file bytes
    image_bytes = await file.read()
    
    # Validate image file
    try:
        validate_image_file(image_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Process image (preserves aspect ratio, max 1200px, WebP - no cropping, no white padding)
    try:
        processed_image = process_product_image(
            image_bytes,
            max_dimension=1200,
            format_preference="WEBP",
            preserve_aspect_ratio=True
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image processing failed: {str(e)}"
        )
    
    # Upload to Cloudinary
    # Cloudinary can generate multiple sizes via transformations, so we upload the large size
    try:
        public_id = f"products/{product_id}/{file.filename or 'image'}"
        cloudinary_result = upload_image_to_cloudinary(
            processed_image.bytes,
            public_id=public_id,
            folder="products"
        )
        image_url = cloudinary_result.get("secure_url")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image to Cloudinary: {str(e)}"
        )
    
    # Check if this is the first image for the product
    existing_images_count = db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False
    ).count()
    
    is_main = existing_images_count == 0
    
    # If setting as main, unset other main images
    if is_main:
        db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.is_main == True,
            ProductImage.is_deleted == False
        ).update({"is_main": False})
    
    # Get the next order value
    max_order = db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False
    ).order_by(ProductImage.order.desc()).first()
    
    next_order = (max_order.order + 1) if max_order else 0
    
    # Create ProductImage record
    product_image = ProductImage(
        product_id=product_id,
        url=image_url,
        alt_text=alt_text,
        order=next_order,
        is_main=is_main,
        is_deleted=False
    )
    
    db.add(product_image)
    db.commit()
    db.refresh(product_image)
    
    # Re-index product in Elasticsearch (image added)
    await index_product(product_id, db)
    
    return product_image


@router.delete("/{product_id}/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product_image(
    product_id: int,
    image_id: int,
    delete_from_cloudinary_flag: bool = False,
    db: Session = Depends(get_db)
):
    """
    Delete a product image.
    - Soft deletes the image record
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
    
    # Get image
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found for product {product_id}"
        )
    
    # Optionally delete from Cloudinary
    if delete_from_cloudinary_flag:
        try:
            public_id = extract_cloudinary_public_id(image.url)
            if public_id:
                delete_from_cloudinary(public_id, resource_type="image")
        except Exception as e:
            # Log error but don't fail the request
            pass
    
    # If this was the main image, set another image as main (if available)
    if image.is_main:
        # Find another image to set as main
        other_image = db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.id != image_id,
            ProductImage.is_deleted == False
        ).order_by(ProductImage.order).first()
        
        if other_image:
            other_image.is_main = True
    
    # Soft delete
    image.is_deleted = True
    db.commit()
    
    # Re-index product in Elasticsearch (image deleted)
    await index_product(product_id, db)
    
    return None


@router.patch("/{product_id}/images/{image_id}/set-main", response_model=ImageResponse)
async def set_main_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Set an image as the main image for a product.
    - Unsets all other main images for the product
    - Sets the specified image as main
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
    
    # Get image
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found for product {product_id}"
        )
    
    # Unset all other main images for this product
    db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.id != image_id,
        ProductImage.is_main == True,
        ProductImage.is_deleted == False
    ).update({"is_main": False})
    
    # Set this image as main
    image.is_main = True
    db.commit()
    db.refresh(image)
    
    # Re-index product in Elasticsearch (main image changed)
    await index_product(product_id, db)
    
    return image


@router.get("/{product_id}/images", response_model=List[ImageWithSizesResponse])
async def get_product_images(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all images for a product with multiple sizes (thumbnail, medium, large, original).
    Uses Cloudinary transformations to generate different sizes on-demand.
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
    
    # Get all non-deleted images for the product
    images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False
    ).order_by(ProductImage.order).all()
    
    # Build response with sizes
    result = []
    for image in images:
        sizes_dict = get_image_sizes(image.url)
        result.append(ImageWithSizesResponse(
            id=image.id,
            product_id=image.product_id,
            url=image.url,
            sizes=ImageSizes(**sizes_dict),
            alt_text=image.alt_text,
            order=image.order,
            is_main=image.is_main,
            is_deleted=image.is_deleted,
            created_at=image.created_at,
            updated_at=image.updated_at
        ))
    
    return result


@router.get("/{product_id}/images/{image_id}", response_model=ImageWithSizesResponse)
async def get_product_image(
    product_id: int,
    image_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific product image with multiple sizes (thumbnail, medium, large, original).
    Uses Cloudinary transformations to generate different sizes on-demand.
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
    
    # Get image
    image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False
    ).first()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Image with id {image_id} not found for product {product_id}"
        )
    
    # Get sizes using Cloudinary transformations
    sizes_dict = get_image_sizes(image.url)
    
    return ImageWithSizesResponse(
        id=image.id,
        product_id=image.product_id,
        url=image.url,
        sizes=ImageSizes(**sizes_dict),
        alt_text=image.alt_text,
        order=image.order,
        is_main=image.is_main,
        is_deleted=image.is_deleted,
        created_at=image.created_at,
        updated_at=image.updated_at
    )

