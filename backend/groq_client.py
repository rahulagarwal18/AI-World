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

        models_to_try = [self.model, "qwen/qwen3.6-27b", "allam-2-7b", "openai/gpt-oss-20b"]
        for current_model in models_to_try:
            retries = 0
            wait_time = 2
            while retries < 3:
                try:
                    kwargs = {
                        "model": current_model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 4096
                    }
                    if "qwen" not in current_model.lower():
                        kwargs["response_format"] = {"type": "json_object"}

                    response = self.client.chat.completions.create(**kwargs)
                    raw_content = response.choices[0].message.content or ""
                    
                    # Clean out <think>...</think> reasoning blocks if present
                    import re
                    raw_content = re.sub(r'<think>[\s\S]*?</think>', '', raw_content).strip()
                    
                    # Extract JSON object using regex
                    json_match = re.search(r'\{[\s\S]*\}', raw_content)
                    if json_match:
                        return json.loads(json_match.group(0))
                    return json.loads(raw_content)
                except Exception as e:
                    err_str = str(e).lower()
                    if "404" in err_str or "model_not_found" in err_str:
                        logger.warning(f"Model {current_model} not found, falling back...")
                        break
                    elif "429" in err_str or "rate limit" in err_str:
                        # Extract exact retry delay if provided by Groq (e.g. 8m15s or 14.9s)
                        delay = 10
                        import re
                        m_min = re.search(r"try again in (\d+)m(\d+\.?\d*)s", err_str)
                        m_sec = re.search(r"try again in (\d+\.?\d*)s", err_str)
                        if m_min:
                            delay = int(m_min.group(1)) * 60 + float(m_min.group(2)) + 1.0
                        elif m_sec:
                            delay = float(m_sec.group(1)) + 1.0
                        
                        # Cap max sleep inside cycle to 15 seconds to keep server responsive
                        sleep_time = min(delay, 15)
                        logger.warning(f"Groq Rate limit hit on {current_model}. Pausing {sleep_time}s...")
                        time.sleep(sleep_time)
                        retries += 1
                    else:
                        logger.error(f"Error calling Groq API ({current_model}): {e}")
                        break
        
        return {
            "action": "reflect",
            "thought": "Groq API rate limit paused. Auto-resuming continuous creation loop shortly..."
        }
