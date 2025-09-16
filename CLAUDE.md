# Akoma Ntoso Parser Library

## Project Overview
This project creates a Python library to convert PDF documents (Acts, Rules, Regulations) into Akoma Ntoso XML format. Starting with the DORA (Digital Operational Resilience Act) regulation as the primary test case.

**Status: Complete ETL Pipeline Implemented**
- ✅ Extract: PDF text extraction with line numbers
- ✅ Transform: Hierarchical structure extraction (Chapters → Sections → Articles)
- ✅ Load: Complete Akoma Ntoso XML generation with full article content

## Current Implementation

### Completed Features
- **PDF Extraction**: Extract text with accurate line number mapping
- **Metadata Extraction**: Document metadata (title, date, authority, etc.)
- **Hierarchical Structure**: Complete extraction of Chapters, Sections, and Articles
- **Article Content**: Full article content extraction with paragraph structure
- **XML Generation**: Valid Akoma Ntoso XML with complete document hierarchy
- **Hybrid Approach**: LLM-based identification + pattern matching for accuracy

### Core Functionality
- Parse PDF documents containing legal text (Acts, Rules, Regulations)
- Extract hierarchical structure (Chapters, Sections, Articles, Paragraphs)
- Generate valid Akoma Ntoso XML output with full content
- Support incremental parsing with simple components

### Technical Stack
- Python with uv package manager
- PDF processing: `pdfplumber`
- XML generation: Native Python XML
- Data models: `pydantic`
- LLM integration: `instructor` with OpenRouter API
- Pattern matching: `regex`
- HTTP requests: `requests`

### Document Structure Support
The parser should handle common legal document patterns:
- **Preamble/Recitals** (background and rationale)
- **Hierarchical Structure**: Chapters → Sections → Articles → Paragraphs → Points/Subpoints
- **Article Components**: Number, title, paragraphs, sub-paragraphs with letters (a), (b), (c)
- **Cross-references**: Links to other articles, chapters, or external regulations
- **Definitions**: Usually in early articles
- **Annexes/Appendices**

### Test Data
- DORA Regulation (EU) 2022/2554 - Primary test case (stored in `data/` folder)
- Future: GDPR, CPC (Civil Procedure Code), and other regulations

### Architecture Goals
- Simple component-based design
- Incremental parsing approach
- Easy to extend for new document types
- Clear separation between PDF extraction, structure parsing, and XML generation

## Implementation Details

### Key Components
- **`src/pdf_extractor.py`**: PDF text extraction with line number mapping
- **`src/transform/metadata_extractor.py`**: Document metadata extraction using LLM
- **`src/transform/chapter_extractor.py`**: Chapter identification and content extraction
- **`src/transform/section_extractor.py`**: Section extraction within chapters
- **`src/transform/article_extractor.py`**: Article extraction using hybrid LLM + pattern matching
- **`src/transform/article_builder.py`**: Hierarchical XML generation with content parsing
- **`src/transform/models.py`**: Pydantic models for all document structures

### Current Results (DORA Regulation)
- **9 Chapters** extracted with full content
- **6 Sections** properly nested within chapters
- **64 Articles** with 100% accurate line numbers
- **Complete XML**: 57KB Akoma Ntoso XML with full article content
- **Hierarchical Nesting**: Articles under Sections when they exist, directly under Chapters otherwise

### Hybrid Extraction Approach
1. **LLM Identification**: Uses Instructor with GPT-4 to identify article titles and structure
2. **Pattern Matching**: Regex patterns for exact line number verification
3. **Content Extraction**: Line boundary-based content extraction from PDF
4. **Section Assignment**: Automated assignment based on line boundaries

### Commands to Run
- **Main ETL Pipeline**: `uv run main.py`
- **Article Extraction**: Uses `ArticleExtractor` class with OpenRouter API
- **XML Generation**: Outputs to `output/DORA_2022_2554_akoma_ntoso_with_content.xml`
- Tests: Use real environment testing (no mocks)
- Python execution: Use `uv run` for all Python commands

## Project Status & Next Steps

### Completed Milestones
- ✅ PDF extraction with line number accuracy
- ✅ Complete hierarchical structure extraction
- ✅ LLM-based article identification with 100% line number accuracy
- ✅ Full article content extraction and XML generation
- ✅ Production-ready ETL pipeline

### Potential Extensions
- Support for additional document types (GDPR, CPC, etc.)
- Enhanced paragraph structure parsing
- Cross-reference detection and linking
- Annexes and appendices support
- Multi-language document support

### Notes
- Focus on Windows PowerShell compatibility
- No emoji in code or comments
- Real environment testing preferred over mocks
- Current year: 2025, September
- Incremental updates preferred - this is an ETL pipeline: Extract from Acts → Transform → Load as Akoma Ntoso
- Clean, production-ready codebase with comprehensive documentation