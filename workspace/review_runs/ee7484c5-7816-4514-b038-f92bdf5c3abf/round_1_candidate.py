import os
from typing import Dict

def get_api_key() -> str:
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise EnvironmentError("API_KEY environment variable is not set.")
    return api_key

def get_headers() -> Dict[str, str]:
    return {"Authorization": f"Bearer {get_api_key()}"}