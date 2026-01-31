import os
import logging
import json
from openai import OpenAI

class LLMInterface:
    """
    LLM interface using the OpenAI library, compatible with DeepSeek API.
    """
    def __init__(self, config):
        self.config = config
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        if not self.api_key:
            logging.warning("DEEPSEEK_API_KEY not found. LLMInterface will not work.")
            self.client = None
        else:
            self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        logging.info("Initialized LLMInterface.")

    def query_llm(self, prompt: str, context: dict) -> dict:
        """
        Sends a proposal request to the LLM.
        """
        if not self.client:
            logging.error("LLM client not initialized.")
            return None

        full_prompt = f"{prompt}\n\nContext:\n{context}"
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-coder",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that provides trading strategy parameters in JSON format."},
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=500,
                temperature=0.7,
            )
            return self.parse_json_response(response.choices[0].message.content)
        except Exception as e:
            logging.error(f"Error querying LLM API: {e}")
            return None

    def parse_json_response(self, response_content: str) -> dict:
        """
        Parses the JSON response from the LLM.
        """
        try:
            return json.loads(response_content)
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse JSON response from LLM: {e}")
            return None
