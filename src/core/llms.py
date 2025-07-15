import os
import json

from loguru import logger
from azure.core.credentials import AzureKeyCredential
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage


# gpt-4.1-nano
async def call_aoai(system_prompt, prompt):
    logger.info(f"[call_aoai] Start Calling AOAI with prompt...")
    async with ChatCompletionsClient(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        credential=AzureKeyCredential(os.getenv("AZURE_OPENAI_API_KEY", ""))
    ) as aoai_client:
        response = await aoai_client.complete(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(content=prompt)
            ],
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-nano"),
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        usage_total_token = response.usage.total_tokens if response.usage else 0
        logger.info(f"[call_aoai] Successfully called AOAI. System Prompt: {system_prompt[:20]} Total tokens: {usage_total_token}")
        return response.choices[0].message.content


# gpt-4.1-nano json output
async def call_aoai_json_mode(system_prompt, prompt):
    logger.info(f"[call_aoai_json_mode] Start Calling AOAI Json Mode with prompt...")
    async with ChatCompletionsClient(
        endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        credential=AzureKeyCredential(os.getenv("AZURE_OPENAI_API_KEY", ""))
    ) as aoai_client:
        response = await aoai_client.complete(
            messages=[
                SystemMessage(content=system_prompt),
                UserMessage(content=prompt)
            ],
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1-nano"),
            max_tokens=1000,
            temperature=0.7,
            top_p=0.9,
            frequency_penalty=0.0,
            presence_penalty=0.0,
            response_format="json_object"
        )
        usage_total_token = response.usage.total_tokens if response.usage else 0
        logger.info(f"[call_aoai_json_mode] Successfully called AOAI in JSON mode. System Prompt: {system_prompt[:20]} Total tokens: {usage_total_token}")

        try:
            parsed_response = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            logger.error(f"[call_aoai_json_mode] JSON decoding error: {e}")
            logger.error(f"Response content: {response.choices[0].message.content}")
            raise
        return parsed_response

# # 4o-mini
# async def call_aoai_reasoning(system_prompt, prompt):

# # 4o-mini json output
# async def call_aoai_reasoning_json_mode(system_prompt, prompt):


# python3 -m src.core.llms
if __name__ == "__main__":
    import asyncio
    
    from dotenv import load_dotenv

    load_dotenv()
    system_prompt = "You are a helpful assistant."
    prompt = "What is the capital of France? JSONで出力して"
    response = asyncio.run(call_aoai_json_mode(system_prompt, prompt))
    print(response)