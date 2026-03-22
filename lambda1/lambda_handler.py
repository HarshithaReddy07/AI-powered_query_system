import json
import boto3
import os
import uuid

# Bedrock Agent client
agent_client = boto3.client("bedrock-agent-runtime")

# Lambda invoke client
lambda_client = boto3.client("lambda")

AGENT_ID = os.environ["AGENT_ID"]
AGENT_ALIAS_ID = os.environ["AGENT_ALIAS_ID"]
LAMBDA2_NAME = os.environ["LAMBDA2_NAME"]


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        user_input = body.get("query")

        if not user_input:
            return response(400, {"error": "Query is required"})

        # Step 1 — Call Agent
        agent_result = call_bedrock_agent(user_input)

        if agent_result["status"] == "blocked":
            return response(403, agent_result)

        sql_query = agent_result["sql"]

        # Step 2 — Invoke Lambda 2
        lambda2_response = lambda_client.invoke(
            FunctionName=LAMBDA2_NAME,
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "query": sql_query
            })
        )

        lambda2_result = json.loads(
            lambda2_response["Payload"].read()
        )

        return response(200, {
            "status": "success",
            "generated_sql": sql_query,
            "data": lambda2_result
        })

    except Exception as e:
        import traceback
        print("FULL ERROR:", traceback.format_exc())
        return response(500, {"error": str(e)})


def call_bedrock_agent(user_input):

    session_id = str(uuid.uuid4())

    response_stream = agent_client.invoke_agent(
        agentId=AGENT_ID,
        agentAliasId=AGENT_ALIAS_ID,
        sessionId=session_id,
        inputText=user_input
    )

    full_response = ""

    for event in response_stream["completion"]:
        if "chunk" in event:
            full_response += event["chunk"]["bytes"].decode("utf-8")

    full_response = full_response.strip()

    if full_response.startswith("BLOCKED:"):
        return {
            "status": "blocked",
            "reason": full_response
        }

    if full_response.startswith("SAFE:"):
        return {
            "status": "safe",
            "sql": full_response.replace("SAFE:", "").strip()
        }

    raise Exception(f"Unexpected agent response: {full_response}")


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }
    
