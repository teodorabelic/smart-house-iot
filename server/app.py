import json
import os
import threading
import time
from collections import defaultdict, deque
from datetime import datetime, timezone
from urllib.parse import quote

from dotenv import load_dotenv
from flask import Flask, Response, jsonify, render_template, request, send_file

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
PI_ID_FILTER_RAW = os.getenv("PI_ID_FILTER", "")
PI_ID_FILTERS = {
    item.strip().upper()
    for item in PI_ID_FILTER_RAW.split(",")
    if item.strip()
}
WEB_PIN = os.getenv("ALARM_PIN", "1234")
ARM_DS_PIN_GRACE_SEC = int(os.getenv("ARM_DS_PIN_GRACE_SEC", "10"))
GRAFANA_EMBED_URL = os.getenv("GRAFANA_EMBED_URL", "")
CAMERA_ALLOWED_ROOTS = [
    os.path.abspath(path.strip())
    for path in os.getenv("CAMERA_ALLOWED_ROOTS", "/tmp/camera_captures,/workspace").split(",")
    if path.strip()
]

app = Flask(__name__)

influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx.write_api()

latest_state = {}
state_lock = threading.Lock()

system_state = {
    "alarm_active": False,
    "system_armed": False,
    "arm_at": None,
    "pin": WEB_PIN,
    "persons_count": 0,
    "timer_add_seconds": 30,
    "pin_buffer": "",
}

ds_pressed_since = {}
dus_history = defaultdict(lambda: deque(maxlen=8))
ds_armed_pending_until = {}
active_alarm_reasons = set()

def utc_now():
    return datetime.now(timezone.utc)



def now_iso():
    return utc_now().isoformat()


def parse_payload(msg):
    try:
        return json.loads(msg.payload.decode("utf-8"))
    except Exception:
        return {"raw": msg.payload.decode("utf-8", errors="ignore")}


def write_sensor_to_influx(data: dict):
    code = str(data.get("code", ""))
    point = (
        Point("sensor_readings")
        .tag("pi_id", str(data.get("pi_id", "")))
        .tag("device_name", str(data.get("device_name", "")))
        .tag("code", code)
        .tag("simulated", str(bool(data.get("simulated", False))).lower())
    )

    val = data.get("value", None)
    if isinstance(val, bool):
        point = point.field("value_bool", val)
    elif isinstance(val, (int, float)):
        point = point.field("value_num", float(val))
    elif isinstance(val, dict):
        point = point.field("value_json", json.dumps(val))
        if "temperature" in val:
            point = point.field("temperature", float(val.get("temperature", 0)))
        if "humidity" in val:
            point = point.field("humidity", float(val.get("humidity", 0)))
    else:
        point = point.field("value_str", str(val))

    ts = data.get("ts")
    try:
        dt = datetime.fromisoformat(ts) if ts else utc_now()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
    except Exception:
        dt = utc_now()

    point = point.time(dt, WritePrecision.NS)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)


def write_actuator_to_influx(data: dict):
    point = (
        Point("actuator_events")
        .tag("pi_id", str(data.get("pi_id", "")))
        .tag("code", str(data.get("code", "")))
        .field("state", str(data.get("state", "")))
    )
    point = point.time(utc_now(), WritePrecision.NS)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)


def publish_actuator(pi_id, code, payload):
    topic = f"{BASE_TOPIC}/{pi_id}/actuators/{code}/set"
    mqttc.publish(topic, json.dumps(payload), qos=1, retain=False)


def set_alarm(active, reason=""):
    reason = str(reason or "").strip()
    with state_lock:
        if active:
            active_alarm_reasons.add(reason or "unknown")
        else:
            # Manual OFF/PIN OFF treba da ugase sve razloge alarma.
            if reason in {"web_manual", "web_pin_ok", "pin_ok"} or not reason:
                active_alarm_reasons.clear()
            else:
                active_alarm_reasons.discard(reason)

        next_active = bool(active_alarm_reasons)
        changed = system_state["alarm_active"] != next_active
        system_state["alarm_active"] = next_active
    if not changed:
        return
    action = "on" if system_state["alarm_active"] else "off"
    publish_actuator("PI1", "DB", {"action": action})
    point = Point("system_events").tag("event", "alarm").field("active", bool(system_state["alarm_active"])).field("reason", reason).time(utc_now(), WritePrecision.NS)
    write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=point)


