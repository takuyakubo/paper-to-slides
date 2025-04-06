import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import os
import json
import uuid
from datetime import datetime
from io import BytesIO

from app.main import app
from app.models.paper import PaperInfo, PaperContent

client = TestClient(app)


@pytest.fixture
def mock_uuid():
    """Mock UUID to return a fixed value"""
    fixed_uuid = "12345678-1234-5678-1234-567812345678"
    with patch("uuid.uuid4", return_value=uuid.UUID(fixed_uuid)):
        yield fixed_uuid


@pytest.fixture
def mock_pdf_file():
    """Mock PDF file fixture"""
    return BytesIO(b"%PDF-1.5\nTest PDF content")


@pytest.fixture
def mock_datetime():
    """Mock datetime.now to return a fixed value"""
    fixed_date = datetime(2023, 1, 1, 12, 0, 0)
    with patch("app.routers.paper.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_date
        mock_dt.fromtimestamp.return_value = fixed_date
        yield fixed_date.isoformat()


class TestPaperRoutes:
    """Test class for paper-related API routes"""

    @patch("app.routers.paper.aiofiles.open")
    @patch("app.routers.paper.BackgroundTasks")
    @patch("pathlib.Path.mkdir")
    def test_upload_paper_success(
        self,
        mock_mkdir,
        mock_bg_tasks,
        mock_aiofiles,
        mock_uuid,
        mock_datetime,
        mock_pdf_file,
    ):
        """Test successful paper upload"""
        # Setup mocks
        mock_file = mock_aiofiles.return_value.__aenter__.return_value
        mock_bg_tasks = mock_bg_tasks.return_value

        # API request
        response = client.post(
            "/api/papers/upload",
            files={"file": ("test.pdf", mock_pdf_file, "application/pdf")},
        )

        # Assertions
        assert response.status_code == 200
        assert response.json()["paper_id"] == mock_uuid
        assert response.json()["filename"] == "test.pdf"
        assert response.json()["status"] == "processing"

        # Verify background task was added
        mock_bg_tasks.add_task.assert_called_once()

        # Verify file was saved
        mock_file.write.assert_called_once()

    def test_upload_paper_invalid_format(self, mock_datetime):
        """Test uploading invalid file format"""
        # Send a text file
        response = client.post(
            "/api/papers/upload",
            files={"file": ("test.txt", BytesIO(b"This is not a PDF"), "text/plain")},
        )

        # Assertions
        assert response.status_code == 400
        assert "File must be a PDF" in response.json()["detail"]

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_paper_info(self, mock_open, mock_exists, mock_uuid):
        """Test getting paper information"""
        # Setup mocks
        mock_exists.return_value = True

        # Mock metadata file content
        paper_info = {
            "paper_id": mock_uuid,
            "filename": "test.pdf",
            "upload_time": "2023-01-01T12:00:00",
            "status": "processed",
            "title": "Test Paper",
            "author": "Test Author",
            "page_count": 10,
        }

        # Mock open function's context manager return value
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(paper_info)
        mock_open.return_value = mock_file

        # API request
        response = client.get(f"/api/papers/{mock_uuid}")

        # Assertions
        assert response.status_code == 200
        assert response.json()["paper_id"] == mock_uuid
        assert response.json()["status"] == "processed"
        assert response.json()["title"] == "Test Paper"

    @patch("pathlib.Path.exists")
    def test_get_paper_info_not_found(self, mock_exists):
        """Test getting information for non-existent paper"""
        # Setup mocks
        mock_exists.return_value = False

        # API request
        response = client.get("/api/papers/nonexistent-id")

        # Assertions
        assert response.status_code == 404
        assert "Paper not found" in response.json()["detail"]

    @patch("pathlib.Path.exists")
    @patch("builtins.open", new_callable=MagicMock)
    def test_get_paper_content(self, mock_open, mock_exists, mock_uuid):
        """Test getting paper content"""
        # Setup mocks
        mock_exists.return_value = True

        # Mock content file
        paper_content = {
            "paper_id": mock_uuid,
            "text": "This is the text content of the paper.",
            "sections": [
                {"heading": "Introduction", "content": "This is the introduction."}
            ],
            "images": ["images/figure1.png"],
        }

        # Mock open function's context manager return value
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = json.dumps(paper_content)
        mock_open.return_value = mock_file

        # API request
        response = client.get(f"/api/papers/{mock_uuid}/content")

        # Assertions
        assert response.status_code == 200
        assert response.json()["paper_id"] == mock_uuid
        assert response.json()["text"] == "This is the text content of the paper."
        assert len(response.json()["sections"]) == 1
        assert response.json()["sections"][0]["heading"] == "Introduction"

    @patch("pathlib.Path.exists")
    def test_get_paper_content_not_found(self, mock_exists):
        """Test getting content for non-existent paper"""
        # First exists is True (directory exists), second is False (content file doesn't exist)
        mock_exists.side_effect = [True, False]

        # API request
        response = client.get("/api/papers/nonexistent-id/content")

        # Assertions
        assert response.status_code == 404
        assert "Content not yet extracted" in response.json()["detail"]

    @patch("pathlib.Path.exists")
    @patch("shutil.rmtree")
    def test_delete_paper(self, mock_rmtree, mock_exists, mock_uuid):
        """Test deleting a paper"""
        # Setup mocks
        mock_exists.return_value = True

        # API request
        response = client.delete(f"/api/papers/{mock_uuid}")

        # Assertions
        assert response.status_code == 200
        assert "deleted successfully" in response.json()["message"]
        mock_rmtree.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_delete_paper_not_found(self, mock_exists):
        """Test deleting a non-existent paper"""
        # Setup mocks
        mock_exists.return_value = False

        # API request
        response = client.delete("/api/papers/nonexistent-id")

        # Assertions
        assert response.status_code == 404
        assert "Paper not found" in response.json()["detail"]

    @patch("app.routers.paper.extract_text_from_pdf")
    @patch("app.routers.paper.extract_images_from_pdf")
    @patch("fitz.open")
    @patch("builtins.open", new_callable=MagicMock)
    @patch("json.dump")
    def test_process_paper(
        self,
        mock_json_dump,
        mock_open,
        mock_fitz_open,
        mock_extract_images,
        mock_extract_text,
        mock_uuid,
    ):
        """Test paper processing background task"""
        # Setup mocks
        mock_extract_text.return_value = "Extracted text content"
        mock_extract_images.return_value = [
            Path(f"data/papers/{mock_uuid}/images/figure1.png")
        ]

        mock_doc = MagicMock()
        mock_doc.metadata = {
            "title": "Test Paper Title",
            "author": "Test Author",
            "subject": "Test Subject",
            "keywords": "test, keywords",
        }
        mock_doc.__len__.return_value = 10
        mock_fitz_open.return_value = mock_doc

        # Test the process_paper function directly
        from app.routers.paper import process_paper

        # Mock date
        with patch("app.routers.paper.datetime") as mock_dt:
            mock_dt.fromtimestamp.return_value = datetime(2023, 1, 1, 12, 0, 0)

            # Execute function
            process_paper(mock_uuid, f"/tmp/{mock_uuid}/test.pdf")

            # Assertions
            mock_extract_text.assert_called_once()
            mock_extract_images.assert_called_once()
            mock_fitz_open.assert_called_once()

            # Verify metadata and content were saved
            assert mock_json_dump.call_count == 2

            # First call (metadata)
            metadata_call = mock_json_dump.call_args_list[0][0][0]
            assert metadata_call["paper_id"] == mock_uuid
            assert metadata_call["title"] == "Test Paper Title"
            assert metadata_call["status"] == "processed"

            # Second call (content)
            content_call = mock_json_dump.call_args_list[1][0][0]
            assert content_call["paper_id"] == mock_uuid
            assert content_call["text"] == "Extracted text content"
