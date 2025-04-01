from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class SummaryRequest(BaseModel):
    """Request to generate a paper summary."""
    paper_id: str = Field(..., description="ID of the paper to summarize")
    max_length: Optional[int] = Field(500, description="Maximum length of the summary in words")
    style: Optional[str] = Field("academic", description="Style of the summary (academic, simple, bullet_points)")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on in the summary")

class SummaryResponse(BaseModel):
    """Response containing a paper summary."""
    paper_id: str = Field(..., description="ID of the paper that was summarized")
    summary: str = Field(..., description="Generated summary text")
    focus_areas: Optional[List[str]] = Field(None, description="Areas that were focused on")
    style: str = Field(..., description="Style of the summary")

class KeyPoint(BaseModel):
    """A key point extracted from a paper."""
    content: str = Field(..., description="Content of the key point")
    category: Optional[str] = Field(None, description="Category of the key point")
    importance: Optional[int] = Field(None, description="Importance score (1-10)")
    source_section: Optional[str] = Field(None, description="Section from which this was extracted")

class KeyPointsRequest(BaseModel):
    """Request to extract key points from a paper."""
    paper_id: str = Field(..., description="ID of the paper to extract key points from")
    num_points: Optional[int] = Field(5, description="Number of key points to extract")
    categories: Optional[List[str]] = Field(None, description="Categories of key points to extract")

class KeyPointsResponse(BaseModel):
    """Response containing key points extracted from a paper."""
    paper_id: str = Field(..., description="ID of the paper from which key points were extracted")
    key_points: List[KeyPoint] = Field(..., description="Extracted key points")
    categories: Optional[List[str]] = Field(None, description="Categories that were included")

class PromptTemplate(BaseModel):
    """Template for prompting an LLM."""
    id: str = Field(..., description="Unique identifier for the prompt template")
    name: str = Field(..., description="Display name of the prompt template")
    description: str = Field(..., description="Description of what the prompt template does")
    prompt_text: str = Field(..., description="Template text with placeholders")
    default_params: Dict[str, Any] = Field(default_factory=dict, description="Default parameter values")

class LLMConfig(BaseModel):
    """Configuration for an LLM provider."""
    provider: str = Field(..., description="LLM provider (openai, anthropic)")
    model: str = Field(..., description="Model name to use")
    temperature: float = Field(0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    top_p: Optional[float] = Field(None, description="Top-p sampling parameter")
    api_key: Optional[str] = Field(None, description="API key (normally from environment)")
    other_params: Optional[Dict[str, Any]] = Field(None, description="Other provider-specific parameters")
