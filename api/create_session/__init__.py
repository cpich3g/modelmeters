import logging
import os
import json
import azure.functions as func
from openai import AzureOpenAI

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Creating ChatKit session.')

    # Get environment variables
    # We use the same variables as ai-summary.py to ensure consistency
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_V1_API_ENDPOINT")
    
    if not api_key or not endpoint:
        return func.HttpResponse(
            "Missing configuration: AZURE_OPENAI_API_KEY or AZURE_OPENAI_V1_API_ENDPOINT",
            status_code=500
        )

    try:
        # Initialize the client pointing to the user's endpoint
        # We mimic the behavior of the OpenAI client in ai-summary.py
        import requests
        
        # Construct the URL for session creation
        # We assume endpoint is the base URL (e.g. https://my-proxy.com/v1)
        # and we append /chatkit/sessions
        base_url = endpoint.rstrip('/')
        session_url = f"{base_url}/chatkit/sessions"
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Forward the body from the client
        try:
            req_body = req.get_json()
        except ValueError:
            req_body = {}


        response = requests.post(session_url, headers=headers, json=req_body)
        
        if response.status_code != 200:
            logging.error(f"Upstream error: {response.status_code} - {response.text}")
            return func.HttpResponse(
                f"Upstream error: {response.text}",
                status_code=response.status_code
            )

        return func.HttpResponse(
            response.text,
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        logging.error(f"Error creating session: {str(e)}")
        return func.HttpResponse(
            f"Internal error: {str(e)}",
            status_code=500
        )
