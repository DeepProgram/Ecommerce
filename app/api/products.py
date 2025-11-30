from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from decimal import Decimal
import json
from app.core.database import get_db
from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.image import ProductImage
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    ProductStatusUpdate
)
from app.schemas.variant import VariantCreateBatch, VariantResponse, VariantCreate
from app.services.elasticsearch_service import index_product, delete_product_from_index
from app.utils.cloudinary_utils import get_image_url_with_transformation, upload_image_to_cloudinary, get_image_sizes
from app.utils.image_processing import process_product_image, validate_image_file
from app.schemas.image import ImageWithSizesResponse, ImageSizes

router = APIRouter(prefix="/products", tags=["products"])


def get_product_images_with_sizes(product_id: int, db: Session) -> List[ImageWithSizesResponse]:
    """
    Helper function to get all product images with sizes, sorted with main image first.
    """
    # Get all images for the product
    all_images = db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False
    ).all()
    
    # Separate main image and other images
    main_images = [img for img in all_images if img.is_main]
    other_images = [img for img in all_images if not img.is_main]
    
    # Sort main images by order, then other images by order
    main_images_sorted = sorted(main_images, key=lambda img: img.order)
    other_images_sorted = sorted(other_images, key=lambda img: img.order)
    
    # Combine: main images first, then other images
    sorted_images = main_images_sorted + other_images_sorted
    
    # Build images response with sizes
    images_response = []
    for image in sorted_images:
        sizes_dict = get_image_sizes(image.url)
        images_response.append(ImageWithSizesResponse(
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
    
    return images_response


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    title: str = Form(..., min_length=1, max_length=255),
    brand: str = Form(None),
    category: str = Form(None),
    description: str = Form(None),
    variants_json: str = Form(..., description="JSON array of variants"),
    image: UploadFile = File(..., description="Product image file"),
    alt_text: str = Form(None),
    db: Session = Depends(get_db)
):
    """
    Create a new product with at least one variant and an image.
    Requires:
    - Product details (title, brand, category, description)
    - At least one variant (JSON array)
    - One image file
    """
    # Parse variants JSON
    try:
        variants_data = json.loads(variants_json)
        if not isinstance(variants_data, list) or len(variants_data) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one variant is required"
            )
        variants = [VariantCreate(**v) for v in variants_data]
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format for variants"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid variant data: {str(e)}"
        )
    
    # Validate image file
    if not image.content_type or not image.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image"
        )
    
    # Read and validate image
    image_bytes = await image.read()
    try:
        validate_image_file(image_bytes)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Process image
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
    
    # Create product instance
    product = Product(
        title=title,
        brand=brand if brand else None,
        category=category if category else None,
        description=description if description else None,
        is_deleted=False,
        status='published'
    )
    
    db.add(product)
    db.flush()  # Flush to get product.id
    
    # Check for duplicate SKUs in the request
    skus = [v.sku for v in variants if v.sku]
    if len(skus) != len(set(skus)):
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate SKUs found in the request"
        )
    
    # Check if any SKU already exists in the database
    if skus:
        existing_sku = db.query(ProductVariant).filter(
            ProductVariant.sku.in_(skus),
            ProductVariant.is_deleted == False
        ).first()
        if existing_sku:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SKU '{existing_sku.sku}' already exists"
            )
    
    # Create variants
    created_variants = []
    for variant in variants:
        new_variant = ProductVariant(
            product_id=product.id,
            size=variant.size,
            color=variant.color,
            sku=variant.sku,
            price=variant.price,
            stock=variant.stock,
            is_deleted=False
        )
        db.add(new_variant)
        created_variants.append(new_variant)
    
    # Upload image to Cloudinary
    try:
        public_id = f"products/{product.id}/{image.filename or 'image'}"
        cloudinary_result = upload_image_to_cloudinary(
            processed_image.bytes,
            public_id=public_id,
            folder="products"
        )
        image_url = cloudinary_result.get("secure_url")
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image to Cloudinary: {str(e)}"
        )
    
    # Create product image (set as main since it's the first)
    product_image = ProductImage(
        product_id=product.id,
        url=image_url,
        alt_text=alt_text if alt_text else None,
        order=0,
        is_main=True,
        is_deleted=False
    )
    db.add(product_image)
    
    db.commit()
    db.refresh(product)
    
    # Index in Elasticsearch
    await index_product(product.id, db)
    
    # Get thumbnail URL for response
    thumbnail_url = get_image_url_with_transformation(
        image_url,
        width=200,
        crop="limit",
        quality="auto"
    )
    
    # Get min price
    min_price = min([v.price for v in created_variants])
    
    # Get all images with sizes (main image first)
    images_response = get_product_images_with_sizes(product.id, db)
    
    # Get all variants for the product
    variants = db.query(ProductVariant).filter(
        ProductVariant.product_id == product.id,
        ProductVariant.is_deleted == False
    ).all()
    
    variants_response = [VariantResponse.model_validate(v) for v in variants]
    
    # Build response
    product_dict = {
        "id": product.id,
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "description": product.description,
        "is_deleted": product.is_deleted,
        "status": product.status,
        "thumbnail_url": thumbnail_url,
        "min_price": min_price,
        "images": images_response,
        "variants": variants_response,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
    
    return ProductResponse(**product_dict)


@router.get("/", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of products (excluding soft-deleted).
    Includes thumbnail images for each product.
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query non-deleted and published products only
    query = db.query(Product).filter(
        Product.is_deleted == False,
        Product.status == 'published'
    )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Get product IDs
    product_ids = [p.id for p in products]
    
    # Query main images for all products in one query
    main_images = db.query(ProductImage).filter(
        ProductImage.product_id.in_(product_ids),
        ProductImage.is_deleted == False,
        ProductImage.is_main == True
    ).all()
    
    # Create a map of product_id -> main image
    main_image_map = {img.product_id: img for img in main_images}
    
    # For products without main image, get first image ordered by order field
    products_without_main = [pid for pid in product_ids if pid not in main_image_map]
    if products_without_main:
        all_images = db.query(ProductImage).filter(
            ProductImage.product_id.in_(products_without_main),
            ProductImage.is_deleted == False
        ).order_by(ProductImage.product_id, ProductImage.order).all()
        
        # Group by product_id and take the first one for each product
        seen_products = set()
        for img in all_images:
            if img.product_id not in main_image_map and img.product_id not in seen_products:
                main_image_map[img.product_id] = img
                seen_products.add(img.product_id)
    
    # Query min prices for all products in one query
    min_prices = db.query(
        ProductVariant.product_id,
        func.min(ProductVariant.price).label('min_price')
    ).filter(
        ProductVariant.product_id.in_(product_ids),
        ProductVariant.is_deleted == False
    ).group_by(ProductVariant.product_id).all()
    
    # Create a map of product_id -> min_price
    min_price_map = {row.product_id: Decimal(str(row.min_price)) for row in min_prices}
    
    # Build response with thumbnail URLs and min prices
    product_responses = []
    for product in products:
        # Get thumbnail image
        thumbnail_url = None
        image = main_image_map.get(product.id)
        if image:
            thumbnail_url = get_image_url_with_transformation(
                image.url,
                width=200,
                crop="limit",
                quality="auto"
            )
        
        # Get min price
        min_price = min_price_map.get(product.id)
        
        # Create ProductResponse with thumbnail and min_price
        product_dict = {
            "id": product.id,
            "title": product.title,
            "brand": product.brand,
            "category": product.category,
            "description": product.description,
            "is_deleted": product.is_deleted,
            "status": product.status,
            "thumbnail_url": thumbnail_url,
            "min_price": min_price,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        }
        product_responses.append(ProductResponse(**product_dict))
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        items=product_responses,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single product by ID (excluding soft-deleted and archived).
    Includes thumbnail image if available.
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False,
        Product.status == 'published'
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Get thumbnail image
    thumbnail_url = None
    # Try to get main image first
    main_image = db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False,
        ProductImage.is_main == True
    ).first()
    
    # If no main image, get first image ordered by order field
    if not main_image:
        main_image = db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.is_deleted == False
        ).order_by(ProductImage.order).first()
    
    if main_image:
        thumbnail_url = get_image_url_with_transformation(
            main_image.url,
            width=200,
            crop="limit",
            quality="auto"
        )
    
    # Get min price from variants
    min_price_result = db.query(func.min(ProductVariant.price)).filter(
        ProductVariant.product_id == product_id,
        ProductVariant.is_deleted == False
    ).scalar()
    
    min_price = Decimal(str(min_price_result)) if min_price_result is not None else None
    
    # Get all images with sizes (main image first)
    images_response = get_product_images_with_sizes(product_id, db)
    
    # Get all variants for the product
    variants = db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id,
        ProductVariant.is_deleted == False
    ).all()
    
    variants_response = [VariantResponse.model_validate(v) for v in variants]
    
    # Create ProductResponse with thumbnail, min_price, images, and variants
    product_dict = {
        "id": product.id,
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "description": product.description,
        "is_deleted": product.is_deleted,
        "status": product.status,
        "thumbnail_url": thumbnail_url,
        "min_price": min_price,
        "images": images_response,
        "variants": variants_response,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
    
    return ProductResponse(**product_dict)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a product by ID (excluding soft-deleted).
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Update only provided fields
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Re-index in Elasticsearch (only if published)
    await index_product(product.id, db)
    
    # Get thumbnail and min_price for response
    thumbnail_url = None
    main_image = db.query(ProductImage).filter(
        ProductImage.product_id == product.id,
        ProductImage.is_deleted == False,
        ProductImage.is_main == True
    ).first()
    
    if not main_image:
        main_image = db.query(ProductImage).filter(
            ProductImage.product_id == product.id,
            ProductImage.is_deleted == False
        ).order_by(ProductImage.order).first()
    
    if main_image:
        thumbnail_url = get_image_url_with_transformation(
            main_image.url,
            width=200,
            crop="limit",
            quality="auto"
        )
    
    min_price_result = db.query(func.min(ProductVariant.price)).filter(
        ProductVariant.product_id == product.id,
        ProductVariant.is_deleted == False
    ).scalar()
    
    min_price = Decimal(str(min_price_result)) if min_price_result is not None else None
    
    # Get all images with sizes (main image first)
    images_response = get_product_images_with_sizes(product.id, db)
    
    # Get all variants for the product
    variants = db.query(ProductVariant).filter(
        ProductVariant.product_id == product.id,
        ProductVariant.is_deleted == False
    ).all()
    
    variants_response = [VariantResponse.model_validate(v) for v in variants]
    
    product_dict = {
        "id": product.id,
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "description": product.description,
        "is_deleted": product.is_deleted,
        "status": product.status,
        "thumbnail_url": thumbnail_url,
        "min_price": min_price,
        "images": images_response,
        "variants": variants_response,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
    
    return ProductResponse(**product_dict)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a product by ID.
    Sets is_deleted to True instead of actually deleting the record.
    """
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    # Soft delete
    product.is_deleted = True
    db.commit()
    
    # Delete from Elasticsearch index
    await delete_product_from_index(product_id)
    
    return None


@router.patch("/{product_id}/status", response_model=ProductResponse)
async def update_product_status(
    product_id: int,
    status_data: ProductStatusUpdate,
    db: Session = Depends(get_db)
):
    """
    Update product status (published or archived).
    - If archived: removes product from Elasticsearch
    - If published: adds product to Elasticsearch
    """
    # Validate status
    if status_data.status not in ['published', 'archived']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be either 'published' or 'archived'"
        )
    
    # Get product
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    old_status = product.status
    product.status = status_data.status
    db.commit()
    db.refresh(product)
    
    # Handle Elasticsearch based on status change
    if status_data.status == 'archived':
        # Remove from Elasticsearch
        await delete_product_from_index(product_id)
    elif status_data.status == 'published' and old_status == 'archived':
        # Add back to Elasticsearch if it was archived before
        await index_product(product_id, db)
    
    # Get thumbnail and min_price for response
    thumbnail_url = None
    main_image = db.query(ProductImage).filter(
        ProductImage.product_id == product_id,
        ProductImage.is_deleted == False,
        ProductImage.is_main == True
    ).first()
    
    if not main_image:
        main_image = db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.is_deleted == False
        ).order_by(ProductImage.order).first()
    
    if main_image:
        thumbnail_url = get_image_url_with_transformation(
            main_image.url,
            width=200,
            crop="limit",
            quality="auto"
        )
    
    min_price_result = db.query(func.min(ProductVariant.price)).filter(
        ProductVariant.product_id == product_id,
        ProductVariant.is_deleted == False
    ).scalar()
    
    min_price = Decimal(str(min_price_result)) if min_price_result is not None else None
    
    # Get all images with sizes (main image first)
    images_response = get_product_images_with_sizes(product_id, db)
    
    # Get all variants for the product
    variants = db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id,
        ProductVariant.is_deleted == False
    ).all()
    
    variants_response = [VariantResponse.model_validate(v) for v in variants]
    
    product_dict = {
        "id": product.id,
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "description": product.description,
        "is_deleted": product.is_deleted,
        "status": product.status,
        "thumbnail_url": thumbnail_url,
        "min_price": min_price,
        "images": images_response,
        "variants": variants_response,
        "created_at": product.created_at,
        "updated_at": product.updated_at
    }
    
    return ProductResponse(**product_dict)


@router.post("/{product_id}/variants", response_model=List[VariantResponse], status_code=status.HTTP_201_CREATED)
async def create_variants(
    product_id: int,
    variant_data: VariantCreateBatch,
    db: Session = Depends(get_db)
):
    """
    Create one or more variants for a product.
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
    
    # Check for duplicate SKUs in the request
    skus = [v.sku for v in variant_data.variants if v.sku]
    if len(skus) != len(set(skus)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duplicate SKUs found in the request"
        )
    
    # Check if any SKU already exists in the database
    if skus:
        existing_sku = db.query(ProductVariant).filter(
            ProductVariant.sku.in_(skus),
            ProductVariant.is_deleted == False
        ).first()
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SKU '{existing_sku.sku}' already exists"
            )
    
    # Create variants
    created_variants = []
    for variant in variant_data.variants:
        new_variant = ProductVariant(
            product_id=product_id,
            size=variant.size,
            color=variant.color,
            sku=variant.sku,
            price=variant.price,
            stock=variant.stock,
            is_deleted=False
        )
        db.add(new_variant)
        created_variants.append(new_variant)
    
    db.commit()
    
    # Refresh all created variants
    for variant in created_variants:
        db.refresh(variant)
    
    # Re-index product in Elasticsearch (variants changed)
    await index_product(product_id, db)
    
    return created_variants

