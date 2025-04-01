import os
import json
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv
import httpx
import asyncio

# Load environment variables
load_dotenv()

# Load LLM provider based on environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Default to OpenAI if both are available
DEFAULT_PROVIDER = "openai" if OPENAI_API_KEY else "anthropic" if ANTHROPIC_API_KEY else None

if not DEFAULT_PROVIDER:
    print("Warning: No LLM API keys found in environment variables. LLM features will not work.")

async def get_llm_client(provider: str = DEFAULT_PROVIDER):
    """
    Get an LLM client based on the provider.
    
    Args:
        provider: LLM provider (openai or anthropic)
        
    Returns:
        LLM client module
    """
    if provider == "openai":
        try:
            import openai
            openai.api_key = OPENAI_API_KEY
            return openai
        except ImportError:
            raise ImportError("OpenAI package not installed. Run 'pip install openai'.")
    elif provider == "anthropic":
        try:
            import anthropic
            return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        except ImportError:
            raise ImportError("Anthropic package not installed. Run 'pip install anthropic'.")
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

async def generate_text(
    prompt: str,
    provider: str = DEFAULT_PROVIDER,
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    system_message: Optional[str] = None
) -> str:
    """
    Generate text using an LLM.
    
    Args:
        prompt: The prompt to send to the LLM
        provider: LLM provider (openai or anthropic)
        model: Model name to use (defaults to provider's default)
        temperature: Temperature for generation (0.0 to 1.0)
        max_tokens: Maximum tokens to generate
        system_message: System message for chat models
        
    Returns:
        Generated text
    """
    if provider == "openai":
        openai = await get_llm_client(provider)
        
        # Set default model if not specified
        model = model or "gpt-4o"
        
        # Prepare messages
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        # Generate response
        response = await openai.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    elif provider == "anthropic":
        anthropic_client = await get_llm_client(provider)
        
        # Set default model if not specified
        model = model or "claude-3-opus-20240229"
        
        # Prepare system prompt
        system = system_message or ""
        
        # Generate response
        response = anthropic_client.messages.create(
            model=model,
            system=system,
            max_tokens=max_tokens or 4000,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.content[0].text
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

async def summarize_paper(
    paper_content: Dict[str, Any],
    max_length: int = 500,
    style: str = "academic",
    focus_areas: Optional[List[str]] = None
) -> str:
    """
    Generate a summary of a paper.
    
    Args:
        paper_content: Paper content dictionary (with text and sections)
        max_length: Maximum length of the summary in words
        style: Style of the summary (academic, simple, bullet_points)
        focus_areas: Specific areas to focus on
        
    Returns:
        Generated summary
    """
    # Get paper text
    text = paper_content.get("text", "")
    
    # Truncate if too long for context window
    if len(text) > 100000:
        text = text[:100000] + "... [text truncated due to length]"
    
    # Craft prompt
    prompt = f"""Summarize the following academic paper. Please create a concise summary of approximately {max_length} words.

Style: {style}
"""

    if focus_areas:
        prompt += f"Focus on these specific areas: {', '.join(focus_areas)}\n\n"
    
    prompt += f"Paper text:\n{text}\n\nSummary:"
    
    # Get system message based on style
    system_message = "You are an expert academic research assistant. Your task is to summarize academic papers clearly and concisely."
    
    if style == "simple":
        system_message += " Use simple, accessible language that a non-expert could understand."
    elif style == "bullet_points":
        system_message += " Format your summary as bullet points covering the key aspects of the paper."
    
    # Generate summary
    return await generate_text(
        prompt=prompt,
        temperature=0.3,  # Lower temperature for more focused output
        system_message=system_message
    )

async def extract_key_points(
    paper_content: Dict[str, Any],
    num_points: int = 5,
    categories: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Extract key points from a paper.
    
    Args:
        paper_content: Paper content dictionary
        num_points: Number of key points to extract
        categories: Categories of key points to focus on
        
    Returns:
        List of key points with content and category
    """
    # Get paper text
    text = paper_content.get("text", "")
    
    # Truncate if too long for context window
    if len(text) > 100000:
        text = text[:100000] + "... [text truncated due to length]"
    
    # Craft prompt
    prompt = f"""Extract the {num_points} most important key points from the following academic paper. 
For each key point, include:
1. The main content of the key point
2. The category it belongs to (e.g., methodology, finding, limitation)
3. An importance score from 1-10
4. The section of the paper where this point is made

"""

    if categories:
        prompt += f"Focus on these categories: {', '.join(categories)}\n\n"
    
    prompt += f"""Paper text:
{text}

Please format your response as a JSON array with objects that have 'content', 'category', 'importance', and 'source_section' fields.
"""
    
    # Generate key points
    response = await generate_text(
        prompt=prompt,
        temperature=0.3,
        system_message="You are an expert academic research assistant tasked with identifying the most important points in academic papers."
    )
    
    # Parse JSON response
    try:
        # Clean up response to ensure it only contains the JSON part
        json_text = response
        if "```json" in response:
            json_text = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_text = response.split("```")[1].split("```")[0].strip()
        
        key_points = json.loads(json_text)
        
        # Validate and fix structure if needed
        if isinstance(key_points, list):
            for i, point in enumerate(key_points):
                if not isinstance(point, dict):
                    key_points[i] = {"content": str(point), "category": "general", "importance": 5}
                elif "content" not in point:
                    point["content"] = str(point.get("point", "Unknown point"))
                if "category" not in point:
                    point["category"] = "general"
                if "importance" not in point:
                    point["importance"] = 5
        else:
            # If not a list, try to convert
            if isinstance(key_points, dict):
                key_points = [{"content": v, "category": k, "importance": 5} for k, v in key_points.items()]
            else:
                key_points = [{"content": str(key_points), "category": "general", "importance": 5}]
        
        return key_points
    
    except Exception as e:
        # Fall back to manual parsing if JSON parsing fails
        print(f"Error parsing key points JSON: {str(e)}")
        lines = response.strip().split("\n")
        key_points = []
        
        current_point = {}
        for line in lines:
            line = line.strip()
            if line.startswith(("- ", "* ", "Point ", "Key Point ")):
                # Save previous point if exists and start new one
                if current_point and "content" in current_point:
                    key_points.append(current_point)
                current_point = {"content": line.lstrip("- *").strip(), "category": "general", "importance": 5}
            elif ":" in line and not line.startswith("```"):
                # This might be a property of the current point
                parts = line.split(":", 1)
                key = parts[0].strip().lower()
                value = parts[1].strip()
                
                if key in ["category", "type", "topic"]:
                    current_point["category"] = value
                elif key in ["importance", "score", "weight"]:
                    try:
                        current_point["importance"] = int(value.split("/")[0])
                    except:
                        current_point["importance"] = 5
                elif key in ["section", "source", "from"]:
                    current_point["source_section"] = value
        
        # Add the last point
        if current_point and "content" in current_point:
            key_points.append(current_point)
        
        # If we couldn't parse any points, create some basic ones
        if not key_points:
            key_points = [
                {"content": "The paper could not be properly analyzed.", "category": "error", "importance": 1}
            ]
        
        return key_points

async def analyze_paper(
    paper_content: Dict[str, Any],
    analysis_type: str,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Perform custom analysis on a paper.
    
    Args:
        paper_content: Paper content dictionary
        analysis_type: Type of analysis to perform
        options: Additional options for the analysis
        
    Returns:
        Analysis results
    """
    options = options or {}
    
    # Get paper text
    text = paper_content.get("text", "")
    
    # Truncate if too long for context window
    if len(text) > 100000:
        text = text[:100000] + "... [text truncated due to length]"
    
    # Prepare system message
    system_message = "You are an expert academic research assistant with extensive knowledge across scientific domains."
    
    # Prepare prompt based on analysis type
    if analysis_type == "structure":
        prompt = f"""Analyze the structure of the following academic paper. 
Include information about:
- The overall organization
- Key sections and their purposes
- How well the paper follows standard academic structure
- Suggestions for structural improvements

Paper text:
{text}
"""
    
    elif analysis_type == "methodology":
        prompt = f"""Analyze the methodology used in the following academic paper.
Include information about:
- The research method(s) employed
- Data collection and analysis techniques
- Strengths and limitations of the methodology
- How the methodology aligns with the research questions/objectives

Paper text:
{text}
"""
    
    elif analysis_type == "results":
        prompt = f"""Analyze the results and findings of the following academic paper.
Include information about:
- The key results presented
- How results are interpreted by the authors
- The significance of the findings
- Any limitations or caveats mentioned
- How the results compare to prior work in the field

Paper text:
{text}
"""
    
    elif analysis_type == "references":
        prompt = f"""Analyze the references and citations in the following academic paper.
Include information about:
- The key sources cited
- How recent the citations are
- The diversity of sources
- Any notable gaps in the literature review
- How the paper builds on prior work

Paper text:
{text}
"""
    
    elif analysis_type == "custom":
        # For custom analysis, use the provided prompt in options
        custom_prompt = options.get("prompt", "Analyze the following academic paper:")
        prompt = f"""{custom_prompt}

Paper text:
{text}
"""
    
    else:
        # Default general analysis
        prompt = f"""Provide a comprehensive analysis of the following academic paper.
Include information about:
- The key research questions and objectives
- The methodology used
- The main findings and their significance
- Strengths and limitations of the work
- Potential implications and future directions

Paper text:
{text}
"""
    
    # Generate analysis
    analysis_text = await generate_text(
        prompt=prompt,
        temperature=0.4,
        system_message=system_message
    )
    
    # Return results
    return {
        "analysis_type": analysis_type,
        "text": analysis_text,
        "options": options
    }

async def generate_slide_content(
    paper_content: Dict[str, Any],
    max_slides: int = 10,
    focus_areas: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Generate content for presentation slides from a paper.
    
    Args:
        paper_content: Paper content dictionary
        max_slides: Maximum number of slides to generate
        focus_areas: Areas to focus on for the slides
        
    Returns:
        List of slide content objects
    """
    # Get paper text and basic info
    text = paper_content.get("text", "")
    
    # Truncate if too long for context window
    if len(text) > 50000:  # Use less text for slides than summary
        text = text[:50000] + "... [text truncated due to length]"
    
    # Extract the title from the paper text or default to "Unknown"
    title_match = re.search(r"^(.+?)(?:\n|$)", text.strip())
    title = title_match.group(1) if title_match else "Unknown Title"
    
    # Craft prompt
    focus_str = f", focusing on {', '.join(focus_areas)}" if focus_areas else ""
    
    prompt = f"""Create a presentation with {max_slides} slides based on the following academic paper{focus_str}.

For each slide, provide:
1. A slide title
2. Bullet points or key content for the slide
3. Optional speaker notes with additional details or talking points

The presentation should follow this general structure:
- Title slide with paper title and authors
- Introduction / Background
- Research Questions or Objectives
- Methodology
- Key Results (can be multiple slides if needed)
- Discussion of findings
- Conclusion and implications
- References (only key ones)

Make sure the content is concise and suitable for presentation slides.

Paper text:
{text}

Please format your response as a JSON array with objects containing 'title', 'content', 'notes', and 'layout' fields.
'content' should be an array of strings representing bullet points or paragraphs.
"""
    
    # Generate slides content
    response = await generate_text(
        prompt=prompt,
        temperature=0.4,
        max_tokens=4000,
        system_message="You are an expert at creating clear, concise, and engaging presentation slides from academic papers."
    )
    
    # Parse JSON response
    try:
        # Clean up response to ensure it only contains the JSON part
        json_text = response
        if "```json" in response:
            json_text = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_text = response.split("```")[1].split("```")[0].strip()
        
        slides = json.loads(json_text)
        
        # Validate and fix structure if needed
        if not isinstance(slides, list):
            raise ValueError("Slides output is not a list")
        
        # Add title slide if not present
        has_title_slide = False
        for slide in slides:
            if slide.get("layout") == "title" or "title" in slide.get("title", "").lower():
                has_title_slide = True
                break
        
        if not has_title_slide:
            slides.insert(0, {
                "title": title,
                "content": ["Academic Paper Presentation"],
                "notes": "Introduction to the paper and its key contributions",
                "layout": "title"
            })
        
        return slides
    
    except Exception as e:
        # Fall back to manual structure if JSON parsing fails
        print(f"Error parsing slides JSON: {str(e)}")
        
        # Create basic slides manually
        return [
            {
                "title": title,
                "content": ["Academic Paper Presentation"],
                "notes": "Introduction to the paper and its key contributions",
                "layout": "title"
            },
            {
                "title": "Introduction",
                "content": ["Background of the research", "Key context", "Research gap addressed"],
                "notes": "Provide context for the research and why it matters",
                "layout": "content"
            },
            {
                "title": "Methodology",
                "content": ["Research approach", "Data collection methods", "Analysis techniques"],
                "notes": "Explain how the research was conducted",
                "layout": "content"
            },
            {
                "title": "Key Findings",
                "content": ["Main result 1", "Main result 2", "Main result 3"],
                "notes": "Present the most important findings of the research",
                "layout": "content"
            },
            {
                "title": "Conclusion",
                "content": ["Summary of contributions", "Implications", "Future directions"],
                "notes": "Wrap up and explain why these findings matter",
                "layout": "content"
            }
        ]
