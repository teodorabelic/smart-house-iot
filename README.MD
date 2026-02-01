Commands:

docker-compose up -d


1. Terminal - docker (za test)

docker exec -it smart-house-iot-mosquitto-1 \
mosquitto_sub -t "smarthome/PI1/actuators/#" -v

2. Terminal - pi1 Client

python3 pi1/src/main.py

3. Terminal - server

python3 server/app.py