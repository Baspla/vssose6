import paho.mqtt.client as mqtt
import time
import logging as log
from random import randrange, uniform

from constants import SERVER_ID, PUBLISH_VALUES_INTERVAL, INSOLVENCY_LENDING_AMOUNT_MQTT

funds_banken = {}
last_update = {}
current_proposal = None

def on_message(client, userdata, message):
    log.info("Received message: {}".format(str(message.payload.decode("utf-8"))))
    # Buchführung wie viel Geld jede Bank hat
    msg = str(message.payload.decode("utf-8"))
    if message.topic == "VALUES":
        # check if msg is in format "bank_id:amount"
        if len(msg.split(":")) != 2:
            log.error("Received message is not in format 'bank_id:amount'")
            return
        bank_id = msg.split(":")[0]
        funds_banken[bank_id] = msg.split(":")[1]
        last_update[bank_id] = time.time()
        log.info("Updated funds_banken for bank {}".format(bank_id))
    elif message.topic == "RESCUE_PROPOSAL":
        # Falls bereits ein Rettungsplan existiert, ablehnen
        # Bei erhalt eines Rettungsplans transaktionen erstmal sperren
        
        # Rettungsplan auswerten

        # Wenn einverstanden zustimmung senden

        # Wenn nicht einverstanden ablehnen
        pass
    elif message.topic == "RESCUE_PROPOSAL_DECLINED":
        # Falls wir der Koordinator sind und eine Bank ablehnt
        # Rettungsplan verwerfen und über RESCUE_PROPOSAL_FINISHED alle Banken informieren
        pass
    elif message.topic == "RESCUE_PROPOSAL_ACCEPTED":
        # Falls wir der Koordinator sind und eine Bank zustimmt
        # Nachsehen, ob alle Banken zugestimmt haben
        # Falls ja, Transaktionen gemäß Rettungsplan durchführen und über RESCUE_PROPOSAL_FINISHED alle Banken informieren
        # Falls nein, warten
        pass
    elif message.topic == "RESCUE_PROPOSAL_FINISHED":
        # Überprüfen ob erfolgreich oder nicht
        # Falls erfolgreich, Rettungsplan durchführen
        # Falls nicht, Rettungsplan verwerfen
        # Transaktionen wieder freigeben
        pass

## Wie ein Rescue Proposal aussieht:

# {"proposal_id": "proposal_id", "to_be_rescued": "bank_id", "loans": [{"bank_id": "bank_id", "amount": "amount"}, ...]}


# Prüfe, ob eine Bank unter 50.000€ hat (INSOLVENCY_LENDING_AMOUNT_MQTT)
# Wenn ja, dann 2PC
# 2PC
# Auswahl Koordinator: ZU RETTENDE BANK (Raft Algorithmus oder wer zuerst kommt, zufällig, die zu rettende Bank als koordinator oder wer am meisten Geld hat)
# Sperrung aller Transaktionen, damit sich Zahlen nicht mehr ändern
# Rettungsplan
# Koordinator veröffentlicht Rettungsplan
# Zustimmung aller Banken zum Rettungsplan erforderlich (Ja: Geld Transaktionen (trotz Sperrung) gemäß Rettungsplan - Nein/keine Antwort: Abbruch)
# Aufhebung Sperrung


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

            #if self.checkInsolvency(values):
                #log.info("Bank is insolvent")
                # Überprüfen ob bereits ein Rettungsplan diskutiert wird
                # Rettungsplan erstellen
                    # Jede Bank mit funds > 60.000 gibt 10% ihres Geldes ab
                # Rettungsplan veröffentlichen
                #self.client.publish("RESCUE_PROPOSAL", mqtt.Client(SERVER_ID))
                
            time.sleep(PUBLISH_VALUES_INTERVAL)
            
    # check if bank is insolvent
    def checkInsolvency(self, values):
        if values < INSOLVENCY_LENDING_AMOUNT_MQTT:
            return True
        return False

    def stop(self):
        self.client.loop_end()