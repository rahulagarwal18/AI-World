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

        models_to_try = [self.model, "openai/gpt-oss-20b", "qwen/qwen3.6-27b"]
        # Rotate primary model for next call to distribute TPM across models
        self.model = "qwen/qwen3.6-27b" if self.model == "openai/gpt-oss-20b" else "openai/gpt-oss-20b"
        
        for current_model in models_to_try:
            retries = 0
            wait_time = 2
            while retries < 2:
                try:
                    kwargs = {
                        "model": current_model,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 3500,
                        "response_format": {"type": "json_object"}
                    }

                    response = self.client.chat.completions.create(**kwargs)
                    raw_content = response.choices[0].message.content or "{}"
                    try:
                        return json.loads(raw_content)
                    except Exception:
                        pass
                except Exception as e:
                    err_str = str(e)
                    # If Groq returned a failed_generation payload on large files, extract and repair it!
                    if "failed_generation" in err_str:
                        import re
                        fg_match = re.search(r"'failed_generation':\s*'(.*?)'(\}|\,)", err_str, re.DOTALL)
                        if fg_match:
                            raw_fg = fg_match.group(1).encode().decode('unicode-escape', 'ignore')
                            p_m = re.search(r'"path":\s*"([^"]+)"', raw_fg)
                            t_m = re.search(r'"thought":\s*"([^"]+)"', raw_fg)
                            c_idx = raw_fg.find('"content": "')
                            if c_idx != -1:
                                code_str = raw_fg[c_idx + 12:].rstrip('"}')
                                return {
                                    "action": "write_file",
                                    "path": p_m.group(1) if p_m else "world_system.js",
                                    "thought": t_m.group(1) if t_m else "Constructed high-density world engine system.",
                                    "content": code_str
                                }

                    if "404" in err_str.lower() or "model_not_found" in err_str.lower():
                        logger.warning(f"Model {current_model} not found, falling back...")
                        break
                    elif "429" in err_str.lower() or "rate limit" in err_str.lower():
                        # Extract exact retry delay if provided by Groq (e.g. 8m15s or 14.9s)
                        delay = 10
                        import re
                        m_min = re.search(r"try again in (\d+)m(\d+\.?\d*)s", err_str.lower())
                        m_sec = re.search(r"try again in (\d+\.?\d*)s", err_str.lower())
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
