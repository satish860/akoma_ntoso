# Akoma Ntoso Parser Library

A Python library for converting PDF legal documents (Acts, Rules, Regulations) into Akoma Ntoso XML format.

## Overview

This project creates a parser that can extract structured information from PDF legal documents and convert them into machine-readable Akoma Ntoso XML format. Akoma Ntoso is an international OASIS standard for representing parliamentary, legislative, and judicial documents.

## Features

- **PDF to XML Conversion**: Extract text and structure from PDF legal documents
- **Hierarchical Parsing**: Identify chapters, sections, articles, and paragraphs
- **Akoma Ntoso Compliance**: Generate valid XML according to OASIS v1.0 standard
- **Simple Components**: Modular architecture for easy extension
- **Real Document Testing**: Uses actual regulations like DORA for testing

## Project Structure

```
akoma_ntoso/
├── data/                           # Sample PDF documents
│   └── DORA_Regulation_EU_2022_2554.pdf
├── AKOMA_NTOSO_GUIDE.md           # Comprehensive guide to Akoma Ntoso
├── CLAUDE.md                      # Project requirements and setup
├── README.md                      # This file
└── pyproject.toml                 # Python project configuration
```

## Test Documents

The project uses real regulatory documents for testing:

- **DORA Regulation (EU) 2022/2554**: Digital Operational Resilience Act - Primary test case
- **GDPR**: General Data Protection Regulation (planned)
- **CPC**: Civil Procedure Code (planned)

## Technology Stack

- **Python**: Core language with uv package manager
- **PDF Processing**: pdfplumber for text extraction
- **XML Generation**: lxml for Akoma Ntoso XML creation
- **Data Models**: pydantic for validation
- **Pattern Matching**: regex for structure detection

## What is Akoma Ntoso?

Akoma Ntoso ("linked hearts" in Akan language) is an XML standard that:

- Provides semantic markup for legal documents
- Enables machine-readable legal text processing
- Supports version tracking and cross-referencing
- Facilitates digital transformation of legal systems
- Used by governments and legal institutions worldwide

## Getting Started

### Prerequisites

- Python 3.8+
- uv package manager

### Installation

```powershell
# Clone the repository
git clone https://github.com/yourusername/akoma_ntoso.git
cd akoma_ntoso

# Install dependencies (when available)
uv sync
```

### Usage

```python
# Example usage (planned implementation)
from akoma_ntoso import AkomaNtosoParser

parser = AkomaNtosoParser()
xml_output = parser.convert_pdf_to_akn("data/DORA_Regulation_EU_2022_2554.pdf")
print(xml_output)
```

## Development Roadmap

### Phase 1: Foundation (Current)
- [x] Project setup with uv
- [x] Download test documents (DORA regulation)
- [x] Project documentation
- [ ] Basic PDF text extraction
- [ ] Simple structure detection

### Phase 2: Core Parsing
- [ ] Hierarchical document parsing
- [ ] Article and paragraph extraction
- [ ] Cross-reference detection
- [ ] Metadata extraction

### Phase 3: XML Generation
- [ ] Akoma Ntoso XML structure creation
- [ ] FRBR metadata generation
- [ ] Schema validation
- [ ] Quality assurance

### Phase 4: Enhancement
- [ ] Support for additional document types
- [ ] Performance optimization
- [ ] Extended testing with more regulations

## Contributing

This project focuses on:
- Real environment testing (no mocks)
- Windows PowerShell compatibility
- Simple, extensible component design
- Comprehensive documentation

## Resources

- [Akoma Ntoso Official Standard](https://www.oasis-open.org/standard/akn-v1-0/)
- [DORA Regulation Text](https://eur-lex.europa.eu/eli/reg/2022/2554/oj/eng)
- [Project Guide](./AKOMA_NTOSO_GUIDE.md)

## License

MIT License - see LICENSE file for details

## Status

🚧 **In Development** - This project is in early development phase. Core functionality is being implemented.

---

*This project aims to bridge the gap between traditional PDF legal documents and modern structured data formats, enabling better legal document processing and analysis.*