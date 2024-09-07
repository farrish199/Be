import openai
import os
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Set up OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    logger.error("OpenAI API key is not set in environment variables.")
    exit(1)
openai.api_key = OPENAI_API_KEY

def generate_chatgpt_response(prompt: str, model: str = "gpt-3.5-turbo") -> str:
    """Generate a response from OpenAI's ChatGPT."""
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        logger.error(f"Error generating response from ChatGPT: {e}")
        return "Sorry, there was an error generating the response."

def extract_info_from_text(text: str) -> dict:
    """Extract information from text using OpenAI's API."""
    prompt = f"Extract the key information from the following text:\n\n{text}"
    response = generate_chatgpt_response(prompt)
    return {"extracted_info": response}
