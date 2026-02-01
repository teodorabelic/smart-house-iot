import os, json, threading
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision

load_dotenv()

INFLUX_URL = os.getenv("INFLUX_URL", "http://localhost:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "")
INFLUX_ORG = os.getenv("INFLUX_ORG", "iot")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET", "iot_bucket")

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
BASE_TOPIC = os.getenv("MQTT_BASE_TOPIC", "smarthome")
PI_ID_FILTER = os.getenv("PI_ID_FILTER", "PI1").strip()

app = Flask(__name__)

influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx.write_api()

def write_sensor_to_influx(data: dict):
    point = (
        Point("sensor_readings")
        .tag("pi_id", str(data.get("pi_id", "")))
        .tag("device_name", str(data.get("device_name", "")))
        .tag("code", str(data.get("code", "")))
        .tag("simulated", str(bool(data.get("simulated", False))).lower())
    )

    val = data.get("value", None)
    if isinstance(val, bool):
        point = point.field("value_bool", val)
    elif val is None:
        point = point.field("value_num", float("nan"))
    else:
        point = point.field("value_num", float(val))

    ts = data.get("ts")
    try:
        dt = datetime.fromisoformat(ts) if ts else datetime.utcnow()
    except Exception:
        dt = datetime.utcnow()

    point = point.time(dt, WritePrecision.NS)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)
    print("WROTE TO INFLUX:", point.to_line_protocol())

def write_actuator_to_influx(data: dict):
    print("WRITING ACTUATOR:", data)
    point = (
        Point("actuator_events")
        .tag("pi_id", str(data.get("pi_id", "")))
        .tag("code", str(data.get("code", "")))
        .field("state", str(data.get("state", "")))
    )
    point = point.time(datetime.utcnow(), WritePrecision.NS)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="server-subscriber")

def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("MQTT connected")
        client.subscribe(f"{BASE_TOPIC}/+/sensors/#", qos=1)
        client.subscribe(f"{BASE_TOPIC}/+/actuators/+/state", qos=1)
    else:
        print("MQTT connection failed:", reason_code)

def on_message(client, userdata, msg):
    print("SERVER GOT:", msg.topic, msg.payload)
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        payload = {"raw": msg.payload.decode("utf-8", errors="ignore")}

    parts = msg.topic.split("/")
    if len(parts) < 3 or parts[0] != BASE_TOPIC:
        return
    pi_id = parts[1]
    if PI_ID_FILTER and pi_id != PI_ID_FILTER:
        return

    if len(parts) >= 4 and parts[2] == "sensors":
        write_sensor_to_influx(payload)
    elif len(parts) >= 5 and parts[2] == "actuators" and parts[4] == "state":
        write_actuator_to_influx(payload)

mqttc.on_connect = on_connect
mqttc.on_message = on_message

def mqtt_thread():
    mqttc.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    mqttc.loop_forever()

threading.Thread(target=mqtt_thread, daemon=True).start()

@app.get("/health")
def health():
    return jsonify({"ok": True, "mqtt": {"host": MQTT_HOST, "port": MQTT_PORT}, "influx": {"url": INFLUX_URL}})

@app.post("/actuators/<code>")
def actuator(code: str):
    """
    Body JSON:
      {"action":"on"}
      {"action":"off"}
      {"action":"toggle"}
      {"action":"beep","n":3,"duration":0.2,"pitch":440}
    """
    data = request.get_json(force=True, silent=True) or {}
    pi_id = request.args.get("pi_id") or (PI_ID_FILTER if PI_ID_FILTER else "PI1")
    topic = f"{BASE_TOPIC}/{pi_id}/actuators/{code.upper()}/set"
    mqttc.publish(topic, json.dumps(data), qos=1, retain=False)
    return jsonify({"published": True, "topic": topic, "payload": data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
