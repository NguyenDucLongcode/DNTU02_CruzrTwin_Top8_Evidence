"""
Quản lý subscription trong Orion
Đăng ký webhook để nhận thông báo khi DEVICE thay đổi
Sau đó aggregator cập nhật Room entity
"""

import os
import requests

ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")
FIWARE_SERVICE = os.getenv("FIWARE_SERVICE", "cruzrtwin")
FIWARE_SERVICE_PATH = os.getenv("FIWARE_SERVICE_PATH", "/asean/buildings")

# Headers cho FIWARE
FIWARE_HEADERS = {
    "Content-Type": "application/json",
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}

FIWARE_READ_HEADERS = {
    "Fiware-Service": FIWARE_SERVICE,
    "Fiware-ServicePath": FIWARE_SERVICE_PATH,
}

# Webhook URL (aggregator server)
# When Orion runs in Docker on Windows, use host.docker.internal so the container
# can reach a webhook server running on the host machine. Allow override via env.
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "http://host.docker.internal:5000/webhook/notify")


def _subscription_matches(subscription: dict) -> bool:
    notification = subscription.get("notification", {})
    http_url = notification.get("http", {}).get("url")
    return (
        subscription.get("description") == "Monitor Device entities for Room aggregation - CruzrTwin ASEAN"
        and http_url == WEBHOOK_URL
    )


def create_subscription_for_devices():
    """
    Tạo subscription để theo dõi tất cả Device entities
    Khi device thay đổi → gửi webhook → aggregator cập nhật Room
    """
    existing = get_all_subscriptions()
    for subscription in existing:
        if _subscription_matches(subscription):
            print(f"[OK] Subscription already exists")
            print(f"   ID: {subscription.get('id')}")
            print(f"   Webhook: {WEBHOOK_URL}")
            return subscription.get("id")
    
    subscription_payload = {
        "description": "Monitor Device entities for Room aggregation - CruzrTwin ASEAN",
        "subject": {
            "entities": [
                {
                    "idPattern": "Device:.*"  # Theo dõi tất cả device theo prefix ID
                }
            ],
            "condition": {
                "attrs": [
                    "temperature",
                    "humidity",
                    "co2",
                    "smoke_status",
                    "energy_consumption"
                ]
            }
        },
        "notification": {
            "http": {
                "url": WEBHOOK_URL
            },
            "attrs": [
                "temperature",
                "humidity",
                "co2",
                "smoke_status",
                "energy_consumption"
            ],
            "covered": True, 
            "attrsFormat": "keyValues",
            "metadata": ["dateCreated", "dateModified"]
        },
        "throttling": 0,
        "status": "active"
    }
    
    try:
        response = requests.post(
            f"{ORION_URL}/v2/subscriptions",
            headers=FIWARE_HEADERS,
            json=subscription_payload,
            timeout=10
        )
        
        if response.status_code == 201:
            subscription_id = response.headers.get("Location", "").split("/")[-1]
            print(f"[OK] Subscription created successfully!")
            print(f"   ID: {subscription_id}")
            print(f"   Webhook: {WEBHOOK_URL}")
            print(f"   Monitoring: Device.* (all devices)")
            return subscription_id
        elif response.status_code == 409:
            print(f"[WARN] Subscription already exists")
            return None
        else:
            print(f"[FAIL] Failed: {response.status_code}")
            print(f"   {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return None


def get_all_subscriptions():
    """Lấy danh sách tất cả subscriptions"""
    try:
        response = requests.get(
            f"{ORION_URL}/v2/subscriptions",
            headers=FIWARE_READ_HEADERS,
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def delete_subscription(subscription_id: str):
    """Xóa subscription theo ID"""
    try:
        response = requests.delete(
            f"{ORION_URL}/v2/subscriptions/{subscription_id}",
            headers=FIWARE_READ_HEADERS,
            timeout=10
        )
        
        if response.status_code == 204:
            print(f"✅ Deleted subscription: {subscription_id}")
            return True
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def delete_all_subscriptions():
    """Xóa tất cả subscriptions"""
    subs = get_all_subscriptions()
    for sub in subs:
        delete_subscription(sub.get("id"))


def ensure_subscription_for_devices():
    subs = get_all_subscriptions()
    matches = [sub for sub in subs if _subscription_matches(sub)]
    if matches:
        for duplicate in matches[1:]:
            delete_subscription(duplicate.get("id"))
        return matches[0].get("id")
    return create_subscription_for_devices()