'''
========================================================
TUYA BRIDGE - Kết nối ổ cắm thông minh Tuya vào MQTT
========================================================
'''

import os

from env import CONFIG_PATH
import tinytuya
import paho.mqtt.client as mqtt
import json
import time
import yaml
from models import Config
from jinja2 import Template, TemplateError, Environment, meta
from log import setup_logger


logger = setup_logger()


def apply_env_overrides(raw_config: dict) -> dict:
    tuya = raw_config.setdefault("tuya", {})
    if os.getenv("TUYA_REGION"):
        tuya["region"] = os.getenv("TUYA_REGION")
    if os.getenv("TUYA_KEY"):
        tuya["key"] = os.getenv("TUYA_KEY")
    if os.getenv("TUYA_SECRET"):
        tuya["secret"] = os.getenv("TUYA_SECRET")
    return raw_config


def load_config() -> Config:
    try:
        with open(CONFIG_PATH, "r") as file:
            config_data = yaml.safe_load(file) or {}
        apply_env_overrides(config_data)
        config = Config(**config_data)
        logger.debug("Configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", exc_info=True)
        raise


def load_raw_config() -> dict:
    with open(CONFIG_PATH, "r") as file:
        raw = yaml.safe_load(file) or {}
    return apply_env_overrides(raw)


def render_topic(template_str: str, context: dict) -> str:
    try:
        env = Environment()
        parsed_content = env.parse(template_str)
        required_keys = meta.find_undeclared_variables(parsed_content)
        missing_keys = [key for key in required_keys if key not in context]
        if missing_keys:
            raise KeyError(f"Missing keys in device data for template: {missing_keys}")

        template = Template(template_str)
        return template.render(**context)
    except TemplateError as te:
        logger.error(f"Error rendering topic template: {te}", exc_info=True)
        raise
    except KeyError as ke:
        logger.error(f"Error with device keys: {ke}", exc_info=True)
        raise


def build_device_map(raw_config: dict) -> dict:
    devices = raw_config.get("devices") or []
    return {item["id"]: item for item in devices if item.get("id")}


def tuya_to_mqtt(config: Config, raw_config: dict):
    mqtt_broker = config.mqtt.broker
    mqtt_port = config.mqtt.port
    mqtt_user = config.mqtt.user.get_secret_value()
    mqtt_password = (
        config.mqtt.password.get_secret_value()
        if config.mqtt.password is not None
        else None
    )

    try:
        mqtt_client = mqtt.Client()
        if mqtt_user and mqtt_password:
            mqtt_client.username_pw_set(mqtt_user, mqtt_password)
        mqtt_client.connect(mqtt_broker, mqtt_port)
    except Exception:
        logger.error("Error with connecting to MQTT broker", exc_info=True)
        raise

    try:
        cloud = tinytuya.Cloud(
            apiRegion=config.tuya.region,
            apiKey=config.tuya.key.get_secret_value(),
            apiSecret=config.tuya.secret.get_secret_value(),
        )
    except Exception:
        logger.error("Error with connecting to TUYA API", exc_info=True)
        raise

    try:
        devices = cloud.getdevices()
    except Exception:
        logger.error("Error with getting devices", exc_info=True)
        raise

    device_map = build_device_map(raw_config)
    topic_status_template = config.app.topic_status_template

    for device in devices:
        mapping = device_map.get(device["id"])
        if not mapping:
            logger.debug(f"Skip unmapped Tuya device: {device.get('id')}")
            continue

        try:
            result = cloud.getstatus(device["id"])
            all_values = {item["code"]: item["value"] for item in result["result"]}
        except Exception:
            logger.error(
                f"Error reading status for Tuya device {device.get('id')}",
                exc_info=True,
            )
            continue

        wanted_attrs = mapping.get("attrs") or list(all_values.keys())
        payload_data = {
            code: all_values[code]
            for code in wanted_attrs
            if code in all_values
        }

        topic_context = {
            **device,
            "device_id": mapping.get("device_id", device["id"]),
            "name": mapping.get("name", device.get("name")),
        }

        try:
            topic = render_topic(topic_status_template, topic_context)
            payload = json.dumps(payload_data)
            mqtt_client.publish(topic, payload)
            logger.info(
                f"Published {mapping['device_id']} -> {topic}: {payload}"
            )
        except Exception as e:
            logger.error(f"Failed to publish to MQTT: {e}", exc_info=True)
            continue

    mqtt_client.disconnect()
    logger.debug("Disconnected from MQTT")


if __name__ == "__main__":
    logger.info("Starting the application...")
    try:
        logger.info("Loading config...")
        raw_config = load_raw_config()
        config = load_config()
        while True:
            logger.info("Running bridge...")
            tuya_to_mqtt(config, raw_config)
            logger.debug(f"Waiting for period: {config.app.period}s")
            time.sleep(config.app.period)
    except Exception as e:
        logger.error(f"Program encountered an error: {e}", exc_info=True)