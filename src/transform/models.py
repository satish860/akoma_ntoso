from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
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