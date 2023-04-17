import os
import time
import threading
import csv
import logging as log
from bank_constants import *

from connect_to_boerse import listen_to_boerse
from connect_to_lookup import load_boersen_server_from_lookup_server

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

class Bank:
    def __init__(self, amount, value):
        self.portfolio_value = 0
        self.amount = amount
        self.value = value
    #
    # Process Börsen Changes
    #
    def process_stock_change(self,stock, amount, value):
        log.debug("Processing stock change for {} with amount {} and value {}".format(stock, amount, value))
        self.update_stock_value(stock, value)
        self.update_portfolio_value()

    # This function is called when a total stock update is received
    # The difference to process_stock_change is that this function does not update the portfolio value
    # This happens if the bank receives a stock update from the boerse server that is prefixed with "ALL"
    def process_stock_update(self,stock, value):
        log.debug("Processing stock update for {} with value {}".format(stock, value))
        self.update_stock_value(stock, value)

    def update_stock_value(self,stock, updated_value):
        log.debug("Updating stock value for {}".format(stock))
        if stock not in self.value:
            log.debug("Encountered unknown stock {}".format(stock))
            self.amount[stock] = 0
        self.value[stock] = updated_value

    def update_portfolio_value(self):
        log.debug("Updating portfolio value")
        updated_portfolio_value = 0
        for stock in self.amount:
            if stock in self.value: # This check fails if stock is not in value dict. This should not happen.
                updated_portfolio_value += self.amount[stock] * self.value[stock]
            else:
                log.error("Stock {} not found".format(stock))
        
        self.portfolio_value = round(updated_portfolio_value, 2)
        log.info("New Portfolio value: {}".format(self.portfolio_value))

    #
    # Prints out the current values for all stocks
    # This function is called every PRINT_PRICES_INTERVAL seconds
    # This is done for validation purposes
    #
    def print_prices(self):
        while True:
            time.sleep(PRINT_PRICES_INTERVAL)
            log.info("Portfolio value: {}".format(self.portfolio_value))
            log.info("##################\nCurrent prices\n##################")
            for stock in self.value:
                log.info("{}: {}".format(stock, self.value[stock]))
            log.info("##################")
        
#
# Main
#
if __name__ == "__main__":
    log.info("Starting bank server")

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

    amount,value = read_csv_file(FILE_PATH)

    log.info("Loaded {} stocks and amounts".format(len(amount)))

    list_boersen_server = load_boersen_server_from_lookup_server()

    for boersen_server_id in list_boersen_server:
        boersen_server = list_boersen_server[boersen_server_id]
        ip = boersen_server["ip"]
        port = boersen_server["port"]
        bank = Bank(amount, value)
        threading.Thread(target=listen_to_boerse, args=(bank,ip,port)).start()
        threading.Thread(target=bank.print_prices).start()


