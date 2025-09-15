import instructor
from openai import OpenAI
import os
from dotenv import load_dotenv
from .models import PreambleLocation

load_dotenv()

class PreambleIdentifier:
    """LLM-based preamble identifier for EU regulations"""

    def __init__(self):
        """Initialize with OpenRouter client using GPT-5"""
        self.client = instructor.from_openai(
            OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        )
        self.model = "openai/gpt-5"

    def identify_preamble(self, numbered_text: str) -> PreambleLocation:
        """
        Identify preamble location in numbered text from PDF.

        Args:
            numbered_text: Text with line numbers from extract_text_with_line_numbers()

        Returns:
            PreambleLocation with exact line ranges and content
        """
        # Take first 200 lines to find preamble
        lines = numbered_text.split('\n')[:200]
        sample_text = '\n'.join(lines)

        return self.client.chat.completions.create(
            model=self.model,
            response_model=PreambleLocation,
            messages=[
                {
                    "role": "system",
                    "content": """You are analyzing EU regulation text to identify the preamble section.

The preamble is the introductory section that includes:
1. Title starting with "REGULATION (EU)" or similar
2. Date of enactment
3. Subject matter description
4. Multiple "Having regard to..." legal basis statements
5. "Acting in accordance with..." statement

The preamble ENDS right before recitals begin (marked by "Whereas:" or numbered "(1)").

IMPORTANT:
- Return exact line numbers from the numbered text provided
- Extract the complete title and date exactly as written
- Capture ALL "Having regard to" statements found
- Be precise about where preamble ends (before recitals start)"""
                },
                {
                    "role": "user",
                    "content": f"""Find the preamble section in this numbered text from an EU regulation:

{sample_text}

Identify:
- start_line: Line number where regulation title begins
- end_line: Last line of preamble (before recitals/Whereas)
- title: Complete regulation title
- date: Date from the preamble
- legal_basis: All "Having regard to..." statements
- confidence: Your confidence level (0-100)"""
                }
            ]
        )