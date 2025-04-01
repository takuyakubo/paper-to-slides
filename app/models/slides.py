from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class SlideTemplate(BaseModel):
    """Slide template information."""
    id: str = Field(..., description="Unique identifier for the template")
    name: str = Field(..., description="Display name of the template")
    description: str = Field(..., description="Description of the template")
    preview_image: Optional[str] = Field(None, description="Path to preview image for the template")

class SlideRequest(BaseModel):
    """Request to generate slides from a paper."""
    paper_id: str = Field(..., description="ID of the paper to generate slides from")
    template: str = Field("academic", description="Template ID to use for slides")
    output_format: str = Field("pptx", description="Output format (pptx, pdf)")
    include_images: bool = Field(True, description="Whether to include images from the paper")
    max_slides: Optional[int] = Field(None, description="Maximum number of slides to generate")
    custom_options: Optional[Dict[str, Any]] = Field(None, description="Custom options for slide generation")

class SlideInfo(BaseModel):
    """Information about generated slides."""
    slide_id: str = Field(..., description="Unique identifier for the slides")
    paper_id: str = Field(..., description="ID of the paper the slides were generated from")
    request_time: str = Field(..., description="Time when the slides were requested")
    status: str = Field(..., description="Status of slide generation (generating, completed, error)")
    template: str = Field(..., description="Template used for the slides")
    output_format: str = Field(..., description="Output format of the slides")
    completion_time: Optional[str] = Field(None, description="Time when slide generation completed")
    output_file: Optional[str] = Field(None, description="Filename of the generated slides")
    error_message: Optional[str] = Field(None, description="Error message if generation failed")

class SlideContent(BaseModel):
    """Content for a single slide."""
    title: str = Field(..., description="Slide title")
    content: List[Dict[str, Any]] = Field(..., description="Slide content elements")
    notes: Optional[str] = Field(None, description="Speaker notes for the slide")
    layout: Optional[str] = Field(None, description="Layout type for the slide")
    
class Presentation(BaseModel):
    """Complete presentation structure."""
    title: str = Field(..., description="Presentation title")
    subtitle: Optional[str] = Field(None, description="Presentation subtitle")
    author: Optional[str] = Field(None, description="Presentation author")
    date: Optional[str] = Field(None, description="Presentation date")
    slides: List[SlideContent] = Field(..., description="Slides in the presentation")
