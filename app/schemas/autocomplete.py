from pydantic import BaseModel, Field
from typing import List


class AutocompleteSuggestion(BaseModel):
    """Schema for autocomplete suggestion"""
    text: str = Field(..., description="Suggested text")
    score: float = Field(..., description="Relevance score")


class AutocompleteResponse(BaseModel):
    """Schema for autocomplete response"""
    suggestions: List[AutocompleteSuggestion] = Field(..., description="List of suggestions")

