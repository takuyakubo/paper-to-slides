import os
import pytest
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

from app.services.pdf_service import extract_text_from_pdf
from app.services.llm_service import summarize_paper


@pytest.fixture
def sample_pdf_path():
    return "/path/to/test.pdf"


@pytest.mark.asyncio
async def test_pdf_to_text_workflow(monkeypatch, sample_pdf_path):
    sample_text = """
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
    """

    # extract_text_from_pdf��ï
    mock_extract = MagicMock(return_value=sample_text)
    monkeypatch.setattr("app.services.pdf_service.extract_text_from_pdf", mock_extract)

    # summarize_papergLLM�(Y����ï
    mock_generate_text = MagicMock(
        return_value="This is a summarized version of the test paper."
    )
    monkeypatch.setattr("app.services.llm_service.generate_text", mock_generate_text)

    # ƹȟL
    # 1. PDFK�ƭ�Ƚ�
    extracted_text = extract_text_from_pdf(sample_pdf_path)

    # ��P�n<
    assert "Title: Test Paper" in extracted_text
    assert "Abstract" in extracted_text
    assert "Introduction" in extracted_text
    assert "Conclusion" in extracted_text

    # 2. ��W_ƭ�Ȓcf�
    paper_content = {
        "text": extracted_text,
        "sections": [
            {
                "heading": "Introduction",
                "content": "This is the introduction section of the test paper.",
            },
            {
                "heading": "Methodology",
                "content": "This section describes the methodology used in the study.",
            },
            {"heading": "Results", "content": "Here are the results of the study."},
            {
                "heading": "Conclusion",
                "content": "This is the conclusion of the test paper.",
            },
        ],
    }

    summary = await summarize_paper(paper_content, max_length=200, style="academic")

    # �P�n<
    assert summary == "This is a summarized version of the test paper."

    # LLM��ӹLij�����g|p�_K��
    mock_generate_text.assert_called_once()
    call_args = mock_generate_text.call_args[1]
    assert "academic" in call_args["prompt"].lower()
    assert call_args["temperature"] == 0.3  # cWD)�-�
