# Authentication Configuration

This document explains how authentication works in the Model Meters project.

## Overview

The project supports two authentication methods for Azure OpenAI:

1. **Token-based authentication** (Recommended): Uses Azure Managed Identity via `DefaultAzureCredential`
2. **API Key authentication** (Fallback): Uses API keys directly

## Authentication Priority

### For `ai-summary.py` and GitHub Actions:

1. First tries Azure Identity (token-based authentication)
2. Falls back to API key if Azure Identity fails and an API key is available
3. Fails with error if neither method is available

### For Azure Functions (`api/chat` and `api/create_session`):

1. First tries Azure Identity (token-based authentication)
2. Falls back to API key if Azure Identity fails and an API key is available
3. Returns 500 error if neither method is available

## Environment Variables

### APIM Endpoints (Priority 1):
```
APIM_AOAI_KEY=<your-apim-key>
APIM_AOAI_ENDPOINT=https://your-apim.azure-api.net/aoaif/openai
AZURE_OPENAI_API_MODEL=<model-name>
```

### Direct Azure OpenAI Endpoints (Priority 2):
```
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_V1_API_ENDPOINT=https://your-resource.openai.azure.com/openai/v1
AZURE_OPENAI_API_MODEL=<model-name>
```

## Azure Resource Configuration

### When Key-Based Authentication is Disabled

If your Azure OpenAI resource has key-based authentication disabled:

1. The system will automatically use token-based authentication
2. Ensure the service principal or managed identity has appropriate permissions:
   - `Cognitive Services OpenAI User` role
   - `Cognitive Services User` role

### For GitHub Actions

When running in GitHub Actions, token-based authentication will only work if:
1. The workflow has appropriate Azure credentials configured
2. Using a self-hosted runner with managed identity, or
3. Using `azure/login` action to authenticate first

Without proper Azure credentials, GitHub Actions must use API keys.

### For Azure Functions

Azure Functions can use Managed Identity when:
1. System-assigned or user-assigned managed identity is enabled on the Function App
2. The identity has been granted appropriate Azure OpenAI permissions

## Troubleshooting

### Error: "Key based authentication is disabled for this resource"

This means your Azure OpenAI resource has API key authentication disabled. Solutions:

1. **Enable Azure Identity**: Ensure managed identity is configured and has permissions
2. **Re-enable Key Authentication**: In Azure Portal, re-enable key-based authentication on your Azure OpenAI resource

### Error: "Azure Identity not available and no API key provided"

This means:
1. The `azure-identity` Python package is not installed, AND
2. No API key environment variables are set

Solutions:
1. Install azure-identity: `pip install azure-identity`
2. Set API key environment variables

### Deployment 401 Error

The Azure Functions deployment 401 error is typically caused by:
1. Expired publish profile credentials
2. Invalid SCM credentials

Solution: Regenerate the publish profile in Azure Portal:
1. Go to your Function App in Azure Portal
2. Select "Get publish profile" from the Overview or Deployment Center
3. Update the `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` secret in GitHub

## Testing Authentication Locally

```bash
# Test with API key
export AZURE_OPENAI_API_KEY="your-key"
export AZURE_OPENAI_V1_API_ENDPOINT="https://your-resource.openai.azure.com/openai/v1"
export AZURE_OPENAI_API_MODEL="gpt-4"
python ai-summary.py --date 2025-01-01

# Test with Azure Identity (requires Azure login)
az login
python ai-summary.py --date 2025-01-01
```

## Best Practices

1. **Use token-based authentication in production** for better security
2. **Rotate API keys regularly** if using key-based authentication
3. **Use managed identities** for Azure Functions to avoid storing credentials
4. **Monitor authentication failures** in logs to detect issues early
