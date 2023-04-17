#
# UDP Methods
#
import os
import socket

import logging as log
import time

from bank_constants import *

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

def send_message(clientsocket,message, address):
    bytesToSend = str.encode(message)
    clientsocket.sendto(bytesToSend, address)

#
# Connect to Börsen Server and listen for changes
#
def listen_to_boerse(bank,ip,port):
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
            bank.process_stock_change(stock, amount, value)
        elif message.startswith("ALL;"):
            stock,amount, value = message.split(";")[1:]
            value = float(value)
            bank.process_stock_update(stock, value)
        elif message.startswith("KEEPALIVE;"):
            log.debug("Received keepalive message from boersen server at {}:{}".format(ip,port))
            # Send keepalive message back to boersen server. This is needed to measure the round trip time
            send_message(UDPClientSocket,message, (ip,port))
        else:
            log.debug("Received unknown message from boersen server at {}:{}. Message: {}".format(ip,port,message))