"""
FIWARE Orion Client - API cơ bản
Chỉ chứa các hàm gọi HTTP thuần túy
"""

import os
import requests
from urllib.parse import quote

ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "cruzrtwin")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/asean/buildings")

# Headers mặc định
DEFAULT_HEADERS = {
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}


def get_headers(has_body: bool = False) -> dict:
    """Lấy headers cho request"""
    headers = DEFAULT_HEADERS.copy()
    if has_body:
        headers["Content-Type"] = "application/json"
    return headers


def get_orion_version() -> dict:
    """Lấy version của Orion"""
    response = requests.get(f"{ORION_URL}/version", timeout=10)
    return response.json() if response.status_code == 200 else None


def get_entities(params: dict = None) -> list:
    """GET /v2/entities"""
    response = requests.get(
        f"{ORION_URL}/v2/entities",
        params=params or {},
        headers=get_headers(),
        timeout=10
    )
    return response.json() if response.status_code == 200 else []


def get_entity(entity_id: str) -> dict:
    """GET /v2/entities/{id}"""
    encoded_id = quote(entity_id, safe="")
    response = requests.get(
        f"{ORION_URL}/v2/entities/{encoded_id}",
        headers=get_headers(),
        timeout=10
    )
    return response.json() if response.status_code == 200 else None


def create_entity(entity: dict) -> bool:
    """POST /v2/entities"""
    response = requests.post(
        f"{ORION_URL}/v2/entities",
        json=entity,
        headers=get_headers(has_body=True),
        timeout=10
    )
    return response.status_code in [200, 201, 204]


def update_entity_attrs(entity_id: str, attrs: dict) -> bool:
    """PATCH /v2/entities/{id}/attrs"""
    encoded_id = quote(entity_id, safe="")
    response = requests.patch(
        f"{ORION_URL}/v2/entities/{encoded_id}/attrs",
        json=attrs,
        headers=get_headers(has_body=True),
        timeout=10
    )
    return response.status_code in [200, 204]