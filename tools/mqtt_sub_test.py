import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    print(f"{msg.topic} -> {msg.payload.decode()}")

client = mqtt.Client()
client.connect("localhost", 1883)
client.subscribe("smarthome/#")
client.on_message = on_message

print("Listening on smarthome/# ...")
client.loop_forever()
