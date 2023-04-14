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

# Configure logging
LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
log.basicConfig(
    level=LOGLEVEL,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        log.FileHandler('debug.log'),
        log.StreamHandler()
    ]
)

def load_stocks(file_path):
    stock = []
    value = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            stock.append(row['stock'])
            value.append(float(row['value']))
    return stock, value

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
        time.sleep(LOOKUP_KEEPALIVE_INTERVAL)

# A dictionary to keep track of connected clients and their addresses
connected_clients = {}

def send_all_prices(address):
    for i in range(len(stock)):
        send_message("ALL;"+stock[i] + ";0;" + str(value[i]), address)

def send_message(message, address):
    bytesToSend = str.encode(message)
    UDPServerSocket.sendto(bytesToSend, address)

def broadcast_message(message):
    for address in connected_clients.keys():
        send_message(message, address)


# A function that listens for incoming datagrams and sends price changes to connected clients
def listen_for_datagrams():
    # Receive datagram and get the client's address
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
            rtt[address] = time.time() - float(timestamp)
            log.debug("Round trip time of {} is: {}".format(address, rtt[address]))
        else:
            log.debug("Received message from {}: {}".format(address, message))

    # Close the socket when the thread is finished
    UDPServerSocket.close()

# A function that randomly changes the prices of the stocks
def change_prices():
    while True:
        # Generate a random price change and apply it to a random stock
        wId = random.randint(0, len(stock) - 1)
        priceChange = random.randint(-10, 10)
        amount = random.randint(1, 100)
        if priceChange != 0:
            value[wId] = float(value[wId]) + priceChange
            log.info("Traded {} of {} for {} (value change: {})".format(amount, stock[wId], value[wId], priceChange))
            broadcast_message("CHANGE;"+stock[wId] + ";"+str(amount)+";" + str(value[wId]))

        # Wait for a random amount of time before generating the next price change
        waitTime = random.uniform(10.0, 60.0)
        time.sleep(waitTime)

def current_time():
    # Give the time in seconds since the epoch
    return str(int(time.time()))

def client_keepalive():
    while True:
        for address in connected_clients.keys():
            send_message("KEEPALIVE;"+current_time(), address)
        time.sleep(CLIENT_KEEPALIVE_INTERVAL)

LOOKUP_KEEPALIVE_INTERVAL = 30
CLIENT_KEEPALIVE_INTERVAL = 15

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

    t3 = threading.Thread(target=client_keepalive)
    t3.start()

    time.sleep(60) # wait before trying to re-register after startup
    t4 = threading.Thread(target=lookup_keepalive, args=(id, LOCAL_IP, LOCAL_PORT))
    t4.start()

