import requests
from src.common.config import LOCAL_BRIDGE_URL, LOCAL_BRIDGE_TIMEOUT
from src.common.errors import RobotActionError
from src.common.time_utils import now_iso

class RobotAdapter:
    def dispatch(self, robot_action: dict) -> dict:
        raise NotImplementedError

class RealCruzrAdapter(RobotAdapter):
    def dispatch(self, robot_action: dict) -> dict:
        raise RobotActionError("RealCruzrAdapter is not configured.")

class LocalBridgeAdapter(RobotAdapter):
    def dispatch(self, robot_action: dict) -> dict:
        """
        Sends an HTTP POST request to the local tablet bridge.
        """
        try:
            response = requests.post(
                LOCAL_BRIDGE_URL,
                json=robot_action,
                timeout=LOCAL_BRIDGE_TIMEOUT
            )
            if response.status_code in [200, 201, 202]:
                return {
                    "adapter": "LocalBridgeAdapter",
                    "status": "GUIDANCE_DELIVERED",
                    "voice_played": True,
                    "display_shown": True,
                    "message_en": robot_action["message_en"],
                    "message_vi": robot_action["message_vi"],
                    "timestamp": now_iso(),
                    "response": response.text
                }
            else:
                return {
                    "adapter": "LocalBridgeAdapter",
                    "status": "ERROR",
                    "voice_played": False,
                    "display_shown": False,
                    "error": f"Bridge returned status code {response.status_code}: {response.text}",
                    "timestamp": now_iso()
                }
        except requests.RequestException as e:
            return {
                "adapter": "LocalBridgeAdapter",
                "status": "ERROR",
                "voice_played": False,
                "display_shown": False,
                "error": f"Bridge request failed: {e}",
                "timestamp": now_iso()
            }

class MockCruzrAdapter(RobotAdapter):
    def dispatch(self, robot_action: dict) -> dict:
        """
        Mock fallback adapter.
        """
        return {
            "adapter": "MockCruzrAdapter",
            "status": "GUIDANCE_DELIVERED",
            "voice_played": True,
            "display_shown": True,
            "message_en": robot_action["message_en"],
            "message_vi": robot_action["message_vi"],
            "timestamp": now_iso()
        }
