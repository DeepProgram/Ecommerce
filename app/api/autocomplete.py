from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List
from app.core.elasticsearch import get_es_client, PRODUCTS_INDEX
from app.schemas.autocomplete import AutocompleteResponse, AutocompleteSuggestion
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/autocomplete", tags=["autocomplete"])


@router.get("", response_model=AutocompleteResponse)
async def autocomplete(
    q: str = Query(..., min_length=1, description="Search query for autocomplete"),
    size: int = Query(10, ge=1, le=50, description="Number of suggestions to return")
):
    """
    Get autocomplete suggestions for product titles using Elasticsearch completion suggester.
    """
    if not q or not q.strip():
        return AutocompleteResponse(suggestions=[])
    
    try:
        client = await get_es_client()
        
        # Use completion suggester (ES 8.x API)
        # The suggest parameter structure remains the same in ES 8.x
        response = await client.search(
            index=PRODUCTS_INDEX,
            suggest={
                "title_suggest": {
                    "prefix": q.strip(),
                    "completion": {
                        "field": "title_suggest",
                        "size": size,
                        "skip_duplicates": True
                    }
                }
            },
            size=0  # We only want suggestions, not actual documents
        )
        
        # Extract suggestions from response
        suggestions_data = response.get("suggest", {}).get("title_suggest", [])
        
        suggestions = []
        if suggestions_data:
            # Get options from the first suggestion entry
            options = suggestions_data[0].get("options", [])
            for option in options:
                suggestions.append(
                    AutocompleteSuggestion(
                        text=option.get("text", ""),
                        score=option.get("_score", 0.0)
                    )
                )
        
        return AutocompleteResponse(suggestions=suggestions)
        
    except Exception as e:
        logger.error(f"Autocomplete error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Autocomplete failed: {str(e)}"
        )

