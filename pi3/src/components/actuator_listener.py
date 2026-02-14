class ActuatorController:
    def __init__(self, settings, pi_id, base_topic, mqtt, qos=1):
        self.settings = settings
        self.pi_id = pi_id
        self.base_topic = base_topic
        self.mqtt = mqtt
        self.qos = qos

    def handle_command(self, cmd: str):
        parts = cmd.split()
        if not parts:
            return

        c0 = parts[0].lower()

        #door light
        if c0 == "dl":
            if len(parts) < 2:
                print("Usage: dl on|off|toggle")
                return

            action = parts[1].lower()
            topic = f"{self.base_topic}/{self.pi_id}/actuators/DL/set"
            payload = {"action": action}

            self.handle(topic, payload)
            print(f"DL -> {action}")
            return

        #door buzzer
        if c0 == "db":
            if len(parts) < 2:
                print("Usage: db on|off|beep")
                return

            action = parts[1].lower()
            topic = f"{self.base_topic}/{self.pi_id}/actuators/DB/set"
            payload = {"action": action}

            if action == "beep":
                payload["n"] = int(parts[2]) if len(parts) > 2 else 1
                payload["duration"] = float(parts[3]) if len(parts) > 3 else 0.2
                payload["pitch"] = int(parts[4]) if len(parts) > 4 else 440

            self.handle(topic, payload)
            print(f"DB -> {action}")
            return

        print("Unknown command")

    def handle(self, topic, payload):
        action = payload.get("action")

        print(f"ACTUATOR EXECUTED: {topic} -> {action}")

        # Publish state update
        state_topic = topic.replace("/set", "/state")

        self.mqtt.publish_json(
            state_topic,
            {
                "pi_id": self.pi_id,
                "code": topic.split("/")[-2],
                "state": action
            },
            qos=self.qos
        )

