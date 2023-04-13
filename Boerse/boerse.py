import socket
import os
import time
import csv
import random
import threading

print("Server started")

# Get stock data from csv
def read_csv_file(file_path):
    stock = []
    value = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            stock.append(row['stock'])
            value.append(float(row['value']))
    return stock, value

file_path = 'vs_p1_stocks.csv'
stock, value = read_csv_file(file_path)

print("Loaded {} stocks".format(len(stock)))

LOCAL_IP = ""
LOCAL_PORT = int(os.environ.get("PORT",12345))
BUFFER_SIZE = 1024

# Create a datagram socket
print("Setting up socket with IP: {} and Port: {}".format(LOCAL_IP, LOCAL_PORT))
UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
UDPServerSocket.bind((LOCAL_IP, LOCAL_PORT))
print("UDP server up and listening")

# A dictionary to keep track of connected clients and their addresses
connected_clients = {}

def send_all_prices(address):
    for i in range(len(stock)):
        send_message("CHANGE;"+stock[i] + ";0;" + str(value[i]), address)

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
            print("New client connected: {}".format(address))

        # Send the current prices to the client
        if message == b'all':
            print("Sending all prices to {}".format(address))
            send_all_prices(address)

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
            print("Traded {} of {} for {} (value change: {})".format(amount, stock[wId], value[wId], priceChange))
            broadcast_message("CHANGE;"+stock[wId] + ";"+str(amount)+";" + str(value[wId]))

        # Wait for a random amount of time before generating the next price change
        waitTime = random.uniform(5.0, 10.0)
        time.sleep(waitTime)

# Start the thread that listens for incoming datagrams
t1 = threading.Thread(target=listen_for_datagrams)
t1.start()

# Start the thread that changes the prices of the stocks
t2 = threading.Thread(target=change_prices)
t2.start()
