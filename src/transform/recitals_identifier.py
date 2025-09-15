import instructor
from openai import OpenAI
import os
from dotenv import load_dotenv
from .models import RecitalsLocation

load_dotenv()

class RecitalsIdentifier:
    """LLM-based recitals identifier for EU regulations"""

    def __init__(self):
        """Initialize with OpenRouter client using GPT-5"""
        self.client = instructor.from_openai(
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        )
        self.model = "openai/gpt-5"

    def identify_recitals(self, numbered_text: str) -> RecitalsLocation:
        """
        Identify recitals location in numbered text from PDF.

        Args:
            numbered_text: Text with line numbers from extract_text_with_line_numbers()

        Returns:
            RecitalsLocation with exact line ranges and metadata
        """
        # Take lines 15-200 to find recitals section (after preamble)
        lines = numbered_text.split('\n')
        # Start from line 15 to skip preamble, take up to line 200 to find recitals boundaries
        sample_lines = lines[14:200]  # Lines 15-200
        sample_text = '\n'.join(sample_lines)

        return self.client.chat.completions.create(
            model=self.model,
            response_model=RecitalsLocation,
            messages=[
                {
                    "role": "system",
                    "content": """You are analyzing EU regulation text to identify the recitals section.

Recitals are the explanatory section that follows the preamble and includes:
1. "Whereas:" marker line
2. Numbered paragraphs starting with (1), (2), (3), etc.
3. Each recital explains reasoning and context for the regulation
4. Ends before "HAVE ADOPTED THIS REGULATION"

IMPORTANT:
- Return exact line numbers from the numbered text provided
- Count total number of recitals found
- Identify the first recital line where (1) appears
- Find the highest recital number (e.g., (111) for DORA)
- Be precise about where recitals end (before "HAVE ADOPTED")"""
                },
                {
                    "role": "user",
                    "content": f"""Find the recitals section in this numbered text from an EU regulation:

{sample_text}

Identify:
- start_line: Line number with "Whereas:"
- end_line: Last line of recitals (before "HAVE ADOPTED THIS REGULATION")
- recital_count: Total number of recitals
- first_recital_line: Line where (1) starts
- last_recital_number: Highest numbered recital (e.g., 111)
- confidence: Your confidence level (0-100)"""
                }
            ]
        )