# Akoma Ntoso Parser Library

## Project Overview
This project creates a Python library to convert PDF documents (Acts, Rules, Regulations) into Akoma Ntoso XML format. Starting with the DORA (Digital Operational Resilience Act) regulation as the primary test case.

## Requirements

### Core Functionality
- Parse PDF documents containing legal text (Acts, Rules, Regulations)
- Extract hierarchical structure (Chapters, Sections, Articles, Paragraphs)
- Generate valid Akoma Ntoso XML output
- Support incremental parsing with simple components

### Technical Stack
- Python with uv package manager
- PDF processing: `pdfplumber` or `pypdf2`
- XML generation: `lxml`
- Data models: `pydantic`
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

### Development Approach
1. Start with basic structure detection (Chapters, Articles)
2. Build hierarchical parsing capabilities
3. Generate valid Akoma Ntoso XML
4. Test with DORA regulation
5. Extend to handle more complex patterns

### Commands to Run
- Tests: Use real environment testing (no mocks)
- Python execution: Use `uv run` for all Python commands
- Linting/Type checking: TBD based on project setup

### Notes
- Focus on Windows PowerShell compatibility
- No emoji in code or comments
- Real environment testing preferred over mocks
- Current year: 2025, September