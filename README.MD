# Smart House IoT

## Pokretanje

```bash
docker-compose up -d
```

Zatim pokrenuti procese (u odvojenim terminalima):

```bash
python3 pi1/src/main.py
python3 pi2/src/main.py
python3 pi3/src/main.py
python3 server/app.py
```

## Brza provera MQTT-a

```bash
docker exec -it smart-house-iot-mosquitto-1 mosquitto_sub -t "smarthome/+/sensors/#" -v
```

```bash
docker exec -it smart-house-iot-mosquitto-1 mosquitto_sub -t "smarthome/+/actuators/#" -v
```

## Web aplikacija

Korisnički interfejs je dostupan na:

- `http://localhost:5050/`

Omogućeno:
- uključivanje/isključivanje alarma i PIN deakivacija
- podešavanje kuhinjskog tajmera i `BTN +N` vrednosti
- upravljanje BRGB svetlom
- prikaz trenutnog stanja svih komponenti (poslednji MQTT event po kodu)
- opciono embed Grafana panela preko `GRAFANA_EMBED_URL`
