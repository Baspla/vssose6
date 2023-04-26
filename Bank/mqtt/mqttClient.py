import paho.mqtt.client as mqtt
import time
import logging as log
from random import randrange, uniform

def on_message(client, userdata, message):
    print("Received message: ", str(message.payload.decode("utf-8")))

class mqttClient:
    def init(self):
        log.info("Initialized MQTT Client")
        mqttBroker = "mosquitto"
        self.client = mqtt.Client("Smartphone")
        self.client.connect(mqttBroker)


        while True:
            randNumber = uniform(20.0, 21.0)
            self.client.publish("TEMPERATURE", randNumber)
            print("Just published " + str(randNumber) + " to topic TEMPERATURE")
            time.sleep(2)


    def start(self):
        log.info("Starting MQTT Client")
        self.client.loop_start()
        self.client.subscribe("TEMPERATURE")
        self.client.on_message = on_message

    def stop(self):
        self.client.loop_end()