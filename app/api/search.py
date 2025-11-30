from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Optional, List, Dict
from decimal import Decimal
from sqlalchemy.orm import Session
from app.core.elasticsearch import get_es_client, PRODUCTS_INDEX
from app.core.database import get_db
from app.models.variant_attribute_type import VariantAttributeType
from app.schemas.search import SearchResponse, SearchProduct, Aggregations, AggregationBucket
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


def build_search_query(
    q: Optional[str] = None,
    brand: Optional[str] = None,
    category: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    in_stock_only: bool = False,
    attribute_filters: Optional[Dict[str, str]] = None
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
    
    # Dynamic attribute filters (nested in variants.attributes)
    if attribute_filters:
        for attr_name, attr_value in attribute_filters.items():
            filter_clauses.append({
                "nested": {
                    "path": "variants",
                    "query": {
                        "term": {f"variants.attributes.{attr_name}": attr_value}
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


async def build_aggregations(db: Session) -> dict:
    """
    Build aggregations for facets (brands, categories, and all active attribute types).
    """
    aggs = {
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
        }
    }
    
    # Get all active attribute types and build aggregations for each
    attribute_types = db.query(VariantAttributeType).filter(
        VariantAttributeType.is_deleted == False,
        VariantAttributeType.is_active == True
    ).order_by(VariantAttributeType.sort_order, VariantAttributeType.name).all()
    
    for attr_type in attribute_types:
        aggs[f"attr_{attr_type.name}"] = {
            "nested": {
                "path": "variants"
            },
            "aggs": {
                f"{attr_type.name}_terms": {
                    "terms": {
                        "field": f"variants.attributes.{attr_type.name}",
                        "size": 100
                    }
                }
            }
        }
    
    return aggs


@router.get("", response_model=SearchResponse)
async def search_products(
    request: Request,
    q: Optional[str] = Query(None, description="Search query text"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price"),
    in_stock_only: bool = Query(False, description="Filter to only in-stock items"),
    # Dynamic attribute filters: pass as JSON string or individual query params
    # Option 1: ?attributes={"color":"red","size":"M"} (URL encoded)
    # Option 2: ?attr_color=red&attr_size=M (using attr_ prefix)
    attributes_json: Optional[str] = Query(None, alias="attributes", description="Dynamic attribute filters as JSON string: {\"color\":\"red\",\"size\":\"M\"}"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """
    Search products with full-text search, filters, and aggregations.
    
    Dynamic attribute filters can be passed in two ways:
    1. As JSON string: ?attributes={"color":"red","size":"M"}
    2. As individual params: ?attr_color=red&attr_size=M
    """
    try:
        # Parse dynamic attribute filters
        attribute_filters = {}
        
        # Option 1: Parse from JSON string
        if attributes_json:
            try:
                attribute_filters = json.loads(attributes_json)
                if not isinstance(attribute_filters, dict):
                    raise ValueError("Attributes must be a JSON object")
            except (json.JSONDecodeError, ValueError) as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid attributes JSON: {str(e)}"
                )
        
        # Option 2: Parse from individual query params with attr_ prefix
        query_params = dict(request.query_params)
        for key, value in query_params.items():
            if key.startswith("attr_") and key != "attributes":
                attr_name = key[5:]  # Remove "attr_" prefix
                attribute_filters[attr_name] = value
        
        client = await get_es_client()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query
        query = build_search_query(
            q=q,
            brand=brand,
            category=category,
            min_price=min_price,
            max_price=max_price,
            in_stock_only=in_stock_only,
            attribute_filters=attribute_filters if attribute_filters else None
        )
        
        # Build aggregations (dynamic based on active attribute types)
        aggregations = await build_aggregations(db)
        
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
        
        # Dynamic attribute aggregations
        attribute_aggregations = {}
        attribute_types = db.query(VariantAttributeType).filter(
            VariantAttributeType.is_deleted == False,
            VariantAttributeType.is_active == True
        ).all()
        
        for attr_type in attribute_types:
            attr_agg_key = f"attr_{attr_type.name}"
            attr_agg = aggs.get(attr_agg_key, {})
            attr_buckets = attr_agg.get(f"{attr_type.name}_terms", {}).get("buckets", [])
            attribute_aggregations[attr_type.name] = [
                AggregationBucket(key=bucket["key"], doc_count=bucket["doc_count"])
                for bucket in attr_buckets
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
                attributes=attribute_aggregations
            )
        )
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )

