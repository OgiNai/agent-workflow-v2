from typing import Dict, Any

def normalize_user_data(data: Dict[str, Any]) -> Dict[str, str]:
    """Normalizes user or admin data by stripping and lowercasing fields."""
    return {
        "name": str(data.get("name", "")).strip().lower(),
        "email": str(data.get("email", "")).strip().lower(),
    }

def process_user(user: Dict[str, Any]) -> Dict[str, str]:
    return normalize_user_data(user)

def process_admin(admin: Dict[str, Any]) -> Dict[str, str]:
    return normalize_user_data(admin)