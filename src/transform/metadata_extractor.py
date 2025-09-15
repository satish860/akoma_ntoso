import instructor
from openai import OpenAI
from typing import Dict, Any
import os
from dotenv import load_dotenv
from .models import DocumentMetadata, ValidationResult

load_dotenv()

class MetadataExtractor:
    """Multi-LLM metadata extractor with self-validation using OpenRouter and GPT-4"""

    def __init__(self):
        """Initialize with OpenRouter client using GPT-4"""
        self.client = instructor.from_openai(
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        )
        self.extraction_model = "openai/gpt-5"
        self.validation_model = "openai/gpt-5"

    def extract_metadata(self, text: str) -> DocumentMetadata:
        """Step 1: Extract metadata using GPT-4 with structured output"""
        return self.client.chat.completions.create(
            model=self.extraction_model,
            response_model=DocumentMetadata,
            messages=[
                {
                    "role": "system",
                    "content": """Extract metadata from legal documents accurately.
                    For EU documents: country should be 'eu', language typically 'eng'.
                    Document types: regulation, act, directive, implementing regulation, delegated regulation.
                    Parse dates carefully (format as YYYY-MM-DD).

                    IMPORTANT for title field: Extract the COMPLETE title including the document type and number.
                    For example: "Regulation (EU) 2022/2554 on digital operational resilience..."
                    NOT just: "on digital operational resilience..." """
                },
                {
                    "role": "user",
                    "content": f"Extract metadata from this legal document:\n\n{text[:2000]}"
                }
            ]
        )

    def validate_metadata(self, text: str, metadata: DocumentMetadata) -> ValidationResult:
        """Step 2: Validate extracted metadata with GPT-4"""
        validation_prompt = f"""
        Verify if this metadata extraction is correct by checking against the original text.

        Original text excerpt:
        {text[:1500]}

        Extracted metadata:
        - Document Type: {metadata.document_type}
        - Number: {metadata.number}
        - Title: {metadata.title}
        - Date Enacted: {metadata.date_enacted}
        - Authority: {metadata.authority}
        - Country: {metadata.country}
        - Language: {metadata.language}

        Check for accuracy and provide corrections if needed.
        Give confidence score based on how certain you are.
        """

        return self.client.chat.completions.create(
            model=self.validation_model,
            response_model=ValidationResult,
            messages=[
                {
                    "role": "system",
                    "content": "Validate metadata extraction accuracy. Be strict and provide corrections if anything is wrong."
                },
                {
                    "role": "user",
                    "content": validation_prompt
                }
            ]
        )

    def refine_metadata(self, metadata: DocumentMetadata, validation: ValidationResult) -> DocumentMetadata:
        """Step 3: Apply corrections if needed"""
        if not validation.is_valid and validation.corrections:
            # Apply corrections to metadata
            updated_data = metadata.model_dump()
            updated_data.update(validation.corrections)
            return DocumentMetadata(**updated_data)
        return metadata

    def extract_with_validation(self, text: str) -> tuple[DocumentMetadata, ValidationResult]:
        """Complete pipeline: extract → validate → refine"""
        # Step 1: Extract
        metadata = self.extract_metadata(text)

        # Step 2: Validate
        validation = self.validate_metadata(text, metadata)

        # Step 3: Refine if needed
        if not validation.is_valid:
            metadata = self.refine_metadata(metadata, validation)

        return metadata, validation