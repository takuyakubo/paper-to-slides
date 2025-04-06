import os
import pytest
import tempfile
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.services import pdf_service

class TestPdfService:
    """PDF Service Test Class"""
    
    def test_extract_text_from_pdf(self, monkeypatch):
        """Test extracting text from PDF"""
        # Mock PyMuPDF (fitz)
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 content"
        
        mock_doc.__len__.return_value = 2
        mock_doc.__iter__.return_value = iter([mock_page1, mock_page2])
        
        # Mock fitz.open function
        mock_open = MagicMock(return_value=mock_doc)
        monkeypatch.setattr("fitz.open", mock_open)
        
        # Execute the function
        result = pdf_service.extract_text_from_pdf("dummy.pdf")
        
        # Assertions
        assert "Page 1 content" in result
        assert "Page 2 content" in result
        assert "--- Page Break ---" in result
        mock_open.assert_called_once_with("dummy.pdf")
    
    def test_extract_text_from_pdf_error(self, monkeypatch):
        """Test error handling when extracting text from PDF"""
        # Mock fitz.open to raise an exception
        def mock_open_error(*args):
            raise Exception("Test error")
        
        monkeypatch.setattr("fitz.open", mock_open_error)
        
        # Check that exception is raised
        with pytest.raises(Exception) as excinfo:
            pdf_service.extract_text_from_pdf("invalid.pdf")
        
        assert "Error extracting text from PDF" in str(excinfo.value)
    
    def test_extract_images_from_pdf(self, monkeypatch, tmp_path):
        """Test extracting images from PDF"""
        # Setup mocks
        mock_doc = MagicMock()
        mock_page = MagicMock()
        
        # Mock image data
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0)]  # xref = 1
        mock_doc.extract_image.return_value = {
            "image": b"fake image data",
            "ext": "png"
        }
        
        mock_doc.__iter__.return_value = iter([mock_page])
        
        # Apply mocks with monkeypatch
        monkeypatch.setattr("fitz.open", MagicMock(return_value=mock_doc))
        
        # Execute the function
        output_dir = str(tmp_path)
        result = pdf_service.extract_images_from_pdf("dummy.pdf", output_dir)
        
        # Assertions
        assert len(result) == 1
        assert result[0].name == "page1_img1.png"
        assert result[0].exists()
        
        # Verify image file content
        with open(result[0], "rb") as f:
            assert f.read() == b"fake image data"
    
    def test_get_pdf_metadata(self, monkeypatch):
        """Test getting PDF metadata"""
        # Setup mocks
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
        
        # Execute the function
        result = pdf_service.get_pdf_metadata("dummy.pdf")
        
        # Assertions
        assert result["title"] == "Test Paper"
        assert result["author"] == "Test Author"
        assert result["page_count"] == 10
        assert result["creation_date"] == "2023-01-01"
    
    def test_extract_sections_from_pdf(self, monkeypatch):
        """Test extracting sections from PDF"""
        # Setup mocks
        mock_doc = MagicMock()
        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "1. Introduction\nThis is the introduction.\n\n1.1 Background\nThis is the background."
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "2. Methods\nThis is the methods section."
        
        mock_doc.__iter__.return_value = iter([mock_page1, mock_page2])
        
        monkeypatch.setattr("fitz.open", MagicMock(return_value=mock_doc))
        
        # Execute the function
        result = pdf_service.extract_sections_from_pdf("dummy.pdf")
        
        # Assertions
        assert len(result) > 0
        assert any(section["heading"] == "Introduction" for section in result)
