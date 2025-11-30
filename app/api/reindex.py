from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.elasticsearch_service import reindex_all_products
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["admin"])


class ReindexResponse(BaseModel):
    """Schema for reindex response"""
    message: str
    indexed_count: int


@router.post("/reindex", response_model=ReindexResponse, status_code=status.HTTP_200_OK)
async def reindex_products(
    db: Session = Depends(get_db)
):
    """
    Reindex all products in Elasticsearch from scratch.
    - Deletes the existing index first to avoid overlaps
    - Recreates the index with the current mapping
    - Indexes all non-deleted products
    
    **Warning:** This operation deletes all existing search data and rebuilds it.
    Use this for initial setup or when you need to completely rebuild the search index.
    """
    try:
        logger.info("Starting full reindex of all products")
        
        # Reindex all products (delete_existing=True will delete index first)
        indexed_count = await reindex_all_products(db)
        
        return ReindexResponse(
            message=f"Successfully reindexed {indexed_count} products",
            indexed_count=indexed_count
        )
        
    except Exception as e:
        logger.error(f"Reindex error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindex failed: {str(e)}"
        )

