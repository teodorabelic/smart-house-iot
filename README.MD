# Smart House IoT

A team-developed smart home system built using Raspberry Pi devices, Python, and MQTT communication. The project integrates sensors, actuators, data collection, monitoring, and a web-based control interface.

## Features

- Integration of sensors and actuators across three Raspberry Pi devices.
- MQTT-based communication between devices and the central server.
- Alarm activation, deactivation, and PIN-based control.
- Kitchen timer configuration and RGB lighting control.
- Real-time device status monitoring through a Flask web interface.
- Sensor data storage and visualization using InfluxDB and Grafana.
- Docker-based infrastructure for MQTT, database, and monitoring services.

## Technologies

**Hardware:** Raspberry Pi, sensors, actuators

**Backend:** Python, Flask

**Communication:** MQTT, Eclipse Mosquitto

**Database & Monitoring:** InfluxDB, Grafana

**Infrastructure:** Docker, Docker Compose

## System Architecture

The system consists of three Raspberry Pi devices communicating with a central MQTT broker.

1. Raspberry Pi devices collect sensor readings and publish device events through MQTT.
2. Eclipse Mosquitto manages communication between devices and the server.
3. The Python/Flask server processes incoming events and stores sensor data in InfluxDB.
4. Grafana dashboards visualize collected data.
5. The web interface provides device monitoring and control functionality.

## Getting Started

### Prerequisites

- Python 3
- Docker and Docker Compose
- Raspberry Pi devices and the required hardware components for full functionality

### Configuration

Copy `.env.example` to `.env` and configure the required environment variables. Never commit real credentials or tokens.

### Start infrastructure

```bash
docker compose up -d
```

### Start application processes

Run each process in a separate terminal:

```bash
python pi1/src/main.py
python pi2/src/main.py
python pi3/src/main.py
python server/app.py
```

The web interface is available at `http://localhost:5050`, and Grafana at `http://localhost:3000`.

The full system requires the appropriate Raspberry Pi hardware and configuration.
