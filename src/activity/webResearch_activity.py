import os
import json

from loguru import logger
from tavily import AsyncTavilyClient

from function_app import app
from ..helpers.deduplicate_and_format_sources import deduplicate_and_format_sources, format_sources

@app.function_name(name="webResearch_activity")
@app.activity_trigger(input_name="query")
async def webResearch_activity(query: str):
    logger.info("[WebResearch_activity] Start Activity")
    client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY", ""))

    search_results = await client.search(
        query=query,
        max_results=3,
        max_tokens_per_source=1000,
        include_raw_content=True,
        include_images=False, # FIXME: 一旦画像は取得しない
    )

    search_results_str = deduplicate_and_format_sources(
        search_results,
        max_tokens_per_source=10000,
        fetch_full_page=True,
    )

    sources = format_sources(
        search_results,
    )

    # TODO: 後で消す
    txt_path = os.path.join(os.getcwd(), f"{query}_formatted_sources.txt")
    with open(txt_path, "w", encoding="utf-8") as f_txt:
        f_txt.write(search_results_str)

    logger.info("[WebResearch_activity] End Activity")
    return search_results_str, sources

# python3 -m src.activity.webResearch_activity
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(webResearch_activity("durable functions Best Practices"))