import os
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.services.llm_service import analyze_paper, summarize_paper, extract_key_points
from app.models.paper import PaperContent
from app.models.llm import SummaryRequest, SummaryResponse, KeyPointsRequest, KeyPointsResponse

router = APIRouter()

@router.post("/summarize", response_model=SummaryResponse)
async def get_paper_summary(request: SummaryRequest = Body(...)):
    """
    Generate a summary of the paper using LLM.
    """
    paper_id = request.paper_id
    paper_dir = f"data/papers/{paper_id}"
    
    if not os.path.exists(paper_dir):
        raise HTTPException(status_code=404, detail="Paper not found")
    
    content_path = os.path.join(paper_dir, "content.json")
    if not os.path.exists(content_path):
        raise HTTPException(status_code=400, detail="Paper content not yet extracted")
    
    try:
        import json
        with open(content_path, 'r') as f:
            paper_content = json.load(f)
        
        # Generate summary using LLM
        summary = await summarize_paper(
            paper_content=paper_content,
            max_length=request.max_length,
            style=request.style,
            focus_areas=request.focus_areas
        )
        
        return SummaryResponse(
            paper_id=paper_id,
            summary=summary,
            focus_areas=request.focus_areas,
            style=request.style
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")

@router.post("/key-points", response_model=KeyPointsResponse)
async def get_key_points(request: KeyPointsRequest = Body(...)):
    """
    Extract key points from the paper using LLM.
    """
    paper_id = request.paper_id
    paper_dir = f"data/papers/{paper_id}"
    
    if not os.path.exists(paper_dir):
        raise HTTPException(status_code=404, detail="Paper not found")
    
    content_path = os.path.join(paper_dir, "content.json")
    if not os.path.exists(content_path):
        raise HTTPException(status_code=400, detail="Paper content not yet extracted")
    
    try:
        import json
        with open(content_path, 'r') as f:
            paper_content = json.load(f)
        
        # Extract key points using LLM
        key_points = await extract_key_points(
            paper_content=paper_content,
            num_points=request.num_points,
            categories=request.categories
        )
        
        return KeyPointsResponse(
            paper_id=paper_id,
            key_points=key_points,
            categories=request.categories
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting key points: {str(e)}")

@router.post("/analyze")
async def analyze_paper_content(
    paper_id: str = Body(...),
    analysis_type: str = Body(...),
    options: Optional[Dict[str, Any]] = Body(None)
):
    """
    Perform custom analysis on the paper using LLM.
    
    Analysis types:
    - structure: Analyze the structure of the paper
    - methodology: Analyze the methodology used
    - results: Analyze the results and findings
    - references: Analyze the references and citations
    - custom: Custom analysis with specified prompt
    """
    paper_dir = f"data/papers/{paper_id}"
    
    if not os.path.exists(paper_dir):
        raise HTTPException(status_code=404, detail="Paper not found")
    
    content_path = os.path.join(paper_dir, "content.json")
    if not os.path.exists(content_path):
        raise HTTPException(status_code=400, detail="Paper content not yet extracted")
    
    try:
        import json
        with open(content_path, 'r') as f:
            paper_content = json.load(f)
        
        # Analyze paper using LLM
        analysis_result = await analyze_paper(
            paper_content=paper_content,
            analysis_type=analysis_type,
            options=options or {}
        )
        
        return {
            "paper_id": paper_id,
            "analysis_type": analysis_type,
            "result": analysis_result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing paper: {str(e)}")
