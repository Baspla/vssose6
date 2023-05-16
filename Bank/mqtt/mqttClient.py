import json
import uuid
import paho.mqtt.client as mqtt
import time
import logging as log
from random import randrange, uniform

from constants import SERVER_ID, PUBLISH_VALUES_INTERVAL, INSOLVENCY_LENDING_AMOUNT_MQTT


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
        self.mqttBroker = "mosquitto"
        self.bank = bank
        self.funds_banken = {}
        self.last_update = {}
        self.current_proposal = None
        self.controlled_proposal = None
        self.received_agreements = {}
        self.client = mqtt.Client(SERVER_ID)


    def start(self):
        log.info("Starting MQTT Client")
        try:
            self.client.connect(self.mqttBroker, 8883)
        except Exception as e:
            log.error("Error connecting to MQTT broker: {}".format(e))
            return
        self.client.loop_start()
        self.client.subscribe("VALUES")
        self.client.subscribe("RESCUE_PROPOSAL")
        self.client.subscribe("RESCUE_PROPOSAL_ACCEPTED")
        self.client.subscribe("RESCUE_PROPOSAL_DECLINED")
        self.client.subscribe("RESCUE_PROPOSAL_FINISHED")


        self.client.on_message = self.on_message

    def publishValues(self):
        while True:
            values = self.bank.getValues()
            self.client.publish("VALUES", values)
            log.info("Published values {}".format(values))

            if self.checkInsolvency(self.bank.getTotalFunds()):
                log.info("Bank is insolvent")
                # Überprüfen ob bereits ein Rettungsplan diskutiert wird
                if self.current_proposal is not None:
                    log.info("Already discussing a proposal")
                    return
                if self.controlled_proposal is not None:
                    log.info("Already controlling a proposal")
                    return

                # Rettungsplan erstellen
                loans = {}
                for bank_id in self.funds_banken:
                    if bank_id == SERVER_ID: # Wir retten uns nicht selbst
                        continue
                    if self.funds_banken[bank_id] > 60000: # Jede Bank mit funds > 60.000 gibt 10% ihres Geldes ab
                        loans[bank_id] = 0.1 * self.funds_banken[bank_id]
                        log.info("Bank " + bank_id + " sends " + str(loans[bank_id]) + " to bank " + SERVER_ID)
                        self.received_agreements[bank_id] = False
                proposal = {"proposal_id": uuid.uuid4().__str__(), "to_be_rescued": SERVER_ID, "loans": loans}
                self.controlled_proposal = proposal
                self.client.publish("RESCUE_PROPOSAL", json.dumps(proposal)) # Rettungsplan veröffentlichen
                
            time.sleep(PUBLISH_VALUES_INTERVAL)
            
    # check if bank is insolvent
    def checkInsolvency(self, values):
        log.info("Checking insolvency: Funds: "+str(values)+" insolvency limit: "+str(INSOLVENCY_LENDING_AMOUNT_MQTT)+" overstep limit: "+str(values < INSOLVENCY_LENDING_AMOUNT_MQTT))
        if values < INSOLVENCY_LENDING_AMOUNT_MQTT:
            return True
        return False

    def stop(self):
        self.client.loop_stop()

    def on_message(self,client, userdata, message):
        log.debug("Received message in topic {}: {}".format(message.topic, message.payload.decode("utf-8")))
        # Buchführung wie viel Geld jede Bank hat
        msg = str(message.payload.decode("utf-8"))
        if message.topic == "VALUES":
            # check if msg is in format "bank_id:amount"
            if len(msg.split(":")) != 2:
                log.error("Received message is not in format 'bank_id:amount'")
                return
            bank_id = msg.split(":")[0]
            self.funds_banken[bank_id] = int(float(msg.split(":")[1]))
            self.last_update[bank_id] = time.time()
            log.debug("Updated funds_banken for bank {}".format(bank_id))
        elif message.topic == "RESCUE_PROPOSAL":
            json_msg = json.loads(msg)
            # Falls bereits ein Rettungsplan existiert, ablehnen
            # Bei erhalt eines Rettungsplans transaktionen erstmal sperren
            if json_msg is None:
                log.error("Received message is not in JSON format")
                return
            if self.current_proposal is not None:
                log.info("Received rescue proposal but already have one")
                client.publish("RESCUE_PROPOSAL_DECLINED", json.dumps({"proposal_id": json_msg["proposal_id"],"sender": SERVER_ID}))
                return

            # Rettungsplan auswerten
            self.current_proposal = json_msg
            self.bank.lock(True)
            log.info("Received rescue proposal: {}".format(json_msg))

            if json_msg["to_be_rescued"] == SERVER_ID: # Wenn wir die zu rettende Bank sind lehnen wir nicht ab
                client.publish("RESCUE_PROPOSAL_ACCEPTED", json.dumps({"proposal_id": json_msg["proposal_id"],"sender": SERVER_ID}))
            else:
                loans = json_msg["loans"]
                accepted = True
                if self.bank.getTotalFunds() < loans[SERVER_ID]:            # In dieser Implementierung wird nur abgelehnt, wenn mehr Funds benötigt werden als vorhanden sind
                    accepted = False
                if accepted:
                    client.publish("RESCUE_PROPOSAL_ACCEPTED", json.dumps({"proposal_id": json_msg["proposal_id"],"sender": SERVER_ID})) # Wenn einverstanden zustimmung senden
                else:
                    client.publish("RESCUE_PROPOSAL_DECLINED", json.dumps({"proposal_id": json_msg["proposal_id"],"sender": SERVER_ID})) # Wenn nicht einverstanden ablehnen
            return
        elif message.topic == "RESCUE_PROPOSAL_DECLINED":
            # Falls wir der Koordinator sind und eine Bank ablehnt
            # Rettungsplan verwerfen und über RESCUE_PROPOSAL_FINISHED alle Banken informieren
            
            json_msg = json.loads(msg)

            if json_msg is None:
                log.error("Received message is not in JSON format")
                return
            
            if self.controlled_proposal is None:
                log.info("Received decline but have no controlled proposal")
                return
            
            if self.controlled_proposal["proposal_id"] != json_msg["proposal_id"]:
                log.info("Received decline but proposal id does not match")
                return
            
            # Rettungsplan verwerfen
            self.controlled_proposal = None
            log.info("Proposal {} declined, therefor sending FINISHED".format(json_msg["proposal_id"]))
            client.publish("RESCUE_PROPOSAL_FINISHED", json.dumps({"proposal_id": json_msg["proposal_id"], "success": False}))
            return
        elif message.topic == "RESCUE_PROPOSAL_ACCEPTED":
            # Falls wir der Koordinator sind und eine Bank zustimmt
            # Nachsehen, ob alle Banken zugestimmt haben
            # Falls ja, Transaktionen gemäß Rettungsplan durchführen und über RESCUE_PROPOSAL_FINISHED alle Banken informieren
            # Falls nein, warten
            json_msg = json.loads(msg)

            if json_msg is None:
                log.error("Received message is not in JSON format")
                return
            
            if self.controlled_proposal is None:
                log.info("Received acceptance but have no controlled proposal")
                return
            
            if self.controlled_proposal["proposal_id"] != json_msg["proposal_id"]:
                log.info("Received acceptance but proposal id does not match")
                return
            
            if not json_msg["sender"] in self.received_agreements:
                if json_msg["sender"] == SERVER_ID:
                    log.info("Received acceptance from myself")
                    return
                log.info(f"Received acceptance but sender %s is not in received_agreements", json_msg["sender"])
                return

            if self.received_agreements[json_msg["sender"]]:
                log.info("Received acceptance but already have one from this sender")
                return

            if json_msg["sender"] == SERVER_ID:
                log.info("Received acceptance from myself")
                return
            
            self.received_agreements[json_msg["sender"]] = True

            if all(self.received_agreements.values()):
                log.info("All banks have accepted, therefor sending FINISHED")
                client.publish("RESCUE_PROPOSAL_FINISHED", json.dumps({"proposal_id": json_msg["proposal_id"], "success": True}))
            else:
                log.info("Received acceptance from %s, waiting for others", json_msg["sender"])
            return
        elif message.topic == "RESCUE_PROPOSAL_FINISHED":
            # Überprüfen ob erfolgreich oder nicht
            # Falls erfolgreich, Rettungsplan durchführen
            # Falls nicht, Rettungsplan verwerfen
            # Transaktionen wieder freigeben
            json_msg = json.loads(msg)

            if json_msg is None:
                log.error("Received message is not in JSON format")
                return
            
            if self.current_proposal is None:
                log.info("Received Proposal finished but have no current proposal")
                return
            
            if self.current_proposal["proposal_id"] != json_msg["proposal_id"]:
                log.info("Received Proposal finished but proposal id does not match")
                return
            
            if json_msg["success"]:
                log.info("Proposal finished successfully")
                # Rettungsplan durchführen
                if self.current_proposal["to_be_rescued"] == SERVER_ID:
                    # Wenn wir die zu rettende Bank sind, dann das erhaltene Geld annehmen
                    sum = 0
                    for bank_id, amount in self.current_proposal["loans"].items():
                        if bank_id != SERVER_ID:
                            sum += amount
                    self.bank.lock(False)
                    self.bank.deposit(sum)
                    log.info("Rescue plan executed")
                else:
                    # Wenn wir nicht die zu rettende Bank sind, dann das verliehene Geld abziehen
                    loaning = self.current_proposal["loans"][SERVER_ID]
                    self.bank.lock(False)
                    self.bank.getLoan(loaning)
                    log.info("Rescue plan executed")
            else:
                log.info("Proposal finished unsuccessfully")
                self.bank.lock(False)

            # Transaktionen wieder freigeben
            self.current_proposal = None
            self.controlled_proposal = None
            self.received_agreements = {}
            return