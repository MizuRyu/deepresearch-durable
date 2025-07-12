
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
        "followups": [],
        "queries": [],
        "urls": [],
        "summaries": [],
        "answer": ""
    })

    operation = context.operation_name
    data = context.get_input()
    logger.info(f"Entity op: {operation} data: {str(data)[:120]}")

    if operation == "init":
        state["question"] = data
    elif operation == "append_followups":
        _append_unique(state["followups"], data)
    elif operation == "append_queries":
        _append_unique(state["queries"], data)
    elif operation == "append_urls":
        _append_unique(state["urls"], data)
    elif operation == "append_summary":
        state["summaries"].append(data)
    elif operation == "finalize":
        state["answer"] = data
    elif operation == "get":
        pass  # no-op, just return
    else:
        logger.warning(f"Unknown operation {operation}")

    context.set_state(state)
    return state