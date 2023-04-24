import logging as log
import socket
import threading
import csv
import os
import time
from configuration import GRPC_PORT
from lookup.lookup import load_boersen_server, lookup_keepalive, register_bank_at_lookup
from rest.server import HTTPServer
import rpc.client
import rpc.server
from constants import *
from bank import Bank
from udp.reciever import listen_to_boerse

#
# Set up logging
#
def configure_logging():
    LOGLEVEL = os.environ.get('LOGLEVEL', 'INFO').upper()
    log.basicConfig(
        level=LOGLEVEL,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            log.FileHandler('debug.log'),
            log.StreamHandler()
        ]
    )

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

#
# Main
#
if __name__ == "__main__":
    configure_logging()
    
    log.info("Starting bank server")

    amount,value = read_csv_file(FILE_PATH)

    log.info("Loaded {} stocks and amounts".format(len(amount)))

    bank = Bank(amount, value, START_FUNDS, START_LOANS)
    uiServer = HTTPServer(bank)
    gRPCServer = rpc.server.GRPCServer(bank)
    LOCAL_IP = socket.gethostbyname(socket.gethostname())

    log.debug("Registering with lookup service")
    id = register_bank_at_lookup(LOCAL_IP,GRPC_PORT)
    log.info("Registered with lookup service with id {}".format(id))

    list_boersen_server = load_boersen_server()
    for boersen_server_id in list_boersen_server:
        boersen_server = list_boersen_server[boersen_server_id]
        ip = boersen_server["ip"]
        port = boersen_server["port"]
        threading.Thread(target=listen_to_boerse, args=(bank,ip,port)).start()
    
    pricesThread = threading.Thread(target=bank.print_prices)
    httpThread = threading.Thread(target=uiServer.start)
    grpcThread = threading.Thread(target=gRPCServer.serve)
    keepaliveThread = threading.Thread(target=lookup_keepalive, args=(id,LOCAL_IP,GRPC_PORT))
    financecheckThread = threading.Thread(target=bank.financecheck)
    pricesThread.start()
    httpThread.start()
    grpcThread.start()
    keepaliveThread.start()
    financecheckThread.start()
    grpcThread.join()
    httpThread.join()
    pricesThread.join()
    keepaliveThread.join()
    financecheckThread.join()