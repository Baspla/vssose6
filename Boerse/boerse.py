import socket
import os
import time
import csv
import random
import threading
import uuid
import http.client
import json
import logging as log
import math
import statistics

from boerse_constants import *

#
# Set up logging
#
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
log.basicConfig(
    level=LOGLEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        log.FileHandler('debug.log'),
        log.StreamHandler()
    ]
)

#
# Loads the initail stock values from the csv file
#
def load_stocks(file_path):
    stock = []
    value = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            stock.append(row['stock'])
            value.append(float(row['value']))
    return stock, value

#
# Registers the boerse with the lookup service
# This is done so that the bank can find the boerses
#
def register_lookup(ip,port):
    id = str(uuid.uuid4())
    data = {
        "id": id,
        "ip": ip,
        "port": port,
        "type": "boerse"
    }

    LOOKUP_HOST = os.environ.get("LOOKUP_HOST", "lookup")
    LOOKUP_IP = socket.gethostbyname(LOOKUP_HOST)
    LOOKUP_PORT = int(os.environ.get("LOOKUP_PORT",22000))

    payload = json.dumps(data)

    headers = {
        "Content-Type": "application/json"
    }

    run = True

    attempt = 0
    
    while run:
        try:
            conn = http.client.HTTPConnection(LOOKUP_IP, LOOKUP_PORT)
            conn.request("POST", "/register", payload, headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 200 and response.status < 300:
                # Parse the json response if ok is true
                if data["ok"]:
                    log.info("Successfully registered with lookup service. Response: {}".format(data))
                    run = False
            if run:
                log.error(f"Registration failed with HTTP status code {response.status} {response.reason} and data {data}")
        except Exception as e:
            log.error(f"Error: {e}")
        finally:
            conn.close()
        if run:
            # exponential backoff up to a maximum of 1 minute
            backoff = min(2 ** (attempt + 1), 60)
            attempt += 1
            log.debug(f"Retrying in {backoff} seconds...")
            time.sleep(backoff)    
    return id

#
# This method is periodically called to send keepalive messages to the lookup service
# This is done so that the lookup service knows that the boerse is still running
#
def lookup_keepalive(id, ip, port):
    data = {
        "id": id,
        "ip": ip,
        "port": port,
        "type": "boerse"
    }

    LOOKUP_HOST = os.environ.get("LOOKUP_HOST", "lookup")
    LOOKUP_IP = socket.gethostbyname(LOOKUP_HOST)
    LOOKUP_PORT = int(os.environ.get("LOOKUP_PORT",22000))

    payload = json.dumps(data)

    headers = {
        "Content-Type": "application/json"
    }

    while True:
        time.sleep(LOOKUP_KEEPALIVE_INTERVAL)
        try:
            conn = http.client.HTTPConnection(LOOKUP_IP, LOOKUP_PORT)
            conn.request("POST", "/register", payload, headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 200 and response.status < 300:
                # Parse the json response if ok is true
                if data["ok"]:
                    log.info("Successfully re-registered with lookup service. Response: {}".format(data))
                else:
                    log.error(f"Re-registration failed. Response: {data}")
            else:
                log.error(f"Re-registration failed with HTTP status code {response.status} {response.reason} and data {data}")
        except Exception as e:
            log.error(f"Error: {e}")
        finally:
            conn.close()

#
# This method sends all current stock prices to the bank
#
def send_all_prices(address):
    for i in range(len(stock)):
        send_message("ALL;"+stock[i] + ";0;" + str(value[i]), address)

#
# This method is used to send a message to a client
#
def send_message(message, address):
    bytesToSend = str.encode(message)
    UDPServerSocket.sendto(bytesToSend, address)

#
# This method is used to send a message to all connected clients
#
def broadcast_message(message):
    for address in connected_clients.keys():
        send_message(message, address)

#
# This method listens for incoming datagrams and sends price changes to connected clients
# It also handles keepalive messages from the bank, which also are used to measure the round trip time 
# All this runs in a separate thread
#
def listen_for_datagrams():
    # Receive datagram and get the client's address
    last_rtt_index = 0
    last_rtts = [0] * RTT_MEASUREMENT_COUNT
    while True:
        bytes_address_pair = UDPServerSocket.recvfrom(BUFFER_SIZE)
        message = bytes_address_pair[0]
        address = bytes_address_pair[1]

        # If the client is not already connected, add it to the dictionary of connected clients
        if address not in connected_clients:
            connected_clients[address] = True
            log.info("New client connected: {}".format(address))

        # Send the current prices to the client
        if message == b'all':
            log.debug("Sending all prices to {}".format(address))
            send_all_prices(address)
        elif message.startswith(b'KEEPALIVE;'):
            log.debug("Received keepalive response from {}".format(address))#
            timestamp = message.split(b';')[1]
            rtt[address] = (time.time() - float(timestamp)) * 1000
            last_rtts[last_rtt_index] = rtt[address]
            last_rtt_index = (last_rtt_index + 1) % len(last_rtts)
            if last_rtt_index == 0:
                log.debug("Average round trip time: {}".format(sum(last_rtts) / len(last_rtts)))
                min_rtt = min(last_rtts)
                max_rtt = max(last_rtts)
                log.debug("Min round trip time: {} ms".format(min_rtt))
                log.debug("Max round trip time: {} ms".format(max_rtt))
                log.debug("Standard deviation: {}".format(math.sqrt(sum((x - min_rtt) ** 2 for x in last_rtts) / len(last_rtts))))
                log.debug("Median: {} ms".format(statistics.median(last_rtts)))

            log.debug("Round trip time of {} is: {} ms (#{})".format(address, rtt[address], last_rtt_index))
        else:
            log.debug("Received message from {}: {}".format(address, message))

    # Close the socket when the thread is finished
    UDPServerSocket.close()

#
# This method is used to generate random price changes for the stocks
# It runs in a separate thread
#
def change_prices():
    while True:
        # Generate a random price change and apply it to a random stock
        wId = random.randint(0, len(stock) - 1)
        priceChange = random.randint(MIN_PRICE_CHANGE, MAX_PRICE_CHANGE)
        amount = random.randint(MIN_TRADE_AMOUNT, MAX_TRADE_AMOUNT)
        if priceChange != 0:
            value[wId] = float(value[wId]) + priceChange
            log.info("Traded {} of {} for {} (value change: {})".format(amount, stock[wId], value[wId], priceChange))
            broadcast_message("CHANGE;"+stock[wId] + ";"+str(amount)+";" + str(value[wId]))

        # Wait for a random amount of time before generating the next price change
        waitTime = random.uniform(MIN_PRICE_CHANGE_INTERVAL, MAX_PRICE_CHANGE_INTERVAL)
        time.sleep(waitTime)

#
# This is a helper method to get the current time
#
def current_time():
    return str(time.time())

#
# This method is used to periodically send keepalive messages to all connected clients
# It runs in a separate thread
#
def client_keepalive():
    while True:
        for address in connected_clients.keys():
            send_message("KEEPALIVE;"+current_time(), address)
        time.sleep(CLIENT_KEEPALIVE_INTERVAL)

#
# This method is used to print the current stock prices
# This is used for validation purposes
# It runs in a separate thread
#
def print_prices():
    while True:
        time.sleep(PRINT_PRICES_INTERVAL)
        log.info("##################\nCurrent prices\n##################")
        for i in range(len(value)):
            log.info("Stock: {} Value: {}".format(stock[i], value[i]))
        log.info("##################")

# A dictionary to keep track of connected clients and their addresses
connected_clients = {}

if __name__ == "__main__":
    log.info("Started boersen server")

    # Set random seed to environment variable if it exists
    if os.environ.get("RANDOM_SEED"):
        random.seed(os.environ.get("RANDOM_SEED"))
    else:
        random.seed()

    file_path = 'vs_p1_stocks.csv'
    stock, value = load_stocks(file_path)

    rtt = {}

    log.info("Loaded {} stocks".format(len(stock)))

    # Server settings

    LOCAL_IP = socket.gethostbyname(socket.gethostname())
    LOCAL_PORT = int(os.environ.get("PORT",12345))
    BUFFER_SIZE = 1024

    log.debug("Registering with lookup service")
    id = register_lookup(LOCAL_IP,LOCAL_PORT)
    log.info("Registered with lookup service with id {}".format(id))

    # Create a datagram socket
    log.info("Setting up socket with IP: {} and Port: {}".format(LOCAL_IP, LOCAL_PORT))
    UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Bind to address and ip
    UDPServerSocket.bind(("", LOCAL_PORT))
    log.info("UDP server up and listening")

    # Start the thread that listens for incoming datagrams
    t1 = threading.Thread(target=listen_for_datagrams)
    t1.start()

    # Start the thread that changes the prices of the stocks
    t2 = threading.Thread(target=change_prices)
    t2.start()

    # Start the thread that sends keepalive messages to the clients
    t3 = threading.Thread(target=client_keepalive)
    t3.start()

    # Start the thread that sends keepalive messages to the lookup service
    t4 = threading.Thread(target=lookup_keepalive, args=(id, LOCAL_IP, LOCAL_PORT))
    t4.start()

    # Print the current prices of the stocks after the server has been running for 5 minutes
    t5 = threading.Thread(target=print_prices)
    t5.start()
