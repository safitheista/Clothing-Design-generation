import openai

def validate_openai_api_key(api_key: str) -> bool:
    """Validate an OpenAI API key by making a test request."""
    try:
        # Create an OpenAI client with the given API key
        client = openai.OpenAI(api_key=api_key)
        
        # Make a simple test request (list available models)
        client.models.list()
        
        return True  # API key is valid
    except openai.OpenAIError:
        return False  # Invalid API key