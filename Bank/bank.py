import time
import logging as log
from rpc.client import on_funds_low
from constants import *


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
        while PRINT_PRICES:
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

    def getValues(self):
        return SERVER_ID+":"+str(self.getTotalFunds())

    # How much all stocks are worth + cash
    def getTotalValue(self):
        return self.funds + self.portfolio_value

    # P2 functions (deposit, withdraw, getLoan, repayLoan)
    def deposit(self, value):
        if value < 0:
            log.debug("Denying deposit request for negative value {}".format(value))
            return False
        self.funds = self.funds + value
        log.debug("Deposited {} to bank. New bank funds: {}".format(value, self.funds))
        return True
    
    def withdraw(self, value):
        if value < 0:
            log.debug("Denying withdraw request for negative value {}".format(value))
            return False
        if value > self.funds:
            log.debug("Denying withdraw request for value {} because bank has only {}".format(value, self.funds))
            return False
        self.funds = self.funds - value
        log.debug("Withdrew {} from bank. New bank funds: {}".format(value, self.funds))
        return True

    def getLoan(self, value):
        if value < 0:
            log.debug("Denying loan request for negative value {}".format(value))
            return False
        if value > self.funds:
            log.debug("Denying loan request for value {} because bank has only {}".format(value, self.funds))
            return False
        self.funds = self.funds - value
        self.loans = self.loans + value
        log.debug("Lent out {} of funds. New bank loans: {}".format(value, self.loans))
        return True
        
    def repayLoan(self, value):
        if value < 0:
            log.debug("Denying repay request for negative value {}".format(value))
            return False
        self.funds = self.funds + value
        self.loans = self.loans - value
        log.debug("Repayed {} of loan. New bank loans: {}".format(value, self.loans))
        return True

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
    
    def financecheck(self):
        while True:
            time.sleep(FINANCECHECK_INTERVAL)
            if self.funds < INSOLVENCY_THRESHOLD:                                       # If bank is insolvent
                log.warning("Bank is insolvent. Trying to find a helping bank.")        # Print warning                
                if on_funds_low(self) :                                                 # Call on_funds_low function to handle this If bank is still insolvent after handling
                    log.info("Bank is no longer insolvent.")                            # Print warning
                else:
                    log.warning("Bank is insolvent. Could not find a helping bank.")
        
        