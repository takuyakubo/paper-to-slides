import os
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio

from app.services import llm_service


class TestLLMService:

    @pytest.fixture
    def mock_openai_response(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message = MagicMock()
        mock_response.choices[0].message.content = "Generated text from OpenAI"
        return mock_response

    @pytest.fixture
    def mock_anthropic_response(self):
        mock_content = MagicMock()
        mock_content.text = "Generated text from Anthropic"

        mock_response = MagicMock()
        mock_response.content = [mock_content]
        return mock_response

    @pytest.mark.asyncio
    async def test_get_llm_client_openai(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        mock_openai = MagicMock()
        monkeypatch.setattr("openai.api_key", None)
        monkeypatch.setattr("llm_service.openai", mock_openai)

        monkeypatch.setattr(
            "builtins.__import__",
            lambda name, *args, **kwargs: (
                mock_openai if name == "openai" else __import__(name, *args, **kwargs)
            ),
        )

        with patch("app.services.llm_service.DEFAULT_PROVIDER", "openai"):
            result = await llm_service.get_llm_client("openai")
            assert result is not None

    @pytest.mark.asyncio
    async def test_generate_text_openai(self, monkeypatch, mock_openai_response):
        mock_client = AsyncMock()
        mock_client.chat = MagicMock()
        mock_client.chat.completions = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            return_value=mock_openai_response
        )

        mock_get_client = AsyncMock(return_value=mock_client)
        monkeypatch.setattr("app.services.llm_service.get_llm_client", mock_get_client)

        result = await llm_service.generate_text(
            prompt="Test prompt", provider="openai", model="gpt-4o", temperature=0.7
        )

        assert result == "Generated text from OpenAI"
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        assert call_args["model"] == "gpt-4o"
        assert call_args["temperature"] == 0.7
        assert any(msg["content"] == "Test prompt" for msg in call_args["messages"])

    @pytest.mark.asyncio
    async def test_generate_text_anthropic(self, monkeypatch, mock_anthropic_response):
        mock_client = MagicMock()
        mock_client.messages = MagicMock()
        mock_client.messages.create = MagicMock(return_value=mock_anthropic_response)

        mock_get_client = AsyncMock(return_value=mock_client)
        monkeypatch.setattr("app.services.llm_service.get_llm_client", mock_get_client)

        result = await llm_service.generate_text(
            prompt="Test prompt",
            provider="anthropic",
            model="claude-3-opus-20240229",
            temperature=0.7,
        )

        # ������
        assert result == "Generated text from Anthropic"
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args[1]
        assert call_args["model"] == "claude-3-opus-20240229"
        assert call_args["temperature"] == 0.7
        assert any(msg["content"] == "Test prompt" for msg in call_args["messages"])

    @pytest.mark.asyncio
    async def test_summarize_paper(self, monkeypatch):
        mock_generate = AsyncMock(return_value="Summarized paper content")
        monkeypatch.setattr("app.services.llm_service.generate_text", mock_generate)

        paper_content = {
            "text": "This is a test paper about some research topic.",
            "sections": [{"heading": "Introduction", "content": "Intro content"}],
        }

        result = await llm_service.summarize_paper(
            paper_content=paper_content, max_length=300, style="academic"
        )

        assert result == "Summarized paper content"
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[1]
        assert "style" in call_args["prompt"].lower()
        assert "academic" in call_args["prompt"].lower()
        assert call_args["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_extract_key_points_success(self, monkeypatch):
        json_response = """```json
        [
            {
                "content": "First key point",
                "category": "finding",
                "importance": 8,
                "source_section": "Results"
            },
            {
                "content": "Second key point",
                "category": "method",
                "importance": 7,
                "source_section": "Methodology"
            }
        ]
        ```"""

        mock_generate = AsyncMock(return_value=json_response)
        monkeypatch.setattr("app.services.llm_service.generate_text", mock_generate)

        paper_content = {"text": "Test paper content"}
        result = await llm_service.extract_key_points(paper_content, num_points=2)

        assert len(result) == 2
        assert result[0]["content"] == "First key point"
        assert result[0]["category"] == "finding"
        assert result[0]["importance"] == 8
        assert result[1]["content"] == "Second key point"

    @pytest.mark.asyncio
    async def test_extract_key_points_parse_error(self, monkeypatch):
        text_response = """
        - Key point 1: Important finding about the topic
          Category: finding
          Importance: 8
          
        - Key point 2: Interesting methodology used
          Category: method
          Importance: 7
        """

        mock_generate = AsyncMock(return_value=text_response)
        monkeypatch.setattr("app.services.llm_service.generate_text", mock_generate)

        def mock_loads(*args, **kwargs):
            raise json.JSONDecodeError("Test error", "", 0)

        monkeypatch.setattr("json.loads", mock_loads)

        paper_content = {"text": "Test paper content"}
        result = await llm_service.extract_key_points(paper_content, num_points=2)

        assert isinstance(result, list)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_generate_slide_content(self, monkeypatch):
        json_response = """```json
        [
            {
                "title": "Paper Title",
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
        ```"""

        mock_generate = AsyncMock(return_value=json_response)
        monkeypatch.setattr("app.services.llm_service.generate_text", mock_generate)

        mock_re = MagicMock()
        mock_match = MagicMock()
        mock_match.group.return_value = "Test Paper Title"
        mock_re.search.return_value = mock_match
        monkeypatch.setattr("app.services.llm_service.re", mock_re)

        paper_content = {"text": "Test Paper Title\nAbstract: This is a test paper."}
        result = await llm_service.generate_slide_content(paper_content, max_slides=5)

        assert len(result) == 2
        assert result[0]["title"] == "Paper Title"
        assert result[0]["layout"] == "title"
        assert result[1]["title"] == "Introduction"
        assert "Background" in result[1]["content"]

    @pytest.mark.asyncio
    async def test_analyze_paper(self, monkeypatch):
        mock_generate = AsyncMock(
            return_value="Detailed analysis of the paper's methodology"
        )
        monkeypatch.setattr("app.services.llm_service.generate_text", mock_generate)

        paper_content = {"text": "Test paper content for analysis"}
        result = await llm_service.analyze_paper(
            paper_content=paper_content, analysis_type="methodology"
        )

        assert result["analysis_type"] == "methodology"
        assert result["text"] == "Detailed analysis of the paper's methodology"
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[1]
        assert "methodology" in call_args["prompt"].lower()
