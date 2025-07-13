from loguru import logger

from function_app import app

from ..core.prompts import REFLECTION_INSTRUCTIONS
from ..core.llms import call_aoai_json_mode

@app.function_name(name="reflection_activity")
@app.activity_trigger(input_name="input")
async def reflection_activity(input: dict):
    logger.info(f"[reflection_activity] Start Activity")

    topic = input.get("topic", "Durable Functions って何？")
    followups = input.get("followups", "具体的にどんな情報をお探しですか？")
    followup_answer = input.get("followup_answer", "実装に関するベストプラクティスや実際の事例を知りたいです。")
    existing_summary = input.get("existing_summary", "")

    human_message_content = (
        "既存のKnowledgeを振り返り Knowledge Gap を洗い出し、"
        "次に実行すべき follow_up_query (英語) を JSON 形式で返してください。\n\n"
        "===\n"
        f"{existing_summary}"
    )

    formatted_prompt = REFLECTION_INSTRUCTIONS.format(
        research_topic=topic,
        lang="en",
        followups=followups,
        answer=followup_answer
    )
    logger.info(f"【reflection_activity】Formatted Prompt: {formatted_prompt}")
    response = await call_aoai_json_mode(
        system_prompt=formatted_prompt,
        prompt=human_message_content,
    )
    logger.info(f"【reflection_activity】Response: {response}")
    logger.info(f"[reflection_activity] End Activity")
    return response


# python3 -m src.activity.reflection_activity
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    existing_summary = """
        Durable Functionsは、Microsoft Azureの拡張機能で、サーバーレス環境で状態を持つワークフローを作成することを可能にします。これは、Azure Functionsの機能を拡張し、長時間実行されるワークフローを効率的に管理するためのものです。Durable Functionsは、Azure Storageを利用して状態、チェックポイント、実行履歴を管理し、これによりオーケストレーションが可能な長時間のプロセスをサポートします。
Durable Functionsの主な特長には、状態を保持できること、サーバーレスで自動スケーリングが可能であること、外部イベントに反応できることが含まれます。具体的には、オーケストレーター関数がワークフローのロジックを定義し、アクティビティ関数が個々のタスクを実行します。これにより、複雑なワークフローを段階的に構築し、外部イベントに基づいて処理を行うことができます。
Durable Functionsを使用する際のベストプラクティスとして、最新の拡張機能とSDKを使用し、関数の入力と出力を可能な限り小さく保つことが推奨されています。また、オーケストレーターコードにおいては決定論的APIを使用する必要があり、これにより再生時に同じ結果を生成できるように制約が設けられています。
このように、Durable Functionsは、長期的なワークフローの管理、状態の保持、複雑な処理のオーケストレーションをサポートする強力で柔軟なソリューションです。
    """

    test_input_data = {
        "topic": "Durable Functions って何？",
        "followups": "具体的にどんな情報をお探しですか？",
        "answer": "実装に関するベストプラクティスや実際の事例を知りたいです。",
        "existing_summary": existing_summary
    }

    asyncio.run(reflection_activity(test_input_data))
