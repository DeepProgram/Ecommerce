from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import cloudinary

from app.core.config import settings
from app.core.elasticsearch import create_index_if_not_exists, close_es_client
from app.api.products import router as products_router
from app.api.variants import router as variants_router
from app.api.images import router as images_router
from app.api.videos import router as videos_router
from app.api.search import router as search_router
from app.api.autocomplete import router as autocomplete_router
from app.api.reindex import router as reindex_router

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)

app = FastAPI(
    title="E-commerce Backend API",
    description="E-commerce backend with product management, media handling, and search",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products_router)
app.include_router(variants_router)
app.include_router(images_router)
app.include_router(videos_router)
app.include_router(search_router)
app.include_router(autocomplete_router)
app.include_router(reindex_router)


@app.on_event("startup")
async def startup_event():
    """Initialize Elasticsearch index on startup"""
    try:
        await create_index_if_not_exists()
    except Exception as e:
        print(f"Warning: Failed to initialize Elasticsearch: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Close Elasticsearch connection on shutdown"""
    await close_es_client()


@app.get("/")
async def root():
    return {"message": "E-commerce Backend API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

