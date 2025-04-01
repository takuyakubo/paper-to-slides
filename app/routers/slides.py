import os
import uuid
from fastapi import APIRouter, HTTPException, BackgroundTasks, Body
from fastapi.responses import FileResponse
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from app.models.slides import SlideRequest, SlideInfo, SlideTemplate
from app.services.slides_service import generate_presentation

router = APIRouter()

# Ensure output directory exists
OUTPUT_DIR = Path("output/slides")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

@router.post("/generate", response_model=SlideInfo)
async def create_slides(
    background_tasks: BackgroundTasks,
    request: SlideRequest = Body(...),
):
    """
    Generate presentation slides from a processed paper.
    """
    paper_id = request.paper_id
    paper_dir = Path(f"data/papers/{paper_id}")
    
    if not paper_dir.exists():
        raise HTTPException(status_code=404, detail="Paper not found")
    
    # Check if content has been extracted
    content_path = paper_dir / "content.json"
    if not content_path.exists():
        raise HTTPException(status_code=400, detail="Paper content not yet extracted")
    
    # Generate a unique ID for this slide generation
    slide_id = str(uuid.uuid4())
    
    # Create directory for this presentation
    slide_dir = OUTPUT_DIR / slide_id
    slide_dir.mkdir(exist_ok=True)
    
    # Save request configuration
    import json
    with open(slide_dir / "request.json", 'w') as f:
        json.dump(request.dict(), f)
    
    # Initialize metadata
    metadata = {
        "slide_id": slide_id,
        "paper_id": paper_id,
        "request_time": datetime.now().isoformat(),
        "status": "generating",
        "template": request.template,
        "output_format": request.output_format,
    }
    
    with open(slide_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f)
    
    # Schedule background task to generate slides
    background_tasks.add_task(
        process_slide_generation,
        slide_id=slide_id,
        paper_id=paper_id,
        template=request.template,
        output_format=request.output_format,
        include_images=request.include_images,
        custom_options=request.custom_options
    )
    
    return SlideInfo(**metadata)

@router.get("/{slide_id}", response_model=SlideInfo)
async def get_slide_info(slide_id: str):
    """
    Get information about a slide generation task.
    """
    slide_dir = OUTPUT_DIR / slide_id
    
    if not slide_dir.exists():
        raise HTTPException(status_code=404, detail="Slides not found")
    
    try:
        # Get metadata file
        metadata_path = slide_dir / "metadata.json"
        if metadata_path.exists():
            import json
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                return SlideInfo(**metadata)
        else:
            raise HTTPException(status_code=500, detail="Metadata not found")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving slide info: {str(e)}")

@router.get("/{slide_id}/download")
async def download_slides(slide_id: str):
    """
    Download the generated presentation.
    """
    slide_dir = OUTPUT_DIR / slide_id
    
    if not slide_dir.exists():
        raise HTTPException(status_code=404, detail="Slides not found")
    
    # Check metadata for status
    try:
        import json
        with open(slide_dir / "metadata.json", 'r') as f:
            metadata = json.load(f)
            
        if metadata.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Slides generation not yet complete")
        
        # Get output file path from metadata
        output_file = metadata.get("output_file")
        if not output_file:
            raise HTTPException(status_code=500, detail="Output file not found in metadata")
        
        file_path = slide_dir / output_file
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Output file not found")
        
        return FileResponse(
            path=file_path,
            filename=output_file,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving slides: {str(e)}")

@router.get("/templates", response_model=List[SlideTemplate])
async def list_templates():
    """
    List available slide templates.
    """
    # For now, return hardcoded templates
    # In a real application, these would be loaded from the filesystem
    return [
        SlideTemplate(
            id="academic",
            name="Academic",
            description="A professional template for academic presentations",
            preview_image="templates/academic_preview.png"
        ),
        SlideTemplate(
            id="minimalist",
            name="Minimalist",
            description="A clean, minimalist template with focus on content",
            preview_image="templates/minimalist_preview.png"
        ),
        SlideTemplate(
            id="corporate",
            name="Corporate",
            description="A business-oriented template with modern design",
            preview_image="templates/corporate_preview.png"
        )
    ]

@router.delete("/{slide_id}")
async def delete_slides(slide_id: str):
    """
    Delete generated slides and associated files.
    """
    slide_dir = OUTPUT_DIR / slide_id
    
    if not slide_dir.exists():
        raise HTTPException(status_code=404, detail="Slides not found")
    
    try:
        import shutil
        shutil.rmtree(slide_dir)
        return {"message": f"Slides {slide_id} deleted successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting slides: {str(e)}")

# Background task for processing slide generation
def process_slide_generation(
    slide_id: str,
    paper_id: str,
    template: str,
    output_format: str = "pptx",
    include_images: bool = True,
    custom_options: Optional[Dict[str, Any]] = None
):
    """
    Process slide generation in the background.
    """
    slide_dir = OUTPUT_DIR / slide_id
    paper_dir = Path(f"data/papers/{paper_id}")
    
    try:
        # Load paper content
        import json
        with open(paper_dir / "content.json", 'r') as f:
            paper_content = json.load(f)
        
        # Generate presentation
        output_file = generate_presentation(
            paper_content=paper_content,
            output_dir=str(slide_dir),
            template=template,
            output_format=output_format,
            include_images=include_images,
            custom_options=custom_options or {}
        )
        
        # Update metadata
        with open(slide_dir / "metadata.json", 'r') as f:
            metadata = json.load(f)
        
        metadata.update({
            "status": "completed",
            "completion_time": datetime.now().isoformat(),
            "output_file": output_file
        })
        
        with open(slide_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f)
        
    except Exception as e:
        # On error, update metadata with error status
        try:
            with open(slide_dir / "metadata.json", 'r') as f:
                metadata = json.load(f)
            
            metadata.update({
                "status": "error",
                "error_message": str(e),
                "completion_time": datetime.now().isoformat()
            })
            
            with open(slide_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f)
        except:
            # If we can't update metadata, just log the error
            print(f"Error generating slides: {str(e)}")
