from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.variant_attribute_type import VariantAttributeType
from app.schemas.variant_attribute_type import (
    VariantAttributeTypeCreate,
    VariantAttributeTypeUpdate,
    VariantAttributeTypeResponse
)

router = APIRouter(prefix="/variant-attribute-types", tags=["variant-attribute-types"])


@router.post("/", response_model=VariantAttributeTypeResponse, status_code=status.HTTP_201_CREATED)
async def create_variant_attribute_type(
    attribute_type_data: VariantAttributeTypeCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new variant attribute type (e.g., size, color, material).
    """
    # Check if name already exists
    existing = db.query(VariantAttributeType).filter(
        VariantAttributeType.name == attribute_type_data.name,
        VariantAttributeType.is_deleted == False
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Attribute type with name '{attribute_type_data.name}' already exists"
        )
    
    attribute_type = VariantAttributeType(
        name=attribute_type_data.name,
        data_type=attribute_type_data.data_type,
        display_name=attribute_type_data.display_name,
        sort_order=attribute_type_data.sort_order,
        is_active=attribute_type_data.is_active,
        is_deleted=False
    )
    
    db.add(attribute_type)
    db.commit()
    db.refresh(attribute_type)
    
    return attribute_type


@router.get("/", response_model=List[VariantAttributeTypeResponse])
async def get_variant_attribute_types(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get list of variant attribute types.
    """
    query = db.query(VariantAttributeType).filter(VariantAttributeType.is_deleted == False)
    
    if is_active is not None:
        query = query.filter(VariantAttributeType.is_active == is_active)
    
    attribute_types = query.order_by(VariantAttributeType.sort_order, VariantAttributeType.name).all()
    return attribute_types


@router.get("/{attribute_type_id}", response_model=VariantAttributeTypeResponse)
async def get_variant_attribute_type(
    attribute_type_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single variant attribute type by ID.
    """
    attribute_type = db.query(VariantAttributeType).filter(
        VariantAttributeType.id == attribute_type_id,
        VariantAttributeType.is_deleted == False
    ).first()
    
    if not attribute_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attribute type with id {attribute_type_id} not found"
        )
    
    return attribute_type


@router.put("/{attribute_type_id}", response_model=VariantAttributeTypeResponse)
async def update_variant_attribute_type(
    attribute_type_id: int,
    attribute_type_data: VariantAttributeTypeUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a variant attribute type.
    """
    attribute_type = db.query(VariantAttributeType).filter(
        VariantAttributeType.id == attribute_type_id,
        VariantAttributeType.is_deleted == False
    ).first()
    
    if not attribute_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attribute type with id {attribute_type_id} not found"
        )
    
    # Update only provided fields
    update_data = attribute_type_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attribute_type, field, value)
    
    db.commit()
    db.refresh(attribute_type)
    
    return attribute_type


@router.delete("/{attribute_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_variant_attribute_type(
    attribute_type_id: int,
    db: Session = Depends(get_db)
):
    """
    Soft delete a variant attribute type.
    """
    attribute_type = db.query(VariantAttributeType).filter(
        VariantAttributeType.id == attribute_type_id,
        VariantAttributeType.is_deleted == False
    ).first()
    
    if not attribute_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attribute type with id {attribute_type_id} not found"
        )
    
    # Soft delete
    attribute_type.is_deleted = True
    db.commit()
    
    return None

