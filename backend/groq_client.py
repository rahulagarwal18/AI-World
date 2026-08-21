import time
import json
import os
import logging
from typing import Dict, Any, List, Optional
from groq import Groq
from backend.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GroqEngine")

class GroqEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "").strip() or Config.GROQ_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {e}")
        else:
            logger.warning("GROQ_API_KEY environment variable is not set.")

        self.model = Config.MODEL_NAME

    def generate_action(self, system_prompt: str, user_context: str) -> Dict[str, Any]:
        """
        Queries Groq API expecting a structured JSON action object with exponential backoff on 429 rate limits.
        """
        if not self.client:
            self.api_key = os.getenv("GROQ_API_KEY", "").strip() or Config.GROQ_API_KEY
            if self.api_key:
                try:
                    self.client = Groq(api_key=self.api_key)
                except Exception:
                    pass
            if not self.client:
                return {
                    "action": "reflect",
                    "thought": "GROQ_API_KEY environment variable is missing on server. Awaiting key configuration."
                }

        retries = 0
        wait_time = 2

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_context}
        ]

        while retries < 8:
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    response_format={"type": "json_object"},
                    temperature=0.7,
                    max_tokens=4096
                )
                raw_content = response.choices[0].message.content
                return json.loads(raw_content)
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "rate limit" in err_str:
                    logger.warning(f"Groq Rate limit hit. Retrying in {wait_time}s... (Attempt {retries+1})")
                    time.sleep(wait_time)
                    wait_time = min(wait_time * 2, 60)
                    retries += 1
                else:
                    logger.error(f"Error calling Groq API: {e}")
                    return {
                        "action": "reflect",
                        "thought": f"Groq API error: {str(e)}"
                    }
        
        return {
            "action": "reflect",
            "thought": "Exceeded maximum retries for Groq API calls due to rate limits."
        }
