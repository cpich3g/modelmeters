# Fix Summary: Authentication Errors

## Issues Fixed

### 1. Token Provider Authentication Bug in `ai-summary.py` ✅

**Problem**: The script was attempting token-based authentication but had inadequate error handling when falling back to API key authentication.

**Solution**: 
- Improved fallback logic to only use API key if available and token auth fails
- Added better error messages and logging
- Added check to ensure at least one auth method is available

**Impact**: The `create-ai-summaries.py` script should now work correctly with Azure resources that have key-based authentication disabled.

### 2. Token Provider Bug in `api/chat/__init__.py` ✅

**Problem**: The code was calling `token_provider()` to get a token string, but the OpenAI client expects a callable function.

**Solution**: Changed `api_key=token_provider()` to `api_key=token_provider`

**Impact**: The chat API function will now properly authenticate using Azure Identity.

### 3. Missing Azure Identity Support in `api/create_session/__init__.py` ✅

**Problem**: This function was only using API key authentication and didn't support token-based authentication.

**Solution**: 
- Added Azure Identity support with `get_bearer_token_provider`
- Implemented proper fallback to API key if token auth fails
- Added logging to track which authentication method is used

**Impact**: The session creation API will now work with token-based authentication.

### 4. Documentation ✅

**Added**: Comprehensive authentication documentation at `.github/AUTHENTICATION.md`

## Issues Requiring Manual Action

### Azure Functions Deployment 401 Error ❗

**Problem**: 
```
Error: Failed to fetch Kudu App Settings.
Unauthorized (CODE: 401)
```

**Root Cause**: The publish profile credentials in the `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` GitHub secret are expired or invalid.

**Solution Required** (User Action):
1. Go to Azure Portal
2. Navigate to your Function App: `model-meter-chat`
3. Click on "Get publish profile" (or "Download publish profile")
4. In GitHub repository settings:
   - Go to Settings → Secrets and variables → Actions
   - Update the `AZURE_FUNCTIONAPP_PUBLISH_PROFILE` secret with the new profile content
5. Re-run the deployment workflow

**Note**: This cannot be fixed through code changes. It requires Azure Portal configuration.

## Testing Recommendations

### 1. Test AI Summary Generation

After the fixes, test the AI summary generation:

```bash
# Set up environment variables (use your actual values)
export AZURE_OPENAI_V1_API_ENDPOINT="https://your-resource.openai.azure.com/openai/v1"
export AZURE_OPENAI_API_MODEL="gpt-4"

# For token-based auth (recommended)
az login
python ai-summary.py --date 2025-01-01

# For API key auth (fallback)
export AZURE_OPENAI_API_KEY="your-api-key"
python ai-summary.py --date 2025-01-01
```

### 2. Test Azure Functions Locally

```bash
cd api
pip install -r requirements.txt
func start
```

Then test the endpoints:
- POST http://localhost:7071/api/create_session
- POST http://localhost:7071/api/chat

### 3. Test GitHub Actions Workflow

1. First, update the publish profile secret as described above
2. Manually trigger the "Daily Data Update" workflow
3. Monitor the logs to ensure authentication works correctly

## Expected Outcomes

### For `create-ai-summaries.py`:
- ✅ Should successfully generate AI summaries using token-based authentication
- ✅ Falls back to API key if token auth fails
- ✅ Clear error messages if neither method works

### For Azure Functions:
- ✅ `chat` function uses token-based authentication
- ✅ `create_session` function uses token-based authentication
- ✅ Both fall back to API key if needed
- ❗ Deployment will succeed only after publish profile is updated

### For GitHub Actions:
- ✅ Daily data update workflow will use token-based auth if available
- ✅ Falls back to API key (current setup)
- ❗ Deployment workflow needs publish profile update to succeed

## Security Notes

✅ **CodeQL Security Scan**: PASSED - No security issues found

### Best Practices Applied:
1. Token-based authentication is prioritized over API keys
2. API keys are only used as fallback
3. Clear logging helps identify which auth method is being used
4. Sensitive credentials are not logged
5. Proper error handling prevents credential leakage

## Next Steps

1. **User Action Required**: Update Azure Functions publish profile secret
2. **Recommended**: Test the changes in a development environment first
3. **Recommended**: Enable Managed Identity for Azure Functions for better security
4. **Optional**: Consider disabling API key authentication once token-based auth is confirmed working

## Support

For issues or questions about these changes:
- Review `.github/AUTHENTICATION.md` for detailed authentication configuration
- Check Azure Function App logs for authentication errors
- Monitor GitHub Actions workflow logs for authentication status
