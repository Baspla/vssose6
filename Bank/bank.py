import os
import socket
import time
import threading
import csv

print("Programm Start")

BUFFER_SIZE = 1024
TIMEOUT = 30
portfolio_value = 0

# Load stocks and amounts from csv

# Get stock data from csv
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


print("Loaded {} stocks and amounts".format(len(amount)))

def send_message(clientsocket,message, address):
    bytesToSend = str.encode(message)
    clientsocket.sendto(bytesToSend, address)

def update_stock_value(stock, updated_value):
    print("Updating stock value for {}".format(stock))
    if stock not in value:
        print("Encountered unknown stock {}".format(stock))
        amount[stock] = 0
    value[stock] = updated_value

def update_portfolio_value():
    print("Updating portfolio value")
    updated_portfolio_value = 0
    for stock in amount:
        if stock in value: # This check fails if stock is not in value dict. This should not happen.
            updated_portfolio_value += amount[stock] * value[stock]
        else:
            print("Stock {} not found".format(stock))
    
    portfolio_value = round(updated_portfolio_value, 2)
    print("New Portfolio value: {}".format(portfolio_value))

def process_stock_change(stock, amount, value):
    print("Processing stock change for {} with amount {} and value {}".format(stock, amount, value))
    update_stock_value(stock, value)
    update_portfolio_value()


def listen_to_boerse(ip,port):
    # Create a UDP socket at client side
    UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
    UDPClientSocket.settimeout(TIMEOUT)
    print("Started listening to boersen server at {}:{}".format(ip,port))
    # Send welcome message to boersen server
    time.sleep(5)
    
    backoff = 1
    print("Sending welcome message to boersen server at {}:{}".format(ip,port))
    send_message(UDPClientSocket,"all", (ip,port))
            
    while True:
        # Wait for response
        try:
            bytes_address_pair = UDPClientSocket.recvfrom(BUFFER_SIZE)
        except socket.timeout:
            print("No message received from boersen server at {}:{} for {} seconds. Trying to reconnect...".format(ip,port,TIMEOUT))
            UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            UDPClientSocket.settimeout(TIMEOUT)
            # Exponential backoff max 60 seconds
            print ("Waiting {} seconds before trying to reconnect".format(backoff))
            time.sleep(backoff)
            backoff = min(backoff * 2, 60)
            send_message(UDPClientSocket,"all", (ip,port))
            continue
        # Reset backoff
        backoff = 1

        message = bytes_address_pair[0].decode("utf-8")
        address = bytes_address_pair[1]
        print("Received message: {} from {}".format(message, address))
        # If the message is a stock price change, process it
        if message.startswith("CHANGE;"):
            stock,amount, value = message.split(";")[1:]
            value = float(value)
            amount = int(amount)
            process_stock_change(stock, amount, value)

# ToDo: Server IPs per Config Client mitteilen
list_boersen_server = [
    {"ip":"127.0.0.1","port":12345},
    {"ip":"127.0.0.1","port":12000}                   
                       ]

for boersen_server in list_boersen_server:
    ip = boersen_server["ip"]
    port = boersen_server["port"]
    threading.Thread(target=listen_to_boerse, args=(ip,port)).start()

