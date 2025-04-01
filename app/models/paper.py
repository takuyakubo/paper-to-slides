from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class PaperMetadata(BaseModel):
    """Metadata about a paper extracted from the PDF."""
    title: str = Field(..., description="Title of the paper")
    author: str = Field(..., description="Author(s) of the paper")
    subject: Optional[str] = Field(None, description="Subject or category of the paper")
    keywords: Optional[str] = Field(None, description="Keywords associated with the paper")
    page_count: int = Field(..., description="Number of pages in the paper")

class PaperSection(BaseModel):
    """Section of a paper with heading and content."""
    heading: str = Field(..., description="Section heading")
    level: int = Field(..., description="Heading level (1 for main headings, 2 for subheadings, etc.)")
    content: str = Field(..., description="Section content")
    start_page: Optional[int] = Field(None, description="Page number where section starts")

class PaperImage(BaseModel):
    """Image extracted from a paper."""
    path: str = Field(..., description="Path to the image file")
    page: Optional[int] = Field(None, description="Page number where the image appears")
    caption: Optional[str] = Field(None, description="Caption of the image, if available")

class PaperContent(BaseModel):
    """Content extracted from a paper."""
    paper_id: str = Field(..., description="Unique identifier for the paper")
    text: str = Field(..., description="Full text content of the paper")
    sections: List[PaperSection] = Field(default_factory=list, description="Sections of the paper")
    images: List[str] = Field(default_factory=list, description="Paths to images extracted from the paper")
    tables: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="Tables extracted from the paper")
    references: Optional[List[str]] = Field(default_factory=list, description="References cited in the paper")

class PaperInfo(BaseModel):
    """Information about an uploaded paper."""
    paper_id: str = Field(..., description="Unique identifier for the paper")
    filename: str = Field(..., description="Original filename of the uploaded PDF")
    upload_time: str = Field(..., description="Time when the paper was uploaded")
    status: str = Field(..., description="Processing status (processing, processed, error)")
    title: Optional[str] = Field(None, description="Title of the paper, if extracted")
    author: Optional[str] = Field(None, description="Author(s) of the paper, if extracted")
    subject: Optional[str] = Field(None, description="Subject or category, if extracted")
    keywords: Optional[str] = Field(None, description="Keywords, if extracted")
    page_count: Optional[int] = Field(None, description="Number of pages in the PDF")
    error_message: Optional[str] = Field(None, description="Error message if processing failed")
