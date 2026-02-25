import json
from typing import Callable, List, Tuple
import paho.mqtt.client as mqtt

class MqttClient:
    def __init__(self, host: str, port: int, client_id: str):
        self.host = host
        self.port = port
        self.client = mqtt.Client(
            # mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id
        )
        self._handlers: List[Tuple[str, Callable[[str, dict], None]]] = []
        self.client.on_message = self._dispatch_message

    def connect(self):
        self.client.connect(self.host, self.port, keepalive=60)
        self.client.loop_start()

    def publish(self, topic: str, payload: dict, qos: int = 1, retain: bool = False):
        self.publish_json(topic, payload, qos=qos, retain=retain)

    def publish_json(self, topic: str, payload: dict, qos: int = 1, retain: bool = False):
        self.client.publish(
            topic,
            json.dumps(payload),
            qos=qos,
            retain=retain
        )

    def _dispatch_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
        except Exception:
            data = {"raw": msg.payload.decode("utf-8", errors="ignore")}

        for subscribed_topic, callback in self._handlers:
            if mqtt.topic_matches_sub(subscribed_topic, msg.topic):
                callback(msg.topic, data)

    def subscribe_json(self, topic: str, on_message: Callable[[str, dict], None], qos: int = 1):
        self._handlers.append((topic, on_message))
        self.client.subscribe(topic, qos=qos)

    def close(self):
        try:
            self.client.loop_stop()
        except Exception:
            pass
        try:
            self.client.disconnect()
        except Exception:
            pass
