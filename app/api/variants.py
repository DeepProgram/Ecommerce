from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.variant import ProductVariant
from app.models.variant_attribute import VariantAttribute
from app.models.variant_attribute_type import VariantAttributeType
from app.schemas.variant import (
    VariantUpdate,
    VariantStockUpdate,
    VariantResponse
)
from app.schemas.variant_attribute import VariantAttributeResponse
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
    
    # Update only provided fields (excluding attributes)
    update_data = variant_data.model_dump(exclude_unset=True, exclude={"attributes"})
    for field, value in update_data.items():
        setattr(variant, field, value)
    
    # Handle dynamic attributes if provided
    if variant_data.attributes is not None:
        # Delete existing attributes (soft delete)
        existing_attrs = variant.attributes.filter(VariantAttribute.is_deleted == False).all()
        for attr in existing_attrs:
            attr.is_deleted = True
        
        # Create new attributes
        for attribute_type_id, value in variant_data.attributes.items():
            # Verify attribute type exists
            attr_type = db.query(VariantAttributeType).filter(
                VariantAttributeType.id == attribute_type_id,
                VariantAttributeType.is_deleted == False,
                VariantAttributeType.is_active == True
            ).first()
            
            if not attr_type:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Attribute type with id {attribute_type_id} not found or inactive"
                )
            
            attr = VariantAttribute(
                variant_id=variant.id,
                attribute_type_id=attribute_type_id,
                value=str(value),
                is_deleted=False
            )
            db.add(attr)
    
    db.commit()
    db.refresh(variant)
    
    # Build response with attributes
    variant_dict = {
        "id": variant.id,
        "product_id": variant.product_id,
        "sku": variant.sku,
        "price": variant.price,
        "stock": variant.stock,
        "is_deleted": variant.is_deleted,
        "created_at": variant.created_at,
        "updated_at": variant.updated_at,
        "attributes": {},
        "attribute_objects": []
    }
    
    # Load attributes
    attributes = variant.attributes.filter(VariantAttribute.is_deleted == False).all()
    for attr in attributes:
        variant_dict["attributes"][attr.attribute_type_id] = attr.value
        variant_dict["attribute_objects"].append(VariantAttributeResponse(
            id=attr.id,
            variant_id=attr.variant_id,
            attribute_type_id=attr.attribute_type_id,
            value=attr.value,
            is_deleted=attr.is_deleted,
            created_at=attr.created_at,
            updated_at=attr.updated_at,
            attribute_type_name=attr.attribute_type.name if attr.attribute_type else None,
            attribute_type_display_name=attr.attribute_type.display_name if attr.attribute_type else None
        ))
    
    # Re-index product in Elasticsearch (variant changed)
    await index_product(variant.product_id, db)
    
    return VariantResponse(**variant_dict)


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

