import azure.durable_functions as df
from datetime import timedelta
from loguru import logger

from function_app import app

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

    # 1. フォローアップ生成
    followups = yield context.call_activity("generateFollowUp_activity", question)
    if followups:
        context.signal_entity(entity_id, "append_followups", followups)
    if not context.is_replaying:
        logger.info(f"Follow-ups: {followups}")

    # 外部イベント（ユーザー承認ワークフロー）
    # context.set_custom_status({
    #     "custom_status": "waiting_for_followup",
    #     "followup": followup,
    #     "eventId": event_id
    # })
    # answer = yield context.wait_for_external_event(
    #     name=f"followup_response_{event_id}"
    # )
    
    # logger.info(f"[DeepResearch Orchestrator] Received follow-up response: {answer}")

    # 2. 検索クエリ生成
    answer = "実装に関するベストプラクティスや実際の事例を知りたいです。" #FIXME
    context.signal_entity(entity_id, "append_followup_answer", answer)
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
        "step": "generate_query", 
        "loop_count": loop_count,
        "queries": queries,
    })

    while True:
        state = yield context.call_entity(entity_id, "get")
        loop_count = state["loop_count"]
        if loop_count >= MAX_LOOP_COUNT:
            logger.info("Maximum loop count reached, finalizing.")
            break

        # 3. Web検索 (fan‑out/fan-in)
        parallel_tasks = [context.call_activity("webResearch_activity", item["query"]) for item in queries]
        web_research_results = yield context.task_all(parallel_tasks)

        context.set_custom_status({
            "step": "web_research", 
            "loop_count": loop_count
        })
        
        for result, source in web_research_results:
            context.signal_entity(entity_id, "append_web_research_results", result)
            context.signal_entity(entity_id, "append_sources", source)

            state = yield context.call_entity(entity_id, "get")
            existing_summary = state["summaries"][-1] if state["summaries"] else ""

            # summarize
            updated_summary = yield context.call_activity(
                "contentSummarize_activity",
                {
                    "topic": question,
                    "existing_summary": existing_summary,
                    "recent_web_research_result": result
                }
            )
            if not context.is_replaying:
                logger.info(f"Updated Summary: {updated_summary}")
            context.signal_entity(entity_id, "append_summaries", updated_summary)

        state = yield context.call_entity(entity_id, "get")
        existing_summary = state["summaries"][-1] if state["summaries"] else ""
        # reflection
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
            "step": "reflection", 
            "loop_count": loop_count,
            "query": reflection["follow_up_query"],
            "knowledge_gap": reflection["knowledge_gap"]
        })

        if not reflection["follow_up_query"]:
            break

        queries = [
            {
                "query": reflection["follow_up_query"]
            }
        ]
        context.signal_entity(entity_id, "increment_loop_count", loop_count + 1)
    
    # 4. レポート生成
    state = yield context.call_entity(entity_id, "get")
    context.set_custom_status({
        "step": "filalize",
        "final_summary": state["summaries"][-1],
        "sources": state["sources"],
    })
    report = yield context.call_activity(
        "generateReport_activity",
        {
            "final_summary": state["summaries"][-1],
            "sources": state["sources"],
        }
    )
    context.signal_entity(entity_id, "finalize", report)
    
    return report