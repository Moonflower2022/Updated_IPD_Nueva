from openai import OpenAI
from typing import List, Dict
from pydantic import BaseModel

from .prompts import single_strategy_prompt

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
        api_key="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",
    )

def get_response(client, chat_history: List[Dict[str, str]]) -> str:
    completion = client.chat.completions.create(
        model="nvidia/llama-3.1-nemotron-nano-vl-8b-v1",
        messages=chat_history,
        temperature=1.00,
        top_p=0.01,
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