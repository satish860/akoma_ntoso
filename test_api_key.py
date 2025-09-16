import os
from dotenv import load_dotenv
import instructor
from openai import OpenAI

# Load environment variables
load_dotenv()

def test_api_key():
    """Test if OpenRouter API key is working"""
    api_key = os.getenv("OPENROUTER_API_KEY")

    print(f"API Key present: {'Yes' if api_key else 'No'}")
    if api_key:
        print(f"API Key length: {len(api_key)}")
        print(f"API Key starts with: {api_key[:10]}...")

    if not api_key:
        print("ERROR: No OPENROUTER_API_KEY found in environment")
        return False

    try:
        # Test API connection with regular OpenAI client (no instructor)
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )

        print("Testing API connection...")
        # Simple test call
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'API test successful'"}
            ],
            max_tokens=10
        )

        print(f"API Response: {response.choices[0].message.content}")
        print("[OK] API key is working!")
        return True

    except Exception as e:
        print(f"[ERROR] API Error: {e}")
        return False

if __name__ == "__main__":
    test_api_key()