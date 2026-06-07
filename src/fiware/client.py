import requests
from urllib.parse import quote
from src.common.config import (
    ORION_URL,
    FIWARE_SERVICE,
    FIWARE_SERVICE_PATH,
    ORION_TIMEOUT
)
from src.common.errors import OrionClientError

# Module-level in-memory cache for graceful offline/local fallback
offline_cache = {}

def get_headers(has_body: bool = False) -> dict:
    headers = {
        "Fiware-Service": FIWARE_SERVICE,
        "Fiware-ServicePath": FIWARE_SERVICE_PATH,
    }
    if has_body:
        headers["Content-Type"] = "application/json"
    return headers

def get_orion_version() -> dict:
    """Gets version from Orion Context Broker."""
    url = f"{ORION_URL}/version"
    try:
        response = requests.get(url, timeout=ORION_TIMEOUT)
        return response.json() if response.status_code == 200 else None
    except Exception:
        return None

def get_entities(params: dict = None) -> list:
    """GETs all or filtered entities."""
    url = f"{ORION_URL}/v2/entities"
    headers = get_headers(has_body=False)
    try:
        response = requests.get(url, params=params or {}, headers=headers, timeout=ORION_TIMEOUT)
        return response.json() if response.status_code == 200 else []
    except Exception:
        return []

def create_entity(entity: dict) -> bool:
    """POST /v2/entities"""
    entity_id = entity.get("id")
    offline_cache[entity_id] = dict(entity)
    url = f"{ORION_URL}/v2/entities"
    headers = get_headers(has_body=True)
    try:
        response = requests.post(url, json=entity, headers=headers, timeout=ORION_TIMEOUT)
        return response.status_code in [200, 201, 204]
    except Exception:
        return False

def upsert_entity(entity: dict) -> dict:
    """
    POST /v2/entities or PATCH attributes if duplicate.
    """
    entity_id = entity.get("id")
    offline_cache[entity_id] = dict(entity)
    url = f"{ORION_URL}/v2/entities"
    headers = get_headers(has_body=True)
    
    try:
        response = requests.post(url, json=entity, headers=headers, timeout=ORION_TIMEOUT)
        if response.status_code in [200, 201, 204]:
            return {
                "success": True,
                "status_code": response.status_code,
                "entity_id": entity_id,
                "error": None
            }
        elif response.status_code in [422, 409]:
            # Duplicate / Already exists, let's update attributes instead
            attrs = {k: v for k, v in entity.items() if k not in ["id", "type"]}
            return update_entity_attrs(entity_id, attrs)
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "entity_id": entity_id,
                "error": response.text
            }
    except requests.RequestException as e:
        return {
            "success": False,
            "status_code": 503,
            "entity_id": entity_id,
            "error": str(e)
        }

def get_entity(entity_id: str) -> dict:
    """
    GET /v2/entities/{id}
    """
    encoded_id = quote(entity_id, safe="")
    url = f"{ORION_URL}/v2/entities/{encoded_id}"
    headers = get_headers(has_body=False)
    
    try:
        response = requests.get(url, headers=headers, timeout=ORION_TIMEOUT)
        if response.status_code == 200:
            res_json = response.json()
            offline_cache[entity_id] = res_json
            return res_json
        elif response.status_code == 404:
            return None
        else:
            raise OrionClientError(f"Failed to fetch entity {entity_id}. Code: {response.status_code}, Msg: {response.text}")
    except requests.RequestException as e:
        if entity_id in offline_cache:
            return offline_cache[entity_id]
        raise OrionClientError(f"Connection error to Orion broker: {e}")

def update_entity_attrs(entity_id: str, attrs: dict) -> dict:
    """
    PATCH /v2/entities/{id}/attrs
    """
    encoded_id = quote(entity_id, safe="")
    url = f"{ORION_URL}/v2/entities/{encoded_id}/attrs"
    headers = get_headers(has_body=True)
    
    if entity_id in offline_cache:
        for k, v in attrs.items():
            offline_cache[entity_id][k] = v
            
    try:
        response = requests.patch(url, json=attrs, headers=headers, timeout=ORION_TIMEOUT)
        if response.status_code in [200, 204]:
            return {
                "success": True,
                "status_code": response.status_code,
                "entity_id": entity_id,
                "error": None
            }
        else:
            return {
                "success": False,
                "status_code": response.status_code,
                "entity_id": entity_id,
                "error": response.text
            }
    except requests.RequestException as e:
        return {
            "success": False,
            "status_code": 503,
            "entity_id": entity_id,
            "error": str(e)
        }