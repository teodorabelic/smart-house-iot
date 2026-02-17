def run_cli(controller, stop_event):
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
        try:
            cmd = input("PI2> ").strip()
        except (EOFError, KeyboardInterrupt):
            stop_event.set()
            break

        if not cmd:
            continue

        if cmd == "help":
            print(help_text)
            continue

        if cmd == "exit":
            stop_event.set()
            break

        controller.handle_command(cmd)
