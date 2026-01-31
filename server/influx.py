from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(
    url="http://localhost:8086",
    token="my-token",
    org="iot"
)

write_api = client.write_api(write_options=SYNCHRONOUS)

def write_event(topic, payload):
    p = Point("iot_event")

    for k, v in payload.items():
        p = p.field(k, v)

    p = p.tag("topic", topic)
    write_api.write(bucket="smarthome", record=p)
