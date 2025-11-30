from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from decimal import Decimal
from app.core.elasticsearch import get_es_client, PRODUCTS_INDEX
from app.schemas.search import SearchResponse, SearchProduct, Aggregations, AggregationBucket
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


def build_search_query(
    q: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    color: Optional[str] = None,
    size: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock_only: bool = False
) -> dict:
    """
    Build Elasticsearch query with filters and full-text search.
    """
    must_clauses = []
    filter_clauses = []
    
    # Full-text search (multi_match with title boosting and fuzzy)
    if q:
        must_clauses.append({
            "multi_match": {
                "query": q,
                "fields": ["title^3", "description"],  # Boost title 3x
                "fuzziness": "AUTO",
                "operator": "or"
            }
        })
    
    # Brand filter
    if brand:
        filter_clauses.append({
            "term": {"brand": brand}
        })
    
    # Category filter
    if category:
        filter_clauses.append({
            "term": {"category": category}
        })
    
    # Color filter (nested in variants)
    if color:
        filter_clauses.append({
            "nested": {
                "path": "variants",
                "query": {
                    "term": {"variants.color": color}
                }
            }
        })
    
    # Size filter (nested in variants)
    if size:
        filter_clauses.append({
            "nested": {
                "path": "variants",
                "query": {
                    "term": {"variants.size": size}
                }
            }
        })
    
    # Price range filter (nested in variants)
    if min_price is not None or max_price is not None:
        price_range = {}
        if min_price is not None:
            price_range["gte"] = float(min_price)
        if max_price is not None:
            price_range["lte"] = float(max_price)
        
        filter_clauses.append({
            "nested": {
                "path": "variants",
                "query": {
                    "range": {
                        "variants.price": price_range
                    }
                }
            }
        })
    
    # In-stock filter (nested in variants)
    if in_stock_only:
        filter_clauses.append({
            "nested": {
                "path": "variants",
                "query": {
                    "range": {
                        "variants.stock": {"gt": 0}
                    }
                }
            }
        })
    
    # Build query
    query = {}
    if must_clauses or filter_clauses:
        bool_query = {}
        if must_clauses:
            bool_query["must"] = must_clauses
        if filter_clauses:
            bool_query["filter"] = filter_clauses
        query = {"bool": bool_query}
    else:
        # Match all if no search criteria
        query = {"match_all": {}}
    
    return query


def build_aggregations() -> dict:
    """
    Build aggregations for facets (brands, categories, colors).
    """
    return {
        "brands": {
            "terms": {
                "field": "brand",
                "size": 100
            }
        },
        "categories": {
            "terms": {
                "field": "category",
                "size": 100
            }
        },
        "colors": {
            "nested": {
                "path": "variants"
            },
            "aggs": {
                "color_terms": {
                    "terms": {
                        "field": "variants.color",
                        "size": 100
                    }
                }
            }
        }
    }


@router.get("", response_model=SearchResponse)
async def search_products(
    q: Optional[str] = Query(None, description="Search query text"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    category: Optional[str] = Query(None, description="Filter by category"),
    color: Optional[str] = Query(None, description="Filter by color"),
    size: Optional[str] = Query(None, description="Filter by size"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price"),
    in_stock_only: bool = Query(False, description="Filter to only in-stock items"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    """
    Search products with full-text search, filters, and aggregations.
    """
    try:
        client = await get_es_client()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query
        query = build_search_query(
            q=q,
            brand=brand,
            category=category,
            color=color,
            size=size,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only
        )
        
        # Build aggregations
        aggregations = build_aggregations()
        
        # Execute search (ES 8.x API - query, aggs, from, size, _source as direct parameters)
        response = await client.search(
            index=PRODUCTS_INDEX,
            query=query,
            aggs=aggregations,
            from_=offset,
            size=page_size,
            _source=[
                "id", "title", "description", "brand", "category",
                "main_image", "main_video", "variants"
            ]
        )
        
        # Extract results
        hits = response.get("hits", {})
        total = hits.get("total", {}).get("value", 0)
        products_data = hits.get("hits", [])
        
        # Process products
        products = []
        for hit in products_data:
            source = hit.get("_source", {})
            variants = source.get("variants", [])
            
            # Calculate min/max price and in_stock status from variants
            prices = [float(v.get("price", 0)) for v in variants if v.get("price")]
            in_stock = any(v.get("stock", 0) > 0 for v in variants)
            
            min_price_val = Decimal(str(min(prices))) if prices else None
            max_price_val = Decimal(str(max(prices))) if prices else None
            
            product = SearchProduct(
                id=source.get("id"),
                title=source.get("title", ""),
                description=source.get("description"),
                brand=source.get("brand"),
                category=source.get("category"),
                main_image=source.get("main_image"),
                main_video=source.get("main_video"),
                min_price=min_price_val,
                max_price=max_price_val,
                in_stock=in_stock
            )
            products.append(product)
        
        # Process aggregations
        aggs = response.get("aggregations", {})
        
        # Brands aggregation
        brands_buckets = aggs.get("brands", {}).get("buckets", [])
        brands = [
            AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
            for bucket in brands_buckets
        ]
        
        # Categories aggregation
        categories_buckets = aggs.get("categories", {}).get("buckets", [])
        categories = [
            AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
            for bucket in categories_buckets
        ]
        
        # Colors aggregation (nested)
        colors_agg = aggs.get("colors", {})
        colors_buckets = colors_agg.get("color_terms", {}).get("buckets", [])
        colors = [
            AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
            for bucket in colors_buckets
        ]
        
        # Calculate total pages
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return SearchResponse(
            products=products,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            aggregations=Aggregations(
                brands=brands,
                categories=categories,
                colors=colors
            )
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

