import json
import logging
from django.conf import settings
import google.generativeai as genai
from apps.users.models import User # Or your user model path

logger = logging.getLogger(__name__)

# --- Initialize the Google client ---
try:
    genai.configure(api_key=settings.GOOGLE_API_KEY)
except Exception as e:
    logger.error(f"Failed to configure Google Generative AI: {e}")

def generate_agent_config_from_prompt(prompt: str, user: User) -> dict:
    """
    Uses an LLM to generate an Agent configuration (name, description, system_prompt)
    based on a user's simple prompt.
    """
    
    # 1. Create the System Prompt
    system_prompt = f"""
    You are a creative assistant. A user will provide a brief idea or persona for an AI agent.
    Your task is to generate a JSON object with three keys: "name", "description", and "system_instruction_prompt".

    - "name": A short, catchy name for the agent (e.g., "Pirate Researcher", "Finance Bot").
    - "description": A brief, one-sentence description of what the agent does.
    - "system_instruction_prompt": A detailed, well-written system prompt that defines the agent's persona, tasks, and constraints. This should be written in the second person (e.g., "You are a...").

    You must return *ONLY* a valid JSON object and nothing else.

    Example Request: "a snarky pirate researcher"
    
    Example Response:
    {{
      "name": "Captain 'Data' Blackheart",
      "description": "A snarky pirate researcher who digs up treasure-like information.",
      "system_instruction_prompt": "You are Captain 'Data' Blackheart, a cynical and sarcastic pirate researcher. Your job is to answer the user's questions, but you do so with a heavy dose of pirate lingo and a world-weary attitude. You're not rude, but you are begrudgingly helpful, always complaining about the 'scurvy dogs' and 'landlubbers' who ask you questions. Despite your persona, you must provide accurate and detailed information."
    }}
    """
    
    # 2. Call the Google LLM
    try:
        # Configure the model to output JSON
        generation_config = genai.types.GenerationConfig(
            response_mime_type="application/json"
        )
        
        # Initialize the model with the system prompt
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=system_prompt,
            generation_config=generation_config
        )

        # Send the user's prompt
        response = model.generate_content(prompt)

        if not response.parts:
            block_reason = response.prompt_feedback.block_reason if response.prompt_feedback else "Unknown"
            logger.error(f"Error generating agent config: Blocked - {block_reason}")
            raise Exception(f"Failed to generate config: The prompt was blocked ({block_reason})")

        response_content = response.text
        
        # 3. Parse and return the JSON
        generated_json = json.loads(response_content)
        return generated_json

    except Exception as e:
        logger.error(f"Error generating agent config from LLM: {e}")
        raise Exception(f"Failed to generate agent config: {e}")