from src.actuators.led import Led

def run_cli(settings, stop_event):
    dl_cfg = settings.get("DL")
    db_cfg = settings.get("DB")

    # SIM fallback states
    sim_state = {"DL": "OFF", "DB": "OFF"}

    led = None
    buzzer = None

    if dl_cfg and not dl_cfg.get("simulated", True):
        led = Led(dl_cfg["pin"])
        led.setup()

    if db_cfg and not db_cfg.get("simulated", True):
        from src.actuators.buzzer import Buzzer
        buzzer = Buzzer(db_cfg["pin"])
        buzzer.setup()

    help_text = """
Commands:
  help
  dl on|off|toggle
  db on|off
  db beep [n] [duration] [pitch]
  exit
"""
    print(help_text)

    while not stop_event.is_set():
        cmd = input("PI1> ").strip()
        if not cmd:
            continue

        parts = cmd.split()
        c0 = parts[0].lower()

        if c0 == "help":
            print(help_text); continue
        if c0 == "exit":
            stop_event.set(); break

        if c0 == "dl":
            if not dl_cfg:
                print("DL not configured"); continue
            action = parts[1].lower() if len(parts) > 1 else ""
            if dl_cfg.get("simulated", True):
                if action == "on": sim_state["DL"] = "ON"
                elif action == "off": sim_state["DL"] = "OFF"
                elif action == "toggle": sim_state["DL"] = "OFF" if sim_state["DL"] == "ON" else "ON"
                else: print("Unknown action"); continue
                print(f"DL(SIM): {sim_state['DL']}")
            else:
                if action == "on": led.on()
                elif action == "off": led.off()
                elif action == "toggle": led.toggle()
                else: print("Unknown action"); continue
                print("DL: OK")
            continue

        if c0 == "db":
            if not db_cfg:
                print("DB not configured"); continue
            action = parts[1].lower() if len(parts) > 1 else ""
            if db_cfg.get("simulated", True):
                if action in ("on","off"):
                    sim_state["DB"] = action.upper()
                    print(f"DB(SIM): {sim_state['DB']}")
                elif action == "beep":
                    n = int(parts[2]) if len(parts) > 2 else 1
                    print(f"DB(SIM): BEEP x{n}")
                else:
                    print("Unknown action")
            else:
                if action == "on":
                    buzzer.on(440); print("DB: ON")
                elif action == "off":
                    buzzer.off(); print("DB: OFF")
                elif action == "beep":
                    n = int(parts[2]) if len(parts) > 2 else 1
                    duration = float(parts[3]) if len(parts) > 3 else 0.2
                    pitch = int(parts[4]) if len(parts) > 4 else 440
                    buzzer.beep(n, duration, pitch)
                    print("DB: BEEP OK")
                else:
                    print("Unknown action")
            continue

        print("Unknown command. Type help.")
