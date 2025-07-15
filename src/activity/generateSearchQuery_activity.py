from loguru import logger

from function_app import app

from ..core.prompts import QUERY_WRITER_INSTRUCTIONS
from ..core.prompts import get_current_date, build_clarify_exchange
from ..core.llms import call_aoai_json_mode

@app.function_name(name="generateSearchQuery_activity")
@app.activity_trigger(input_name="input")
async def generateSearchQuery_activity(input: dict):
    logger.info(f"[generateSearchQuery_activity] Start Activity")

    topic = input.get("question", "")
    followups = input.get("followups", "")
    answer = input.get("answer", "")

    clarify_exchange = build_clarify_exchange(followups, answer) if followups else ""

    formatted_prompt = QUERY_WRITER_INSTRUCTIONS.format(
        current_date=get_current_date(),
        lang="ja", # FIXME: ENV
        max_queries=5, # FIXME: ENV
        clarify_exchange=clarify_exchange,
        answer=answer,
        research_topic=topic
    )
    response = await call_aoai_json_mode(
        system_prompt=formatted_prompt,
        prompt="Web検索を行うためのクエリを生成すること:"
    )
    logger.info(f"[generateSearchQuery_activity] Response: {response}")
    response = response.get("queries", [])
    
    logger.info(f"[generateSearchQuery_activity] End Activity")
    return response


# python3 -m src.activity.generateSearchQuery_activity
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    test_input_data = {
        "question": "Durable Functions って何？",
        "followups": "具体的にどんな情報をお探しですか？",
        "answer": "実装に関するベストプラクティスや実際の事例を知りたいです。"
    }

    asyncio.run(generateSearchQuery_activity(test_input_data))
