import logging
import os
import json
import azure.functions as func
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import requests

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Creating ChatKit session.')

    # Get environment variables
    # We use the same variables as ai-summary.py to ensure consistency
    # Try APIM endpoints first, fallback to direct Azure OpenAI
    api_key = os.environ.get("APIM_AOAI_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("APIM_AOAI_ENDPOINT") or os.environ.get("AZURE_OPENAI_V1_API_ENDPOINT")
    
    if not endpoint:
        return func.HttpResponse(
            "Missing configuration: APIM_AOAI_ENDPOINT or AZURE_OPENAI_V1_API_ENDPOINT",
            status_code=500
        )

    try:
        # Try to get a token using Azure Identity first
        # For OpenAI-compatible APIs, both tokens and API keys use Bearer authentication
        auth_token = None
        use_azure_identity = False
        try:
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            auth_token = token_provider()
            use_azure_identity = True
            logging.info("Using Azure Identity for authentication")
        except Exception as e:
            logging.warning(f"Azure Identity failed: {e}, falling back to API key")
            if api_key:
                auth_token = api_key
                logging.info("Using API key for authentication")
            else:
                return func.HttpResponse(
                    "Authentication failed: No Azure Identity and no API key available",
                    status_code=500
                )
        
        # Construct the URL for session creation
        # We assume endpoint is the base URL (e.g. https://my-proxy.com/v1)
        # and we append /chatkit/sessions
        base_url = endpoint.rstrip('/')
        session_url = f"{base_url}/chatkit/sessions"
        
        # For OpenAI-compatible APIs (including APIM), both OAuth tokens and API keys
        # use the same Bearer authentication scheme in the Authorization header
        headers = {
            "Authorization": f"Bearer {auth_token}",
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
