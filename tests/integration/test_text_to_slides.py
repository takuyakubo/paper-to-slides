import os
import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.services.llm_service import generate_slide_content
from app.services.slides_service import generate_presentation

@pytest.fixture
def sample_paper_content():
    """Æ¹È(nÖ‡³óÆóÄ’Ğ›Y‹Õ£¯¹Áã"""
    return {
        "paper_id": "test123",
        "text": """
        Title: Test Paper
        
        Abstract: This is a test paper abstract for testing purposes.
        
        1. Introduction
        This is the introduction section of the test paper.
        
        2. Methodology
        This section describes the methodology used in the study.
        
        3. Results
        Here are the results of the study.
        
        4. Conclusion
        This is the conclusion of the test paper.
        """,
        "sections": [
            {"heading": "Introduction", "content": "This is the introduction section of the test paper."},
            {"heading": "Methodology", "content": "This section describes the methodology used in the study."},
            {"heading": "Results", "content": "Here are the results of the study."},
            {"heading": "Conclusion", "content": "This is the conclusion of the test paper."}
        ]
    }

@pytest.fixture
def sample_slide_content():
    """Æ¹È(n¹é¤É³óÆóÄ’Ğ›Y‹Õ£¯¹Áã"""
    return [
        {
            "title": "Test Paper",
            "content": ["Academic Paper Presentation"],
            "notes": "Introduction to the paper",
            "layout": "title"
        },
        {
            "title": "Introduction",
            "content": ["This is the introduction section of the test paper."],
            "notes": "Explain the context",
            "layout": "content"
        },
        {
            "title": "Methodology",
            "content": ["This section describes the methodology used in the study."],
            "notes": "Explain the methods",
            "layout": "content"
        },
        {
            "title": "Results",
            "content": ["Here are the results of the study."],
            "notes": "Discuss the results",
            "layout": "content"
        },
        {
            "title": "Conclusion",
            "content": ["This is the conclusion of the test paper."],
            "notes": "Summarize the paper",
            "layout": "content"
        }
    ]

@pytest.mark.asyncio
async def test_text_to_slides_workflow(monkeypatch, sample_paper_content, sample_slide_content, tmp_path):
    """Æ­¹È½úK‰¹é¤ÉnqÆ¹È"""
    
    # generate_slide_content’âÃ¯
    mock_generate_slide = AsyncMock(return_value=sample_slide_content)
    monkeypatch.setattr("app.services.llm_service.generate_slide_content", mock_generate_slide)
    
    # Presentation¯é¹’âÃ¯
    mock_presentation = MagicMock()
    mock_slides = MagicMock()
    mock_presentation.slides = mock_slides
    mock_presentation.slides.add_slide.return_value = MagicMock()
    
    # mock slide components
    mock_slide = mock_presentation.slides.add_slide.return_value
    mock_title = MagicMock()
    mock_slide.shapes.title = mock_title
    mock_title.text = ""
    
    # mock placeholder
    mock_placeholder = MagicMock()
    mock_slide.placeholders = {1: mock_placeholder}
    mock_content_placeholder = MagicMock()
    mock_slide.placeholders[1] = mock_content_placeholder
    
    # mock text frame
    mock_text_frame = MagicMock()
    mock_content_placeholder.text_frame = mock_text_frame
    mock_paragraph = MagicMock()
    mock_text_frame.paragraphs = [mock_paragraph]
    mock_text_frame.add_paragraph.return_value = mock_paragraph
    
    # Presentation¯é¹’âÃ¯
    monkeypatch.setattr("app.services.slides_service.Presentation", MagicMock(return_value=mock_presentation))
    
    # Æ¹ÈŸL
    # 1. ¹é¤É³óÆóÄ
    slides_content = await generate_slide_content(
        paper_content=sample_paper_content,
        max_slides=10
    )
    
    # ¢µü·çó
    assert mock_generate_slide.call_count == 1
    assert len(slides_content) == len(sample_slide_content)
    assert slides_content[0]["title"] == "Test Paper"
    
    # 2. ×ì¼óÆü·çó
    output_dir = str(tmp_path)
    result = await generate_presentation(
        paper_content=sample_paper_content,
        output_dir=output_dir,
        template="academic",
        output_format="pptx"
    )
    
    # ¢µü·çó
    assert result == "presentation.pptx"
    assert mock_presentation.save.call_count == 1
    
    # ¹é¤Éı LcWDŞp|pŒ_Kº¹é¤Ép + ;Ï¹é¤É	
    # ;ÏLjD4o;Ï¹é¤Éoı UŒjD
    if not sample_paper_content.get("images"):
        assert mock_presentation.slides.add_slide.call_count == len(sample_slide_content)
    else:
        assert mock_presentation.slides.add_slide.call_count == len(sample_slide_content) + 1
