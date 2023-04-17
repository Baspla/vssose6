import os
import time
import threading
import csv
import logging as log
from bank_constants import *
from user_interface import HTTPServer

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
    def __init__(self, stock_amount, stock_value, funds, loans):
        self.portfolio_value = 0
        # How many stocks the bank has
        self.stock_amount = stock_amount
        # How much a stock is worth
        self.stock_value = stock_value
        # How much money the bank has
        self.funds = funds
        # How much money the bank has lent out
        self.loans = loans
    
    #
    # Process Börsen Changes
    #
    def process_stock_change(self,stock, stock_amount, stock_value):
        log.debug("Processing stock change for {} with amount {} and value {}".format(stock, stock_amount, stock_value))
        self.update_stock_value(stock, stock_value)
        self.update_portfolio_value()

    # This function is called when a total stock update is received
    # The difference to process_stock_change is that this function does not update the portfolio value
    # This happens if the bank receives a stock update from the boerse server that is prefixed with "ALL"
    def process_stock_update(self,stock, stock_value):
        log.debug("Processing stock update for {} with value {}".format(stock, stock_value))
        self.update_stock_value(stock, stock_value)

    def update_stock_value(self,stock, updated_value):
        log.debug("Updating stock value for {}".format(stock))
        if stock not in self.stock_value:
            log.debug("Encountered unknown stock {}".format(stock))
            self.stock_amount[stock] = 0
        self.stock_value[stock] = updated_value

    def update_portfolio_value(self):
        log.debug("Updating portfolio value")
        updated_portfolio_value = 0
        for stock in self.stock_amount:
            if stock in self.stock_value: # This check fails if stock is not in value dict. This should not happen.
                updated_portfolio_value += self.stock_amount[stock] * self.stock_value[stock]
            else:
                log.error("Stock {} not found".format(stock))
        
        self.portfolio_value = round(updated_portfolio_value, 2)
        log.info("New Portfolio value: {}".format(self.portfolio_value))

    def getStockValue(self, stock):
        if stock in self.stock_value:
            return self.stock_value[stock]
        else:
            return None

    def getStockList(self):
        # Return a combined list of all stocks with amount and value
        stock_list = {}
        for stock in self.stock_amount:
            stock_list[stock] = {
                "amount": self.stock_amount[stock],
                "value": self.stock_value[stock]
            }
        return stock_list
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
            for stock in self.stock_value:
                log.info("{}: {}".format(stock, self.stock_value[stock]))
            log.info("##################")

    # How much all stocks are worth
    def getPortfolioValue(self):
        return self.portfolio_value

    # How much cash the bank lent out
    def getTotalLoans(self):
        return self.loans

    # How much cash the bank has
    def getTotalFunds(self):
        return self.funds

    # How much all stocks are worth + cash
    def getTotalValue(self):
        return self.funds + self.portfolio_value

    # P2 functions (deposit, withdraw, getLoan, repayLoan)
    def deposit(self, value):
        self.funds = self.funds + value
    
    def withdraw(self, value):
        self.funds = self.funds - value

    def getLoan(self, value):
        self.funds = self.funds - value
        self.loans = self.loans + value
        
    def repayLoan(self, value):
        self.funds = self.funds + value
        self.loans = self.loans - value

    # buying and selling stocks does not change global value of stocks
    def buyStock(self, stock, amount):
        self.stock_amount[stock] = self.stock_amount[stock] + amount
        self.update_portfolio_value()

    def sellStock(self, stock, amount):
        if self.stock_amount[stock] < amount:
            return False
        self.stock_amount[stock] = self.stock_amount[stock] - amount
        self.update_portfolio_value()
        return True

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
        bank = Bank(amount, value, START_FUNDS, START_LOANS)
        uiServer = HTTPServer(bank)
        threading.Thread(target=listen_to_boerse, args=(bank,ip,port)).start()
        threading.Thread(target=bank.print_prices).start()
        threading.Thread(target=uiServer.start).start()