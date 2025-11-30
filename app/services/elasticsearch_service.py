"""
Elasticsearch service for indexing and searching products.
"""
from sqlalchemy.orm import Session
from typing import Optional
from app.core.elasticsearch import get_es_client, PRODUCTS_INDEX
from app.models.product import Product
from app.models.variant import ProductVariant
from app.models.image import ProductImage
from app.models.video import ProductVideo
import logging

logger = logging.getLogger(__name__)


async def build_product_document(product: Product) -> dict:
    """
    Build Elasticsearch document from Product model.
    
    Args:
        product: Product SQLAlchemy model instance
    
    Returns:
        Dictionary representing the product document for Elasticsearch
    """
    # Get variants (non-deleted)
    variants = product.variants.filter(ProductVariant.is_deleted == False).all()
    variant_data = [
        {
            "id": v.id,
            "size": v.size,
            "color": v.color,
            "sku": v.sku,
            "price": float(v.price) if v.price else None,
            "stock": v.stock
        }
        for v in variants
    ]
    
    # Get images (non-deleted, ordered)
    images = product.images.filter(ProductImage.is_deleted == False).order_by(ProductImage.order).all()
    image_data = [
        {
            "id": img.id,
            "url": img.url,
            "alt_text": img.alt_text,
            "order": img.order,
            "is_main": img.is_main
        }
        for img in images
    ]
    
    # Get main image URL
    main_image = None
    main_image_obj = product.images.filter(
        ProductImage.is_deleted == False,
        ProductImage.is_main == True
    ).first()
    if main_image_obj:
        main_image = main_image_obj.url
    
    # Get videos (non-deleted, ordered)
    videos = product.videos.filter(ProductVideo.is_deleted == False).order_by(ProductVideo.order).all()
    video_data = [
        {
            "id": vid.id,
            "url": vid.url,
            "thumbnail_url": vid.thumbnail_url,
            "duration": float(vid.duration) if vid.duration else None,
            "format": vid.format,
            "resolution": vid.resolution,
            "order": vid.order,
            "is_main": vid.is_main
        }
        for vid in videos
    ]
    
    # Get main video URL
    main_video = None
    main_video_obj = product.videos.filter(
        ProductVideo.is_deleted == False,
        ProductVideo.is_main == True
    ).first()
    if main_video_obj:
        main_video = main_video_obj.url
    
    # Build document
    document = {
        "id": product.id,
        "title": product.title,
        "description": product.description or "",
        "brand": product.brand,
        "category": product.category,
        "variants": variant_data,
        "images": image_data,
        "main_image": main_image,
        "videos": video_data,
        "main_video": main_video,
        "title_suggest": {
            "input": product.title.split(),
            "weight": 1
        }
    }
    
    return document


async def index_product(product_id: int, db: Session) -> bool:
    """
    Index a product in Elasticsearch.
    
    Args:
        product_id: Product ID to index
        db: Database session
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get product with relationships
        product = db.query(Product).filter(
            Product.id == product_id,
            Product.is_deleted == False
        ).first()
        
        if not product:
            logger.warning(f"Product {product_id} not found or deleted, skipping indexing")
            return False
        
        # Build document
        document = await build_product_document(product)
        
        # Get ES client
        client = await get_es_client()
        
        # Index document
        await client.index(
            index=PRODUCTS_INDEX,
            id=str(product_id),
            document=document
        )
        
        logger.info(f"Indexed product {product_id} in Elasticsearch")
        return True
        
    except Exception as e:
        logger.error(f"Failed to index product {product_id}: {str(e)}")
        return False


async def delete_product_from_index(product_id: int) -> bool:
    """
    Delete a product from Elasticsearch index.
    
    Args:
        product_id: Product ID to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_es_client()
        
        # Delete document
        result = await client.delete(
            index=PRODUCTS_INDEX,
            id=str(product_id),
            ignore=[404]  # Ignore if document doesn't exist
        )
        
        logger.info(f"Deleted product {product_id} from Elasticsearch index")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete product {product_id} from index: {str(e)}")
        return False


async def delete_index() -> bool:
    """
    Delete the entire products index from Elasticsearch.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        client = await get_es_client()
        
        # Check if index exists
        exists = await client.indices.exists(index=PRODUCTS_INDEX)
        
        if exists:
            # Delete index
            await client.indices.delete(index=PRODUCTS_INDEX)
            logger.info(f"Deleted Elasticsearch index: {PRODUCTS_INDEX}")
        else:
            logger.info(f"Index {PRODUCTS_INDEX} does not exist, nothing to delete")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete index: {str(e)}")
        return False


async def reindex_all_products(db: Session, delete_existing: bool = False) -> int:
    """
    Reindex all products in Elasticsearch.
    Useful for initial setup or after schema changes.
    
    Args:
        db: Database session
        delete_existing: If True, delete the index first before reindexing
    
    Returns:
        Number of products indexed
    """
    # Delete index if requested
    if delete_existing:
        await delete_index()
        # Recreate index
        from app.core.elasticsearch import create_index_if_not_exists
        await create_index_if_not_exists()
    
    products = db.query(Product).filter(Product.is_deleted == False).all()
    
    indexed_count = 0
    for product in products:
        success = await index_product(product.id, db)
        if success:
            indexed_count += 1
    
    logger.info(f"Reindexed {indexed_count} products in Elasticsearch")
    return indexed_count

