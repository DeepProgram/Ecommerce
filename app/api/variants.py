from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.variant import ProductVariant
from app.schemas.variant import (
    VariantUpdate,
    VariantStockUpdate,
    VariantResponse
)
from app.services.elasticsearch_service import index_product

router = APIRouter(prefix="/variants", tags=["variants"])


@router.patch("/{variant_id}", response_model=VariantResponse)
async def update_variant(
    variant_id: int,
    variant_data: VariantUpdate,
    db: Session = Depends(get_db)
):
    """
    Update variant data (color, size, price, etc.).
    """
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.is_deleted == False
    ).first()
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id {variant_id} not found"
        )
    
    # Check if SKU is being updated and if it conflicts with existing SKU
    if variant_data.sku and variant_data.sku != variant.sku:
        existing_sku = db.query(ProductVariant).filter(
            ProductVariant.sku == variant_data.sku,
            ProductVariant.id != variant_id,
            ProductVariant.is_deleted == False
        ).first()
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SKU '{variant_data.sku}' already exists"
            )
    
    # Update only provided fields
    update_data = variant_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(variant, field, value)
    
    db.commit()
    db.refresh(variant)
    
    # Re-index product in Elasticsearch (variant changed)
    await index_product(variant.product_id, db)
    
    return variant


@router.patch("/{variant_id}/stock", response_model=VariantResponse)
async def update_variant_stock(
    variant_id: int,
    stock_data: VariantStockUpdate,
    db: Session = Depends(get_db)
):
    """
    Safely update stock counts for a variant.
    """
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.is_deleted == False
    ).first()
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id {variant_id} not found"
        )
    
    variant.stock = stock_data.stock
    db.commit()
    db.refresh(variant)
    
    # Re-index product in Elasticsearch (stock changed)
    await index_product(variant.product_id, db)
    
    return variant


@router.delete("/{variant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant(
    variant_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a variant by ID.
    Sets is_deleted to True instead of actually deleting the record.
    """
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.is_deleted == False
    ).first()
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Variant with id {variant_id} not found"
        )
    
    # Store product_id before soft delete
    product_id = variant.product_id
    
    # Soft delete
    variant.is_deleted = True
    db.commit()
    
    # Re-index product in Elasticsearch (variant deleted)
    await index_product(product_id, db)
    
    return None

