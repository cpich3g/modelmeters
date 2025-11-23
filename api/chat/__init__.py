import logging
import os
import json
import azure.functions as func
from openai import OpenAI
from azure.identity import DefaultAzureCredential, get_bearer_token_provider

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Processing chat request.')

    endpoint = os.environ.get("AZURE_OPENAI_V1_API_ENDPOINT")
    default_model = os.environ.get("AZURE_OPENAI_API_MODEL")

    if not endpoint or not default_model:
        return func.HttpResponse(
            "Missing configuration: AZURE_OPENAI_V1_API_ENDPOINT or AZURE_OPENAI_API_MODEL",
            status_code=500
        )

    try:
        req_body = req.get_json()
        messages = req_body.get("messages", [])
        model = req_body.get("model", default_model)
    except ValueError:
        return func.HttpResponse("Invalid JSON body", status_code=400)

    if not messages:
        return func.HttpResponse("No messages provided", status_code=400)

    # Construct input with history and system prompt
    system_prompt = """You are an AI assistant specialized in Microsoft Products and Services. 
Do not answer questions unrelated to Microsoft.
You can render rich widgets.
When listing models or products, ALWAYS use this JSON format wrapped in a markdown code block:
```json
{
  "type": "model-card",
  "title": "Recommended Models",
  "models": [
    { 
      "id": "model-id", 
      "name": "Model Name", 
      "price": "$0.00/1k", 
      "provider": "Provider", 
      "features": ["Feature1", "Feature2"] 
    }
  ]
}
```
Ensure the JSON is valid and complete.
"""
    
    # Build conversation history
    conversation_text = f"System: {system_prompt}\n"
    for msg in messages:
        role = msg.get('role', 'user').capitalize()
        content = msg.get('content', '')
        conversation_text += f"{role}: {content}\n"
    
    # The 'input' parameter for client.responses.create typically expects the *next* input or a prompt.
    # We'll pass the full conversation as the input context.

    try:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
        )

        client = OpenAI(
            base_url=endpoint,
            api_key=token_provider()
        )

        # Note: Azure Functions V1 (this model) does not support returning a generator (streaming) directly.
        # We must consume the stream and return the full body. 
        # The frontend is set up to handle NDJSON, so we will return the full NDJSON string.
        
        stream = client.responses.create(
            model=model,
            tools=[
                {
                    "type": "mcp",
                    "server_label": "microsoft_learn",
                    "server_description": "Microsoft Learn MCP server for searching and fetching Microsoft documentation.",
                    "server_url": "https://apim-yiaefkyinmgwy.azure-api.net/msdocs",
                    "require_approval": "never",
                },
            ],
            input=conversation_text,
            stream=True,
        )
        
        response_chunks = []
        for event in stream:
            # Filter for text deltas only to prevent tool calls from leaking into the chat
            if hasattr(event, 'type') and event.type == 'response.output_text.delta':
                if hasattr(event, 'model_dump_json'):
                    response_chunks.append(event.model_dump_json())
                else:
                    response_chunks.append(json.dumps(event))
            # We can also handle 'response.output_text.done' if needed, but delta is sufficient for content

        return func.HttpResponse(
            "\n".join(response_chunks),
            mimetype="application/x-ndjson",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error calling Azure OpenAI: {str(e)}")
        return func.HttpResponse(
            f"Error calling Azure OpenAI: {str(e)}",
            status_code=500
        )
