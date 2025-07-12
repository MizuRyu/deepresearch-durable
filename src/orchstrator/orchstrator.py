import azure.durable_functions as df

from loguru import logger

from function_app import app

@app.function_name(name="deepResearch_orchestrator")
@app.orchestration_trigger(context_name="context")
def deepResearch_orchestrator(context: df.DurableOrchestrationContext):

    question = context.get_input()
    entity_id = df.EntityId("researchState_entity", context.instance_id)
    context.signal_entity(entity_id, "init", question)

    # 1. フォローアップ生成
    followups = yield context.call_activity("generateFollowUp_activity", question)
    if followups:
        context.signal_entity(entity_id, "append_followups", followups)
    if not context.is_replaying:
        logger.info(f"Follow-ups: {followups}")
    return followups