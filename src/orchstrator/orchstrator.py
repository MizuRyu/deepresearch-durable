import os
import azure.durable_functions as df

from datetime import timedelta
from loguru import logger

from function_app import app

from src.helpers.truncate import truncate_text

@app.function_name(name="deepResearch_orchestrator")
@app.orchestration_trigger(context_name="context")
def deepResearch_orchestrator(context: df.DurableOrchestrationContext):

    question = context.get_input()
    entity_id = df.EntityId("researchState_entity", context.instance_id)
    context.signal_entity(entity_id, "init", question)

    loop_count = 0
    MAX_LOOP_COUNT = 2

    # contextのGUIDを使うと、リプレイ時にも同じIDが使われる
    event_id = str(context.new_guid())

    followups = ""
    answer = ""
    # 1. フォローアップ生成
    if os.getenv("ENABLE_FOLLOWUP", "true").lower() == "true":
        followups = yield context.call_activity("generateFollowUp_activity", question)
        if followups:
            context.signal_entity(entity_id, "append_followups", followups)
            # UIにフォローアップ回答待機を通知
            context.set_custom_status({
                "type": "waiting_for_followup",
                "loopCount": loop_count,
                "data": {
                    "followups": followups,
                    "eventId": event_id
                }
            })
            # ユーザーのフォローアップ回答を待つ
            answer = yield context.wait_for_external_event(f"followup_response_{event_id}")
            context.signal_entity(entity_id, "append_followup_answer", answer)

    # 2. 検索クエリ生成
    queries = yield context.call_activity(
        "generateSearchQuery_activity",
        {
            "question": question,
            "followups": followups,
            "answer": answer
        }
    )
    context.signal_entity(entity_id, "append_queries", queries)
    context.set_custom_status({
        "type": "generate_query",
        "loopCount": loop_count,
        "data": {
            "queries": queries
        }
    })

    while True:
        state = yield context.call_entity(entity_id, "get")
        loop_count = state["loop_count"]
        if loop_count >= MAX_LOOP_COUNT:
            context.set_custom_status({
                "type": "routing",
                "loopCount": loop_count,
                "data": {
                    "decision": "finalize",
                    "reason": f"最大ループ数{MAX_LOOP_COUNT}に達したため"
                }
            })
            logger.info("Maximum loop count reached, finalizing.")
            break

        # 3. Web検索 (fan‑out/fan-in)
        parallel_tasks = [context.call_activity("webResearch_activity", item["query"]) for item in queries]
        web_research_results = yield context.task_all(parallel_tasks)
        
        for result, source in web_research_results:
            context.signal_entity(entity_id, "append_web_research_results", result)
            context.signal_entity(entity_id, "append_sources", source)

            context.set_custom_status({
                "type": "web_research",
                "loopCount": loop_count,
                "data": {
                    "researchResult": truncate_text(result),
                    "source": source
                }
            })

            state = yield context.call_entity(entity_id, "get")
            existing_summary = state["summaries"][-1] if state["summaries"] else ""

            # summarize: 各Web検索結果を要約
            updated_summary = yield context.call_activity(
                "contentSummarize_activity",
                {
                    "topic": question,
                    "existing_summary": existing_summary,
                    "recent_web_research_result": result
                }
            )

            context.set_custom_status({
                "type": "summarize",
                "loopCount": loop_count,
                "data": {
                    "updatedSummary": truncate_text(updated_summary)
                }
            })

            if not context.is_replaying:
                logger.info(f"Updated Summary: {updated_summary}")
            context.signal_entity(entity_id, "append_summaries", updated_summary)

        state = yield context.call_entity(entity_id, "get")
        existing_summary = state["summaries"][-1] if state["summaries"] else ""
        # reflection: 追加調査必要か
        reflection = yield context.call_activity(
            "reflection_activity",
            {
                "topic": state["question"],
                "followups": state["followups"],
                "followup_answer": state["followup_answer"],
                "existing_summary": existing_summary
            }
        )
        context.signal_entity(entity_id, "append_reflections", reflection)

        context.set_custom_status({
            "type": "reflection",
            "loopCount": loop_count,
            "data": {
                "query": reflection["follow_up_query"],
                "knowledgeGap": reflection["knowledge_gap"]
            }
        })

        yield context.create_timer(context.current_utc_datetime + timedelta(seconds=1.5))

        if not reflection["follow_up_query"]:
            context.set_custom_status({
                "type": "routing",
                "loopCount": loop_count,
                "data": {
                    "decision": "finalize",
                    "reason": "これ以上情報収集の必要がないため"
                }
            })
            logger.info("No follow-up query generated, finalizing.")
            break

        queries = [
            {
                "query": reflection["follow_up_query"]
            }
        ]

        context.set_custom_status({
            "type": "routing",
            "loopCount": loop_count,
            "data": {
                "decision": "continue",
                "reason": "ループ処理継続",
            }
        })
        context.signal_entity(entity_id, "increment_loop_count", loop_count + 1)


    # finalize: レポート生成
    state = yield context.call_entity(entity_id, "get")
    report = yield context.call_activity(
        "generateReport_activity",
        {
            "final_summary": state["summaries"][-1],
            "sources": state["sources"],
        }
    )
    context.signal_entity(entity_id, "finalize", report)

    context.set_custom_status({
        "type": "finalize",
        "data": {
            "finalSummary": truncate_text(state["summaries"][-1]),
        }
    })
    return report