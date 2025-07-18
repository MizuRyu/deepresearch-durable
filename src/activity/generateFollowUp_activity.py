from loguru import logger

from function_app import app

from ..core.prompts import FOLLOWUP_INSTRUCTIONS
from ..core.prompts import get_current_date
from ..core.llms import call_aoai

@app.function_name(name="generateFollowUp_activity")
@app.activity_trigger(input_name="question")
async def generateFollowUp_activity(question: str):
    logger.info(f"[generateFollowUp_activity] Start generating follow-up questions for: {question}")
    formatted_prompt = FOLLOWUP_INSTRUCTIONS.format(
        question=question
    )
    response = await call_aoai(
        system_prompt=formatted_prompt,
        prompt="ユーザーの質問を具体的にするフォローアップ質問を生成すること:"
    )
    logger.info(f"[generateFollowUp_activity] Response: {response}")
    logger.info(f"[generateFollowUp_activity] End Activity")
    return response


# python3 -m src.activity.generateFollowUp_activity
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    asyncio.run(generateFollowUp_activity("Durable Functions って何？"))
