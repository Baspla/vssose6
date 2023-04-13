import os
import socket
import time
import threading
import csv
import logging as log
import http.client
import json

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

def send_message(clientsocket,message, address):
    bytesToSend = str.encode(message)
    clientsocket.sendto(bytesToSend, address)

def update_stock_value(stock, updated_value):
    log.debug("Updating stock value for {}".format(stock))
    if stock not in value:
        log.debug("Encountered unknown stock {}".format(stock))
        amount[stock] = 0
    value[stock] = updated_value

def update_portfolio_value():
    log.debug("Updating portfolio value")
    updated_portfolio_value = 0
    for stock in amount:
        if stock in value: # This check fails if stock is not in value dict. This should not happen.
            updated_portfolio_value += amount[stock] * value[stock]
        else:
            log.error("Stock {} not found".format(stock))
    
    portfolio_value = round(updated_portfolio_value, 2)
    log.info("New Portfolio value: {}".format(portfolio_value))

def process_stock_change(stock, amount, value):
    log.debug("Processing stock change for {} with amount {} and value {}".format(stock, amount, value))
    update_stock_value(stock, value)
    update_portfolio_value()

# This function is called when a total stock update is received
# The difference to process_stock_change is that this function does not update the portfolio value
def process_stock_update(stock, value):
    log.debug("Processing stock update for {} with value {}".format(stock, value))
    update_stock_value(stock, value)

def load_boersen_server_from_lookup_server():
    
    LOOKUP_HOST = os.environ.get("LOOKUP_HOST", "lookup")
    LOOKUP_IP = socket.gethostbyname(LOOKUP_HOST)
    LOOKUP_PORT = os.environ.get("LOOKUP_PORT", 22000)

    headers = {
        "Content-Type": "application/json"
    }

    run = True
    boersen = []

    attempt = 0

    while run:
        try:
            conn = http.client.HTTPConnection(LOOKUP_IP, LOOKUP_PORT)
            conn.request("GET", "/services?type=boerse",None, headers)
            response = conn.getresponse()
            data = json.loads(response.read())
            if response.status >= 200 and response.status < 300:
                # Parse the json response if ok is true
                if data["ok"]:
                    if data["services"].__len__() > 0:
                        boersen = data["services"]
                        log.info("Successfully retrieved boerse server from lookup service.")
                        run = False
                    else:
                        log.warning("No boerse server found in lookup service. Response: {}".format(data))
            if run:
                log.error(f"Failed to find boersen server with HTTP status code {response.status} {response.reason} and data {data}")
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
    return boersen


def listen_to_boerse(ip,port):
    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.settimeout(TIMEOUT)
    log.info("Started listening to boersen server at {}:{}".format(ip,port))
    # Send welcome message to boersen server
    time.sleep(5)
    
    backoff = 1
    log.debug("Sending welcome message to boersen server at {}:{}".format(ip,port))
    send_message(UDPClientSocket,"all", (ip,port))
            
    while True:
        # Wait for response
        try:
            bytes_address_pair = UDPClientSocket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            log.warning("No message received from boersen server at {}:{} for {} seconds. Trying to reconnect...".format(ip,port,TIMEOUT))
            UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            UDPClientSocket.settimeout(TIMEOUT)
            # Exponential backoff max 60 seconds
            log.debug("Waiting {} seconds before trying to reconnect to boersen server at {}:{}".format(backoff,ip,port))
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            send_message(UDPClientSocket,"all", (ip,port))
            continue
        # Reset backoff
        backoff = 1

        message = bytes_address_pair[0].decode("utf-8")
        address = bytes_address_pair[1]
        log.debug("Received message: {} from {}".format(message, address))
        # If the message is a stock price change, process it
        if message.startswith("CHANGE;"):
            stock,amount, value = message.split(";")[1:]
            value = float(value)
            amount = int(amount)
            process_stock_change(stock, amount, value)
        elif message.startswith("ALL;"):
            stock,amount, value = message.split(";")[1:]
            value = float(value)
            process_stock_update(stock, value)
        elif message == "KEEPALIVE":
            log.debug("Received keepalive message from boersen server at {}:{}".format(ip,port))
        else:
            log.debug("Received unknown message from boersen server at {}:{}. Message: {}".format(ip,port,message))


if __name__ == "__main__":
    log.info("Starting bank server")

    BUFFER_SIZE = 1024
    TIMEOUT = 30
    portfolio_value = 0

    # Get initial stock data from csv
    def read_csv_file(file_path):
        amount = {}
        value = {}
        with open(file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                amount[row['stock']] = float(row['amount'])
                value[row['stock']] = 0
        return amount, value

    file_path = 'stocks_amounts.csv'
    amount,value = read_csv_file(file_path)


    log.info("Loaded {} stocks and amounts".format(len(amount)))

    list_boersen_server = load_boersen_server_from_lookup_server()

    for boersen_server_id in list_boersen_server:
        boersen_server = list_boersen_server[boersen_server_id]
        ip = boersen_server["ip"]
        port = boersen_server["port"]
        threading.Thread(target=listen_to_boerse, args=(ip,port)).start()

