import os
import uuid
from fastapi import APIRouter, File, UploadFile, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import aiofiles
from pathlib import Path
from datetime import datetime

from app.services.pdf_service import extract_text_from_pdf, extract_images_from_pdf
from app.models.paper import PaperInfo, PaperMetadata, PaperContent

router = APIRouter()

# Ensure data directory exists
DATA_DIR = Path("data/papers")
DATA_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/upload", response_model=PaperInfo)
async def upload_paper(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    """
    Upload a paper in PDF format.
    
    The file will be saved and processed in the background.
    """
    # Validate file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Generate unique ID and create storage path
    paper_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    filename = file.filename
    
    # Create directory for this paper
    paper_dir = DATA_DIR / paper_id
    paper_dir.mkdir(exist_ok=True)
    
    # Save the PDF file
    file_path = paper_dir / filename
    
    try:
        # Save the uploaded file
        async with aiofiles.open(file_path, 'wb') as out_file:
            content = await file.read()
            await out_file.write(content)
        
        # Schedule background processing
        background_tasks.add_task(process_paper, paper_id, str(file_path))
        
        # Return basic information
        return PaperInfo(
            paper_id=paper_id,
            filename=filename,
            upload_time=timestamp,
            status="processing",
        )
    
    except Exception as e:
        # Clean up on error
        if paper_dir.exists():
            import shutil
            shutil.rmtree(paper_dir)
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@router.get("/{paper_id}", response_model=PaperInfo)
async def get_paper_info(paper_id: str):
    """
    Get information about an uploaded paper.
    """
    paper_dir = DATA_DIR / paper_id
    
    if not paper_dir.exists():
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        # Get metadata file
        metadata_path = paper_dir / "metadata.json"
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                return PaperInfo(**metadata)
        else:
            # If metadata doesn't exist yet, return basic info
            files = list(paper_dir.glob('*.pdf'))
            if not files:
                raise HTTPException(status_code=404, detail="PDF file not found")
            
            return PaperInfo(
                paper_id=paper_id,
                filename=files[0].name,
                upload_time=datetime.fromtimestamp(files[0].stat().st_mtime).isoformat(),
                status="processing",
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving paper info: {str(e)}")

@router.get("/{paper_id}/content", response_model=PaperContent)
async def get_paper_content(paper_id: str):
    """
    Get the extracted content of a paper.
    """
    paper_dir = DATA_DIR / paper_id
    
    if not paper_dir.exists():
        raise HTTPException(status_code=404, detail="Paper not found")
    
    content_path = paper_dir / "content.json"
    if not content_path.exists():
        raise HTTPException(status_code=404, detail="Content not yet extracted or processing failed")
    
    try:
        import json
        with open(content_path, 'r') as f:
            content = json.load(f)
            return PaperContent(**content)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving paper content: {str(e)}")

@router.delete("/{paper_id}")
async def delete_paper(paper_id: str):
    """
    Delete a paper and all associated files.
    """
    paper_dir = DATA_DIR / paper_id
    
    if not paper_dir.exists():
        raise HTTPException(status_code=404, detail="Paper not found")
    
    try:
        import shutil
        shutil.rmtree(paper_dir)
        return {"message": f"Paper {paper_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting paper: {str(e)}")

# Background task for processing papers
def process_paper(paper_id: str, file_path: str):
    """
    Process a paper in the background.
    
    This function extracts text, images, and metadata from the PDF.
    """
    paper_dir = DATA_DIR / paper_id
    pdf_path = Path(file_path)
    
    try:
        # Extract text from PDF
        text_content = extract_text_from_pdf(file_path)
        
        # Extract images (will save to paper directory)
        image_paths = extract_images_from_pdf(file_path, str(paper_dir))
        
        # Get basic metadata
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        
        metadata = {
            "paper_id": paper_id,
            "filename": pdf_path.name,
            "upload_time": datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat(),
            "page_count": len(doc),
            "title": doc.metadata.get("title", "Unknown Title"),
            "author": doc.metadata.get("author", "Unknown Author"),
            "subject": doc.metadata.get("subject", ""),
            "keywords": doc.metadata.get("keywords", ""),
            "status": "processed",
        }
        
        # Save metadata
        with open(paper_dir / "metadata.json", 'w') as f:
            import json
            json.dump(metadata, f)
        
        # Save content
        content = {
            "paper_id": paper_id,
            "text": text_content,
            "sections": [],  # We'll add section detection later
            "images": [str(path.relative_to(paper_dir)) for path in image_paths],
        }
        
        with open(paper_dir / "content.json", 'w') as f:
            json.dump(content, f)
        
    except Exception as e:
        # On error, update metadata with error status
        error_metadata = {
            "paper_id": paper_id,
            "filename": pdf_path.name,
            "upload_time": datetime.fromtimestamp(pdf_path.stat().st_mtime).isoformat(),
            "status": "error",
            "error_message": str(e),
        }
        
        with open(paper_dir / "metadata.json", 'w') as f:
            import json
            json.dump(error_metadata, f)