def handle_sensor_logic(pi_id, code, value):
    now = time.time()

    if code in {"DUS1", "DUS2"}:
        try:
            dus_history[code].append((now, float(value)))
        except Exception:
            return

    if code in {"DS1", "DS2"}:
        pressed = bool(value)
        if pressed and code not in ds_pressed_since:
            ds_pressed_since[code] = now
        if not pressed:
            ds_pressed_since.pop(code, None)
            ds_armed_pending_until.pop(code, None)
            set_alarm(False, f"{code}_open_over_5s")
            return
        if now - ds_pressed_since.get(code, now) >= 5:
            set_alarm(True, f"{code}_open_over_5s")
        if system_state.get("system_armed"):
            deadline = ds_armed_pending_until.get(code)
            if deadline is None:
                ds_armed_pending_until[code] = now + ARM_DS_PIN_GRACE_SEC
            elif now >= deadline:
                set_alarm(True, f"{code}_trigger_when_armed")

    if code == "DMS":
        k = str(value)
        if k.isdigit():
            with state_lock:
                system_state["pin_buffer"] = (system_state.get("pin_buffer", "") + k)[-4:]
                current = system_state["pin_buffer"]
            if current == system_state["pin"]:
                with state_lock:
                    if system_state["alarm_active"] or system_state["system_armed"] or system_state["arm_at"] is not None:
                        system_state["system_armed"] = False
                        system_state["arm_at"] = None
                        system_state["pin_buffer"] = ""
                        ds_armed_pending_until.clear()
                        disable = True
                    else:
                        system_state["arm_at"] = now + 10
                        system_state["pin_buffer"] = ""
                        disable = False
                if disable:
                    set_alarm(False, "pin_ok")

    if code in {"DPIR1", "DPIR2"} and bool(value):
        if code == "DPIR1":
            publish_actuator("PI1", "DL", {"action": "on"})
            threading.Timer(10.0, lambda: publish_actuator("PI1", "DL", {"action": "off"})).start()

        dus_code = "DUS1" if code == "DPIR1" else "DUS2"
        vals = [v for ts, v in dus_history[dus_code] if now - ts <= 4]
        if len(vals) >= 2:
            if vals[-1] < vals[0]:
                with state_lock:
                    system_state["persons_count"] += 1
            elif vals[-1] > vals[0]:
                with state_lock:
                    system_state["persons_count"] = max(0, system_state["persons_count"] - 1)

    if code in {"DPIR1", "DPIR2", "DPIR3"} and bool(value):
        if system_state.get("persons_count", 0) == 0:
            set_alarm(True, f"motion_empty_home_{code}")

    if code == "GSG" and isinstance(value, dict) and bool(value.get("significant_movement")):
        set_alarm(True, "gyroscope_significant_movement")

    if code == "BTN" and bool(value):
        publish_actuator("PI2", "BTN", {"action": "add", "seconds": int(system_state["timer_add_seconds"])})


def check_scheduled_arm():
    with state_lock:
        arm_at = system_state.get("arm_at")
        if arm_at and time.time() >= arm_at:
            system_state["system_armed"] = True
            system_state["arm_at"] = None


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="server-subscriber")


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        client.subscribe(f"{BASE_TOPIC}/+/sensors/#", qos=1)
        client.subscribe(f"{BASE_TOPIC}/+/camera/#", qos=1)
        client.subscribe(f"{BASE_TOPIC}/+/actuators/+/state", qos=1)


def on_message(client, userdata, msg):
    payload = parse_payload(msg)
    parts = msg.topic.split("/")
    if len(parts) < 3 or parts[0] != BASE_TOPIC:
        return

    pi_id = parts[1]
    if PI_ID_FILTERS and pi_id.upper() not in PI_ID_FILTERS:
        return

    if len(parts) >= 4 and parts[2] == "sensors":
        payload.setdefault("pi_id", pi_id)
        payload.setdefault("code", parts[3])
        payload.setdefault("ts", now_iso())
        write_sensor_to_influx(payload)
        with state_lock:
            latest_state[payload["code"]] = payload
        handle_sensor_logic(pi_id, payload["code"], payload.get("value"))
    elif len(parts) >= 5 and parts[2] == "camera":
        payload.setdefault("pi_id", pi_id)
        payload.setdefault("code", parts[3])
        payload.setdefault("ts", now_iso())
        with state_lock:
            latest_state[f"CAM_{parts[3]}"] = payload
    elif len(parts) >= 5 and parts[2] == "actuators" and parts[4] == "state":
        payload.setdefault("pi_id", pi_id)
        payload.setdefault("code", parts[3])
        write_actuator_to_influx(payload)
        with state_lock:
            latest_state[f"ACT_{parts[3]}"] = payload


mqttc.on_connect = on_connect
mqttc.on_message = on_message


def mqtt_thread():
    mqttc.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    mqttc.loop_forever()


def scheduler_thread():
    while True:
        check_scheduled_arm()
        time.sleep(0.5)


threading.Thread(target=mqtt_thread, daemon=True).start()
threading.Thread(target=scheduler_thread, daemon=True).start()


@app.get("/")
def index():
    return render_template("index.html", grafana_embed=GRAFANA_EMBED_URL)


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": True,
            "mqtt": {"host": MQTT_HOST, "port": MQTT_PORT},
            "influx": {"url": INFLUX_URL},
            "pi_id_filters": sorted(PI_ID_FILTERS),
        }
    )


@app.get("/api/state")
def api_state():
    with state_lock:
        return jsonify({"system": system_state, "latest": latest_state})
    

def _is_allowed_camera_path(path: str) -> bool:
    absolute = os.path.abspath(path)
    return any(absolute == root or absolute.startswith(f"{root}{os.sep}") for root in CAMERA_ALLOWED_ROOTS)

