from elasticsearch import AsyncElasticsearch
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Elasticsearch client
es_client: AsyncElasticsearch = None

# Index name
PRODUCTS_INDEX = "products"


async def get_es_client() -> AsyncElasticsearch:
    """
    Get or create Elasticsearch client.
    """
    global es_client
    if es_client is None:
        es_client = AsyncElasticsearch(
            [settings.ELASTICSEARCH_URL],
            request_timeout=30,
            max_retries=3,
            retry_on_timeout=True
        )
    return es_client


async def close_es_client():
    """
    Close Elasticsearch client connection.
    """
    global es_client
    if es_client is not None:
        await es_client.close()
        es_client = None


async def create_index_if_not_exists():
    """
    Create the products index with mapping if it doesn't exist.
    """
    client = await get_es_client()
    
    # Check if index exists
    exists = await client.indices.exists(index=PRODUCTS_INDEX)
    
    if not exists:
        # Define index mapping and settings (ES 8.x API)
        mappings = {
            "properties": {
                "id": {"type": "integer"},
                "title": {
                    "type": "text",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "description": {"type": "text"},
                "brand": {
                    "type": "keyword",
                    "fields": {
                        "text": {"type": "text"}
                    }
                },
                "category": {
                    "type": "keyword",
                    "fields": {
                        "text": {"type": "text"}
                    }
                },
                "variants": {
                    "type": "nested",
                    "properties": {
                        "id": {"type": "integer"},
                        "sku": {"type": "keyword"},
                        "price": {"type": "float"},
                        "stock": {"type": "integer"},
                        "attributes": {
                            "type": "object",
                            "dynamic": True
                        }
                    }
                },
                "images": {
                    "type": "nested",
                    "properties": {
                        "id": {"type": "integer"},
                        "url": {"type": "keyword"},
                        "alt_text": {"type": "text"},
                        "order": {"type": "integer"},
                        "is_main": {"type": "boolean"}
                    }
                },
                "main_image": {"type": "keyword"},
                "videos": {
                    "type": "nested",
                    "properties": {
                        "id": {"type": "integer"},
                        "url": {"type": "keyword"},
                        "thumbnail_url": {"type": "keyword"},
                        "duration": {"type": "float"},
                        "format": {"type": "keyword"},
                        "resolution": {"type": "keyword"},
                        "order": {"type": "integer"},
                        "is_main": {"type": "boolean"}
                    }
                },
                "main_video": {"type": "keyword"},
                "title_suggest": {
                    "type": "completion",
                    "analyzer": "simple",
                    "preserve_separators": True,
                    "preserve_position_increments": True,
                    "max_input_length": 50
                }
            }
        }
        
        settings = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "analysis": {
                "analyzer": {
                    "default": {
                        "type": "standard"
                    }
                }
            }
        }
        
        # Create index using ES 8.x API (mappings and settings as direct parameters)
        await client.indices.create(
            index=PRODUCTS_INDEX,
            mappings=mappings,
            settings=settings
        )
        logger.info(f"Created Elasticsearch index: {PRODUCTS_INDEX}")
    else:
        logger.info(f"Elasticsearch index {PRODUCTS_INDEX} already exists")

