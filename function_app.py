import azure.functions as func
import azure.durable_functions as df

from loguru import logger

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

# Register components
from src.orchstrator.orchstrator import deepResearch_orchestrator

from src.activity.generateFollowUp_activity import generateFollowUp_activity

from src.entity.researchState_entity import researchState_entity


# HTTPStart
@app.route(route="deepresearch", methods=["GET", "POST"])
@app.durable_client_input(client_name="client")
async def http_start(req: func.HttpRequest, client):
    question = req.params.get("question")
    if not question:
        return func.HttpResponse(
            " Question parameter is required.",
            status_code=400,
        )
    logger.info(f"Received question: {question}")
        
    payload = {
        "question": question,
    }
    
    instance_id = await client.start_new(
        "deepResearch_orchestrator",
        client_input=(payload)
    )

    logger.info(f"Started orchestration with ID = '{instance_id}'.")
    return client.create_check_status_response(req, instance_id)

