from typing import Dict

# Standard API key placeholders to check against
API_KEY_PLACEHOLDERS: Dict[str, str] = {
    "gemini_api_key": "YOUR_GEMINI_API_KEY",
    "openai_api_key": "YOUR_OPENAI_API_KEY",
    "azure_openai_api_key": "YOUR_AZURE_OPENAI_API_KEY",
    "azure_openai_endpoint": "YOUR_AZURE_OPENAI_ENDPOINT",
    "azure_openai_deployment": "YOUR_AZURE_OPENAI_DEPLOYMENT_NAME",
}

DEFAULT_SERVICE_ORDER = ["azure", "openai", "gemini"]

