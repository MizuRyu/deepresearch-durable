
import azure.durable_functions as df
from loguru import logger

from function_app import app


def _append_unique(lst, items):
    for x in items:
        if x not in lst:
            lst.append(x)


@app.function_name(name="researchState_entity")
@app.entity_trigger(context_name="context")
def researchState_entity(context: df.DurableEntityContext):
    state = context.get_state(lambda: {
        "question": "",
        "followups": "",
        "followup_answer": "",
        "queries": [],
        "web_research_results": [],
        "sources": [],
        "summaries": [],
        "reflections": [],
        "report": "",
        "loop_count": 0
    })

    operation = context.operation_name
    data = context.get_input()
    logger.info(f"Entity op: {operation} data: {str(data)[:20]}")

    if operation == "init":
        state["question"] = data
    elif operation == "append_followups":
        state["followups"] = data
    elif operation == "append_followup_answer":
        state["followup_answer"] = data
    elif operation == "append_queries":
        items = data["queries"] if isinstance(data, dict) else data
        _append_unique(state["queries"], items)
    elif operation == "append_web_research_results":
        _append_unique(state["web_research_results"], [data])
    elif operation == "append_sources":
        _append_unique(state["sources"], data)
    elif operation == "append_summaries":
        _append_unique(state["summaries"], [data])
    elif operation == "append_reflections":
        _append_unique(state["reflections"], [data])
    elif operation == "finalize":
        state["report"] = data
    elif operation == "increment_loop_count":
        state["loop_count"] += 1
    elif operation == "get":
        context.set_result(state)
        pass  # no-op, just return
    else:
        logger.warning(f"Unknown operation {operation}")

    context.set_state(state)
    return state