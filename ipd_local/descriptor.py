from openai import OpenAI
from typing import List, Dict
from pydantic import BaseModel

from .prompts import single_strategy_prompt

from .game_specs import NVIDIA_API_KEY

class SummaryResponse(BaseModel):
    summary5: str
    summary40: str

client = None

def get_single_strategy_prompt(noise: bool, strategy_code: str) -> str:
    noise_str = "\n  - how the strategy handles noise\n" if noise else ""
    return single_strategy_prompt.format(noise_str=noise_str, strategy_code=strategy_code)

def get_client():
    return OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NVIDIA_API_KEY,
    )

def get_response(client, chat_history: List[Dict[str, str]]) -> str:
    completion = client.chat.completions.create(
        model="meta/llama-3.1-70b-instruct",
        messages=chat_history,
        temperature=0.2,
        top_p=0.7,
        max_tokens=1024,
        extra_body={"nvext": {"guided_repsonse": {
          "name": "summary_response",
          "json_schema": SummaryResponse.model_json_schema(),
        }}},
        stream=False,
    )
    return completion.choices[0].message.content

def describe_strategy(noise: bool, strategy_code: str) -> str:
    client = get_client()
    response = get_response(client, [{"role": "user", "content": get_single_strategy_prompt(noise, strategy_code)}])
    return response