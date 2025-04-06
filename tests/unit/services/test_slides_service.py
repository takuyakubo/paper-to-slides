import os
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import tempfile
from pathlib import Path

from app.services import slides_service

class TestSlidesService:
    """¹é¤ÉµüÓ¹nÆ¹È¯é¹"""
    
    @pytest.fixture
    def mock_slide_content(self):
        """âÃ¯¹é¤É³óÆóÄ’Ğ›Y‹Õ£¯¹Áã"""
        return [
            {
                "title": "Test Paper Title",
                "content": ["Academic Paper Presentation"],
                "notes": "Introduction to the paper",
                "layout": "title"
            },
            {
                "title": "Introduction",
                "content": ["Background", "Research Gap", "Objectives"],
                "notes": "Explain the context",
                "layout": "content"
            }
        ]
    
    @pytest.fixture
    def mock_paper_content(self):
        """âÃ¯nÖ‡³óÆóÄ’Ğ›Y‹Õ£¯¹Áã"""
        return {
            "paper_id": "test123",
            "text": "Test Paper Title\n\nAbstract: This is a test abstract.\n\n1. Introduction\nThis is the introduction section.\n\n2. Methods\nThis is the methods section.\n\n3. Results\nThese are the results.\n\n4. Conclusion\nThis is the conclusion.",
            "sections": [
                {"heading": "Introduction", "content": "This is the introduction section."},
                {"heading": "Methods", "content": "This is the methods section."},
                {"heading": "Results", "content": "These are the results."},
                {"heading": "Conclusion", "content": "This is the conclusion."}
            ],
            "images": ["image1.png", "image2.png"]
        }
    
    @pytest.mark.asyncio
    async def test_generate_presentation(self, monkeypatch, mock_slide_content, mock_paper_content, tmp_path):
        """×ì¼óÆü·çó_ınÆ¹È"""
        # generate_slide_content’âÃ¯
        mock_generate = AsyncMock(return_value=mock_slide_content)
        monkeypatch.setattr("app.services.slides_service.generate_slide_content", mock_generate)
        
        # mock Presentation class
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
        
        # mock Presentation class
        monkeypatch.setattr("app.services.slides_service.Presentation", MagicMock(return_value=mock_presentation))
        
        # Æ¹È
        output_dir = str(tmp_path)
        result = await slides_service.generate_presentation(
            paper_content=mock_paper_content,
            output_dir=output_dir,
            template="academic",
            output_format="pptx",
            include_images=True
        )
        
        # ¢µü·çó
        assert result == "presentation.pptx"
        mock_generate.assert_called_once()
        mock_presentation.save.assert_called_once()
        # ¹é¤Éı LcWDŞp|pŒ_Kº (¹é¤Ép + ;Ï¹é¤É)
        assert mock_presentation.slides.add_slide.call_count == len(mock_slide_content) + 1
    
    def test_apply_template_styling(self, monkeypatch):
        """Æó×ìüÈ¹¿¤ëni(_ınÆ¹È"""
        # âÃ¯n»ÃÈ¢Ã×
        mock_presentation = MagicMock()
        mock_slide = MagicMock()
        mock_title_shape = MagicMock()
        mock_title_frame = MagicMock()
        mock_paragraph = MagicMock()
        
        mock_presentation.slides = [mock_slide]
        mock_slide.shapes.title = mock_title_shape
        mock_title_shape.text_frame = mock_title_frame
        mock_title_frame.paragraphs = [mock_paragraph]
        
        # ı n·§¤×’-š
        mock_shape = MagicMock()
        mock_shape.text_frame = MagicMock()
        mock_shape.text_frame.paragraphs = [MagicMock()]
        mock_slide.shapes = [mock_title_shape, mock_shape]
        
        # Æ¹È
        slides_service.apply_template_styling(mock_presentation, "academic")
        
        # ¢µü·çó
        assert mock_presentation.slide_width is not None
        assert mock_presentation.slide_height is not None
        # Æó×ìüÈn-šLi(UŒfD‹K
        assert mock_paragraph.font.name is not None
        assert mock_paragraph.font.size is not None
    
    def test_extract_text_for_slides(self, mock_paper_content):
        """¹é¤É(Æ­¹È½ú_ınÆ¹È"""
        # Æ¹È
        result = slides_service.extract_text_for_slides(mock_paper_content)
        
        # ¢µü·çó
        assert result["title"] == "Test Paper Title"
        assert "introduction" in result
        assert result["introduction"] == "This is the introduction section."
        assert result["methodology"] == "This is the methods section."
        assert result["results"] == "These are the results."
        assert result["conclusion"] == "This is the conclusion."
    
    def test_extract_text_for_slides_fallback(self, monkeypatch):
        """»¯·çóL!D4nÆ­¹È½úÕ©üëĞÃ¯nÆ¹È"""
        # »¯·çójWnÖ‡³óÆóÄ
        paper_content = {
            "text": "Test Paper Title\n\nAbstract: This is a test abstract.\n\nIntroduction: This is introduction content.\n\nMethodology: This is methodology content.\n\nResults: These are the results.\n\nConclusion: This is the conclusion."
        }
        
        # Æ¹È
        result = slides_service.extract_text_for_slides(paper_content)
        
        # ¢µü·çó
        assert result["title"] == "Test Paper Title"
        assert "abstract" in result
        assert "This is a test abstract" in result["abstract"]
        assert "introduction" in result
        assert "This is introduction content" in result["introduction"]
