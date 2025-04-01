# Paper to Slides

A Python tool to automatically generate presentation slides from academic papers using LLMs (Large Language Models).

## Features

- Upload academic papers in PDF format
- Extract text and figures from papers
- Generate summaries and key points using LLMs
- Automatically create presentation slides
- Customize slide templates and styles

## Tech Stack

- FastAPI for the backend
- PyPDF2/pdfminer.six for PDF processing
- LLM integration (OpenAI API/Anthropic Claude)
- python-pptx for PowerPoint generation
- SQLite/PostgreSQL for data storage

## Getting Started

### Prerequisites

- Python 3.9+
- Poetry (optional, for dependency management)

### Installation

```bash
# Clone the repository
git clone https://github.com/takuyakubo/paper-to-slides.git
cd paper-to-slides

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Running the application

```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the API documentation.

## License

MIT
