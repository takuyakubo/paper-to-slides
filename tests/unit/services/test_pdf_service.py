import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.services import pdf_service

class TestPdfService:
    """PDFæµüÓ¹nÆ¹È¯é¹"""
    
    def test_extract_text_from_pdf(self, monkeypatch):
        """PDF K‰Æ­¹È½ú_ýnÆ¹È"""
        # PyMuPDF (fitz) nâÃ¯
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 content"
        
        mock_doc.__len__.return_value = 2
        mock_doc.__iter__.return_value = iter([mock_page1, mock_page2])
        
        # fitz.open ¢p’âÃ¯
        mock_open = MagicMock(return_value=mock_doc)
        monkeypatch.setattr("fitz.open", mock_open)
        
        # ¢p’ŸL
        result = pdf_service.extract_text_from_pdf("dummy.pdf")
        
        # ¢µü·çó
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "--- Page Break ---" in result
        mock_open.assert_called_once_with("dummy.pdf")
    
    def test_extract_text_from_pdf_error(self, monkeypatch):
        """PDFÆ­¹È½úBn¨éüÏóÉêó°Æ¹È"""
        # fitz.open ¢pL¨éü’•R‹ˆFkâÃ¯
        def mock_open_error(*args):
            raise Exception("Test error")
        
        monkeypatch.setattr("fitz.open", mock_open_error)
        
        # ¨éüL¹íüUŒ‹Sh’º
        with pytest.raises(Exception) as excinfo:
            pdf_service.extract_text_from_pdf("invalid.pdf")
        
        assert "Error extracting text from PDF" in str(excinfo.value)
    
    def test_extract_images_from_pdf(self, monkeypatch, tmp_path):
        """PDF K‰;Ï½ú_ýnÆ¹È"""
        # âÃ¯n»ÃÈ¢Ã×
        mock_doc = MagicMock()
        mock_page = MagicMock()
        
        # ;ÏÇü¿nâÃ¯
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0)]  # xref = 1
        mock_doc.extract_image.return_value = {
            "image": b"fake image data",
            "ext": "png"
        }
        
        mock_doc.__iter__.return_value = iter([mock_page])
        
        # âÃ¯’monkeypatchgi(
        monkeypatch.setattr("fitz.open", MagicMock(return_value=mock_doc))
        
        # ¢p’ŸL
        output_dir = str(tmp_path)
        result = pdf_service.extract_images_from_pdf("dummy.pdf", output_dir)
        
        # ¢µü·çó
        assert len(result) == 1
        assert result[0].name == "page1_img1.png"
        assert result[0].exists()
        
        # ;ÏÕ¡¤ën…¹’º
        with open(result[0], "rb") as f:
            assert f.read() == b"fake image data"
    
    def test_get_pdf_metadata(self, monkeypatch):
        """PDF á¿Çü¿Ö—_ýnÆ¹È"""
        # âÃ¯n»ÃÈ¢Ã×
        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Test Paper",
            "author": "Test Author",
            "subject": "Test Subject",
            "keywords": "test, pdf, metadata",
            "creator": "Test Creator",
            "producer": "Test Producer",
            "creationDate": "2023-01-01",
            "modDate": "2023-01-02"
        }
        mock_doc.__len__.return_value = 10
        
        monkeypatch.setattr("fitz.open", MagicMock(return_value=mock_doc))
        
        # ¢p’ŸL
        result = pdf_service.get_pdf_metadata("dummy.pdf")
        
        # ¢µü·çó
        assert result["title"] == "Test Paper"
        assert result["author"] == "Test Author"
        assert result["page_count"] == 10
        assert result["creation_date"] == "2023-01-01"
    
    def test_extract_sections_from_pdf(self, monkeypatch):
        """PDF »¯·çó½ú_ýnÆ¹È"""
        # âÃ¯n»ÃÈ¢Ã×
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "1. Introduction\nThis is the introduction.\n\n1.1 Background\nThis is the background."
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "2. Methods\nThis is the methods section."
        
        mock_doc.__iter__.return_value = iter([mock_page1, mock_page2])
        
        monkeypatch.setattr("fitz.open", MagicMock(return_value=mock_doc))
        
        # ¢p’ŸL
        result = pdf_service.extract_sections_from_pdf("dummy.pdf")
        
        # ¢µü·çó
        assert len(result) > 0
        assert any(section["heading"] == "Introduction" for section in result)
