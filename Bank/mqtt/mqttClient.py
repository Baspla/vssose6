import paho.mqtt.client as mqtt
import time
import logging as log
from random import randrange, uniform

from constants import SERVER_ID, PUBLISH_VALUES_INTERVAL

def on_message(client, userdata, message):
    log.info("Received message: {}".format(str(message.payload.decode("utf-8"))))

class mqttClient:
    def __init__(self,bank):
        log.info("Initialized MQTT Client")
        mqttBroker = "mosquitto"
        self.bank = bank
        self.client = mqtt.Client(SERVER_ID)
        self.client.connect(mqttBroker,8883)
        self.start()

    def start(self):
        log.info("Starting MQTT Client")
        self.client.loop_start()
        self.client.subscribe("VALUES")
        self.client.on_message = on_message

    def publishValues(self):
        while True:
            values = self.bank.getValues()
            self.client.publish("VALUES", values)
            log.info("Published values {}".format(values))
            time.sleep(PUBLISH_VALUES_INTERVAL)

    def stop(self):
        self.client.loop_end()