def _camera_mime_from_path(path: str) -> str:
    lower = str(path).lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith(".jpg") or lower.endswith(".jpeg"):
        return "image/jpeg"
    if lower.endswith(".bmp"):
        return "image/bmp"
    return "application/octet-stream"


@app.get("/api/camera/latest")
def api_camera_latest():
    with state_lock:
        camera_state = latest_state.get("CAM_WEBC")
    if not camera_state:
        return jsonify({"ok": False, "error": "No camera frame received yet."}), 404

    value = camera_state.get("value") if isinstance(camera_state, dict) else None
    frame_path = value.get("filename") if isinstance(value, dict) else None

    image_url = None
    if frame_path and _is_allowed_camera_path(frame_path) and os.path.exists(frame_path):
        image_url = f"/api/camera/frame?path={quote(frame_path, safe='')}"

    return jsonify({"ok": True, "camera": camera_state, "image_url": image_url})


@app.get("/api/camera/frame")
def api_camera_frame():
    frame_path = request.args.get("path", "")
    if not frame_path:
        return jsonify({"ok": False, "error": "Missing path query param."}), 400
    if not _is_allowed_camera_path(frame_path):
        return jsonify({"ok": False, "error": "Path is outside allowed roots."}), 403
    if not os.path.exists(frame_path):
        return jsonify({"ok": False, "error": "Frame not found."}), 404
    mimetype = _camera_mime_from_path(frame_path)
    return send_file(frame_path, mimetype=mimetype)


@app.get("/api/camera/stream")
def api_camera_stream():
    def frame_generator():
        last_key = None
        while True:
            with state_lock:
                camera_state = latest_state.get("CAM_WEBC")

            value = camera_state.get("value") if isinstance(camera_state, dict) else None
            frame_path = value.get("filename") if isinstance(value, dict) else None

            if not frame_path or not _is_allowed_camera_path(frame_path) or not os.path.exists(frame_path):
                time.sleep(0.5)
                continue

            try:
                mtime = os.path.getmtime(frame_path)
                key = (frame_path, mtime)
                if key == last_key:
                    time.sleep(0.2)
                    continue

                with open(frame_path, "rb") as frame_file:
                    image_bytes = frame_file.read()

                last_key = key
                content_type = _camera_mime_from_path(frame_path)
                yield (
                    b"--frame\r\n"
                    + f"Content-Type: {content_type}\r\n".encode("utf-8")
                    + b"Cache-Control: no-cache\r\n\r\n"
                    + image_bytes
                    + b"\r\n"
                )
            except Exception:
                time.sleep(0.5)

    return Response(
        frame_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@app.post("/api/alarm")
def api_alarm():
    data = request.get_json(force=True, silent=True) or {}
    action = str(data.get("action", "")).lower()
    if action == "on":
        set_alarm(True, "web_manual")
    elif action == "off":
        set_alarm(False, "web_manual")
        with state_lock:
            system_state["system_armed"] = False
            system_state["arm_at"] = None
    return jsonify({"ok": True})


@app.post("/api/pin")
def api_pin():
    data = request.get_json(force=True, silent=True) or {}
    pin = str(data.get("pin", ""))
    if pin == system_state["pin"]:
        set_alarm(False, "web_pin_ok")
        with state_lock:
            system_state["system_armed"] = False
            system_state["arm_at"] = None
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Invalid PIN"}), 400


@app.post("/api/timer")
def api_timer():
    data = request.get_json(force=True, silent=True) or {}
    seconds = int(data.get("seconds", 0))
    publish_actuator("PI2", "4SD", {"action": "set", "seconds": max(0, seconds)})
    return jsonify({"ok": True})


@app.post("/api/timer/add-seconds")
def api_timer_add_seconds():
    data = request.get_json(force=True, silent=True) or {}
    with state_lock:
        system_state["timer_add_seconds"] = max(1, int(data.get("seconds", 30)))
    return jsonify({"ok": True, "timer_add_seconds": system_state["timer_add_seconds"]})


@app.post("/api/rgb")
def api_rgb():
    data = request.get_json(force=True, silent=True) or {}
    action = str(data.get("action", "OFF")).upper()
    publish_actuator("PI3", "BRGB", {"action": action})
    return jsonify({"ok": True, "action": action})

@app.post("/api/actuator")
def api_actuator():
    data = request.get_json(force=True, silent=True) or {}
    pi_id = str(data.get("pi_id", "")).upper()
    code = str(data.get("code", "")).upper()
    action = data.get("action")

    allowed = {
        "PI1": {"DL", "DB"},
        "PI2": {"4SD", "BTN"},
        "PI3": {"BRGB"},
    }

    if pi_id not in allowed or code not in allowed[pi_id]:
        return jsonify({"ok": False, "error": "Unsupported pi_id/code"}), 400

    payload = {"action": action} if action is not None else {}
    if "seconds" in data:
        payload["seconds"] = int(data.get("seconds", 0))

    publish_actuator(pi_id, code, payload)
    return jsonify({"ok": True, "pi_id": pi_id, "code": code, "payload": payload})




if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)
