from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal


class SearchRequest(BaseModel):
    """Schema for search request query parameters"""
    q: Optional[str] = Field(None, description="Search query text")
    brand: Optional[str] = Field(None, description="Filter by brand")
    category: Optional[str] = Field(None, description="Filter by category")
    color: Optional[str] = Field(None, description="Filter by color")
    size: Optional[str] = Field(None, description="Filter by size")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price")
    in_stock_only: Optional[bool] = Field(False, description="Filter to only in-stock items")
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(10, ge=1, le=100, description="Items per page")


class SearchProduct(BaseModel):
    """Schema for product in search results"""
    id: int
    title: str
    description: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    main_image: Optional[str]
    main_video: Optional[str]
    min_price: Optional[Decimal]
    max_price: Optional[Decimal]
    in_stock: bool


class AggregationBucket(BaseModel):
    """Schema for aggregation bucket"""
    key: str
    doc_count: int


class Aggregations(BaseModel):
    """Schema for search aggregations"""
    brands: List[AggregationBucket]
    categories: List[AggregationBucket]
    colors: List[AggregationBucket]


class SearchResponse(BaseModel):
    """Schema for search response"""
    products: List[SearchProduct]
    total: int
    page: int
    page_size: int
    total_pages: int
    aggregations: Aggregations

