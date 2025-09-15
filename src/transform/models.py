from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import date

class DocumentMetadata(BaseModel):
    """Structured metadata for legal documents"""
    document_type: str = Field(description="Type: regulation, act, directive, implementing regulation, delegated regulation")
    number: str = Field(description="Document number e.g., 2022/2554, 2024/1774")
    title: str = Field(description="Full title of the document")
    date_enacted: date = Field(description="Date when enacted (YYYY-MM-DD)")
    date_published: Optional[date] = Field(default=None, description="Publication date (YYYY-MM-DD)")
    authority: str = Field(description="Issuing authority")
    country: str = Field(description="Country/region code: eu, uk, us")
    language: str = Field(description="ISO language code: eng, fra, deu")
    official_journal: Optional[str] = Field(default=None, description="Official journal reference e.g., L 333/1")

class ValidationResult(BaseModel):
    """Result of metadata validation"""
    is_valid: bool = Field(description="Whether the extracted metadata is valid")
    corrections: Dict[str, Any] = Field(default_factory=dict, description="Fields that need correction")
    confidence: int = Field(ge=0, le=100, description="Confidence score 0-100")
    issues: Optional[str] = Field(default=None, description="Description of any issues found")

class PreambleLocation(BaseModel):
    """Location and content of regulation preamble"""
    start_line: int = Field(description="Line where REGULATION (EU) appears")
    end_line: int = Field(description="Last line before Whereas: or (1)")
    title: str = Field(description="Full title: REGULATION (EU) 2022/2554...")
    date: str = Field(description="Date from preamble: of 14 December 2022")
    legal_basis: List[str] = Field(default_factory=list, description="All Having regard to... statements")
    confidence: int = Field(ge=0, le=100, description="LLM confidence score")

class RecitalsLocation(BaseModel):
    """Location and content of regulation recitals"""
    start_line: int = Field(description="Line with Whereas:")
    end_line: int = Field(description="Line before HAVE ADOPTED THIS REGULATION")
    recital_count: int = Field(description="Number of recitals found")
    first_recital_line: int = Field(description="Line where (1) starts")
    last_recital_number: int = Field(description="Highest recital number e.g., 111")
    confidence: int = Field(ge=0, le=100, description="LLM confidence score")

class ChapterInfo(BaseModel):
    """Single chapter found in document"""
    chapter_number: str = Field(description="Roman numeral: I, II, III, IV")
    title: str = Field(description="Chapter title")
    start_line: int = Field(description="Line where CHAPTER appears")
    page_number: int = Field(description="Which page it was found on")
    confidence: int = Field(ge=0, le=100, description="LLM confidence score")

class ChaptersOnPage(BaseModel):
    """All chapters found on a single page"""
    page_number: int = Field(description="Page number")
    chapters: List[ChapterInfo] = Field(default_factory=list, description="Chapters found on this page")
    has_chapters: bool = Field(description="Whether any chapters were found")

