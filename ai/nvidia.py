from openai import OpenAI
from typing import List, Dict, Any, Tuple
from ai.base_provider import BaseProvider

class NvidiaProvider(BaseProvider):
    def __init__(self, api_key: str, model: str = "meta/llama-3.3-70b-instruct"):
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key,
        )
        self.model = model

    def decide(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]]) -> Tuple[str, Any]:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools_schema if tools_schema else None,
            tool_choice="auto" if tools_schema else None
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            return "tool_call", msg
        return "text", msg.content
