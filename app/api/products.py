from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.models.product import Product
from app.models.variant import ProductVariant
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse
)
from app.schemas.variant import VariantCreateBatch, VariantResponse
from app.services.elasticsearch_service import index_product, delete_product_from_index

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new product.
    """
    # Create product instance
    product = Product(
        title=product_data.title,
        brand=product_data.brand,
        category=product_data.category,
        description=product_data.description,
        is_deleted=False
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Index in Elasticsearch
    await index_product(product.id, db)
    
    return product


@router.get("/", response_model=ProductListResponse)
async def get_products(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of products (excluding soft-deleted).
    """
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Query non-deleted products
    query = db.query(Product).filter(Product.is_deleted == False)
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    products = query.order_by(Product.created_at.desc()).offset(offset).limit(page_size).all()
    
    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size
    
    return ProductListResponse(
        items=products,
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
    Get a single product by ID (excluding soft-deleted).
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
    
    return product


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
    
    # Re-index in Elasticsearch
    await index_product(product.id, db)
    
    return product


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

