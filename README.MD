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

## Usklađivanje Influx/Grafana parametara (bitno)

Da ne bi bilo razlike između `server/.env`, `docker-compose.yaml` i Grafana datasource-a:

- `server/.env` je vraćen na tvoj postojeći token:
  - `INFLUX_TOKEN=60an128...`
- `docker-compose.yaml` koristi iste vrednosti kroz promenljive (`INFLUX_ORG`, `INFLUX_BUCKET`, `INFLUX_TOKEN`) i fallback na isti token.
- Grafana datasource provisioning (`grafana/provisioning/datasources/influxdb.yaml`) koristi iste env promenljive (`${INFLUX_ORG}`, `${INFLUX_BUCKET}`, `${INFLUX_TOKEN}`).

Ako koristiš svoje stvarne kredencijale za Influx login:
- username: `iot`
- password: `iot-projekat`

to je sada podrazumevano i za Influx bootstrap u compose fajlu (`INFLUX_INIT_USERNAME/INFLUX_INIT_PASSWORD`).

> Važno: Influx bootstrap parametri važe samo pri prvom podizanju na praznim volume-ovima.

## Za kolegu na drugom računaru

Na čistom Docker okruženju (bez prethodnih volume-ova), kolega samo radi:

```bash
docker-compose up -d
```

i dobija:
- inicijalizovan Influx (org/bucket/token)
- Grafana datasource ka Influx-u
- učitane dashboard-e iz `grafana/dashboards`

Ako je stack ranije već podizan, potrebno je:

```bash
docker-compose down -v
docker-compose up -d
```

## Grafana dashboard-i i komponente po PI

Sada postoje dashboard-i koji jasno označavaju **PI + komponentu** u naslovu panela.

### Dashboard 1: `Smart House Overview`
- opšti pregled (filter po `pi_id` i `code`)

### Dashboard 2: `Smart House - Components by PI`
- paneli po komponentama (npr. `PI2 / DHT3 - Temp/Humidity`, `PI3 / BRGB - RGB state`, ...)
- svaki panel je precizno vezan za odgovarajući `pi_id` i `code`

## Kako da vidiš PI2 i PI3 u Grafani

1. Otvori Grafanu `http://localhost:3000`
2. Otvori dashboard **Smart House - Components by PI**
3. Proveri panele za PI2 i PI3 (naslov svakog panela sadrži PI i komponentu)

Za ručni Flux upit (primer PI2/PI3):

```flux
from(bucket: "iot_bucket")
  |> range(start: -1h)
  |> filter(fn: (r) => r._measurement == "sensor_readings")
  |> filter(fn: (r) => r.pi_id == "PI2" or r.pi_id == "PI3")
```


## Troubleshooting: "No data" za `PI2 / 4SD - Actuator state` i `PI3 / BRGB - Actuator state`

Ta dva panela čitaju measurement `actuator_events`, koji se popunjava samo kada PI objavi MQTT poruku na topic:

- `smarthome/PI2/actuators/4SD/state`
- `smarthome/PI3/actuators/BRGB/state`

Ako panel prikazuje "No data":
1. restartuj `pi2/src/main.py` i `pi3/src/main.py` (zbog novih publish state izmena),
2. iz web UI-ja okini `Set` tajmera i promeni BRGB boju bar jednom,
3. proveri da `server/app.py` radi i da `PI_ID_FILTER` nije restriktivan.

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

## Influx PI filtriranje (`PI_ID_FILTER`)

`server/app.py` podržava filtriranje PI uređaja na nivou MQTT ingest-a.

- `PI_ID_FILTER=` (prazno) -> upisuje sve PI uređaje (PI1/PI2/PI3)
- `PI_ID_FILTER=PI1` -> upisuje samo PI1
- `PI_ID_FILTER=PI1,PI3` -> upisuje PI1 i PI3

Ako u Influx-u vidiš samo PI1 u tag vrednostima, proveri da filter nije zakucan na `PI1` i restartuj `server/app.py`.
