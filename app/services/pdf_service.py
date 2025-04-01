import os
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content as a string
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Extract text from each page
        text = ""
        for page_num, page in enumerate(doc):
            text += page.get_text()
            # Add a page separator if not the last page
            if page_num < len(doc) - 1:
                text += "\n\n--- Page Break ---\n\n"
        
        return text
    
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def extract_images_from_pdf(pdf_path: str, output_dir: str) -> List[Path]:
    """
    Extract images from a PDF file and save them to the output directory.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images
        
    Returns:
        List of paths to extracted image files
    """
    try:
        # Create images directory if it doesn't exist
        images_dir = Path(output_dir) / "images"
        images_dir.mkdir(parents=True, exist_ok=True)
        
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        image_paths = []
        
        # Loop through each page
        for page_num, page in enumerate(doc):
            # Get images on the page
            image_list = page.get_images(full=True)
            
            # Process each image
            for img_idx, img in enumerate(image_list):
                xref = img[0]  # Image reference
                
                # Extract image
                base_img = doc.extract_image(xref)
                img_bytes = base_img["image"]
                img_ext = base_img["ext"]
                
                # Generate a unique filename
                img_filename = f"page{page_num + 1}_img{img_idx + 1}.{img_ext}"
                img_path = images_dir / img_filename
                
                # Save the image
                with open(img_path, "wb") as img_file:
                    img_file.write(img_bytes)
                
                image_paths.append(img_path)
        
        return image_paths
    
    except Exception as e:
        raise Exception(f"Error extracting images from PDF: {str(e)}")

def extract_sections_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract sections and their headings from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing section information
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Regular expressions for heading detection
        heading_patterns = [
            r"^\s*(\d+\.(?:\d+\.)*)\s+(.*?)\s*$",  # Numbered headings like "1. Introduction"
            r"^([A-Z][A-Za-z\s]+)$",  # Capitalized text on its own line
        ]
        
        sections = []
        current_section = None
        current_page = None
        current_text = ""
        
        # Process each page
        for page_num, page in enumerate(doc):
            text = page.get_text()
            lines = text.split("\n")
            
            for line in lines:
                # Check if this line is a heading
                is_heading = False
                heading_level = 0
                heading_text = ""
                
                for pattern in heading_patterns:
                    match = re.match(pattern, line.strip())
                    if match:
                        is_heading = True
                        # Determine heading level
                        if "." in match.group(1) if len(match.groups()) > 1 else False:
                            # Numbered heading, level based on dots
                            heading_level = match.group(1).count(".") + 1
                            heading_text = match.group(2)
                        else:
                            # Capitalized heading, assume level 1
                            heading_level = 1
                            heading_text = match.group(1) if len(match.groups()) > 0 else line.strip()
                        break
                
                if is_heading:
                    # Save previous section if it exists
                    if current_section:
                        sections.append({
                            "heading": current_section,
                            "level": heading_level,
                            "content": current_text.strip(),
                            "start_page": current_page
                        })
                    
                    # Start new section
                    current_section = heading_text
                    current_page = page_num + 1
                    current_text = ""
                else:
                    # Add to current section's text
                    if current_section:
                        current_text += line + "\n"
        
        # Add the last section
        if current_section:
            sections.append({
                "heading": current_section,
                "level": heading_level,
                "content": current_text.strip(),
                "start_page": current_page
            })
        
        return sections
    
    except Exception as e:
        raise Exception(f"Error extracting sections from PDF: {str(e)}")

def extract_tables_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from a PDF file.
    
    This is a placeholder function. Accurate table extraction from PDFs
    requires more sophisticated libraries or approaches.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of dictionaries containing table information
    """
    # This is a placeholder - would need more sophisticated tools for accurate table extraction
    return []

def get_pdf_metadata(pdf_path: str) -> Dict[str, Any]:
    """
    Get metadata from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary of metadata
    """
    try:
        # Open the PDF
        doc = fitz.open(pdf_path)
        
        # Extract basic metadata
        metadata = {
            "title": doc.metadata.get("title", "Unknown Title"),
            "author": doc.metadata.get("author", "Unknown Author"),
            "subject": doc.metadata.get("subject", ""),
            "keywords": doc.metadata.get("keywords", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "modification_date": doc.metadata.get("modDate", ""),
            "page_count": len(doc),
        }
        
        return metadata
    
    except Exception as e:
        raise Exception(f"Error getting PDF metadata: {str(e)}")
