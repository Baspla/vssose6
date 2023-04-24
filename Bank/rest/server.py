import json
import logging as log
import os
import socket
import threading
import time

from rpc.client import on_funds_low, test_transferMoney

def construct_http_response(status_code, content_type, body):
    response = f"HTTP/1.1 {status_code}\nContent-Type: {content_type}\n\n{body}"
    return response.encode()


def construct_http_response_json(status_code, body):
    return construct_http_response(status_code, "application/json", json.dumps(body))

# Kunden

# GET /kundenportal

# POST /api/deposit  geldpool++
# POST /api/withdraw geldpool--
# POST /api/getLoan  ausstehendeKredite++ geldpool--
# POST /api/repayLoan ausstehendeKredite-- geldpool++

# Bankmitarbeiter

# GET /mitarbeiterportal

# POST /api/buyStock
# POST /api/sellStock
# GET /api/portfolio

# Beispiel HTTP Request
# POST /api/withdraw
# {"kunde": 1, "betrag": 1000}


class HTTPServer:
    def __init__(self, bank):
        self.bank = bank
        self.host = ''
        self.port = int(os.environ.get("PORT", 12340))
        self.backlog = 5
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Makes sure that the port is available again after the server is shut down
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(self.backlog)

        print(f'Server läuft auf http://{self.host}:{self.port}/')

    def handle_client_request(self, client_socket):
        request = client_socket.recv(1024)
        try:
            start_time = time.time()
            response = self.handle_request(request)
            log.debug("Request took "+ str(time.time() - start_time) + " seconds to process")
        except Exception as e:
            log.error(e)
            response = construct_http_response(500, "text/plain", "Internal Server Error")
        client_socket.sendall(response)
        client_socket.close()

    def start(self):
        while True:
            client_socket, address = self.server_socket.accept()
            t = threading.Thread(target=self.handle_client_request, args=(client_socket,))
            t.start()

    def handle_get_request(self, request_path):
        if request_path == "/kundenportal":
            with open("static/kundenportal.html", "r") as f:
                htmlData = f.read()
            return construct_http_response(200, "text/html", htmlData)

        elif request_path == "/mitarbeiterportal":
            with open("static/mitarbeiterportal.html", "r") as f:
                htmlData = f.read()
            return construct_http_response(200, "text/html", htmlData)

        elif request_path == "/api/totalValue":  # Combined value of all funds and stocks
            data = {"totalValue": self.bank.getTotalValue()}
            return construct_http_response_json(200, data)

        elif request_path == "/api/totalFunds":  # Cash in the bank
            data = {"totalFunds": self.bank.getTotalFunds()}
            return construct_http_response_json(200, data)

        elif request_path == "/api/totalLoans":  # Total amount of loaned money
            data = {"totalLoans": self.bank.getTotalLoans()}
            return construct_http_response_json(200, data)

        elif request_path == "/api/totalPortfolio":  # Total value of all stocks
            data = {"totalPortfolio": self.bank.getPortfolioValue()}
            return construct_http_response_json(200, data)
        elif request_path == "/api/stockList":
            data = self.bank.getStockList()
            return construct_http_response_json(200, data)
        elif request_path == "/trigger/transferMoney": # Function for testing the gRPC client
            log.debug("Triggered gRPC transferMoney function")
            data = {"success":test_transferMoney(self.bank)}
            return construct_http_response_json(200, data)
        elif request_path == "/trigger/fundsLow": # Function for testing the gRPC client
            log.debug("Triggered on_funds_low")
            data = {"success": on_funds_low(self.bank)}
            return construct_http_response_json(200, data)
        else:
            return construct_http_response(404, "text/html", "Not Found")

    def handle_post_request(self, request_path, request_lines):
        request_json = json.loads(request_lines[-1])
        if request_path == "/api/deposit":
            if "amount" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            try:
                amount = float(request_json["amount"])
            except ValueError:
                return construct_http_response(400, "text/html", "Bad Request")
            if amount < 1:
                return construct_http_response(400, "text/html", "Bad Request")
            self.bank.deposit(amount)
            data = {}
            return construct_http_response_json(200, data)

        elif request_path == "/api/withdraw":
            if "amount" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            try:
                amount = float(request_json["amount"])
            except ValueError:
                return construct_http_response(400, "text/html", "Bad Request")
            if amount < 1:
                return construct_http_response(400, "text/html", "Bad Request")
            self.bank.withdraw(amount)
            data = {}
            return construct_http_response_json(200, data)

        elif request_path == "/api/getLoan":
            if "amount" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            try:
                amount = float(request_json["amount"])
            except ValueError:
                return construct_http_response(400, "text/html", "Bad Request")
            if amount < 1:
                return construct_http_response(400, "text/html", "Bad Request")
            self.bank.getLoan(amount)
            data = {}
            return construct_http_response_json(200, data)

        elif request_path == "/api/repayLoan":
            if "amount" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            try:
                amount = float(request_json["amount"])
            except ValueError:
                return construct_http_response(400, "text/html", "Bad Request")
            if amount < 1:
                return construct_http_response(400, "text/html", "Bad Request")
            self.bank.repayLoan(amount)
            data = {}
            return construct_http_response_json(200, data)

        elif request_path == "/api/buyStock":
            if "amount" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            if "name" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            try:
                amount = float(request_json["amount"])
            except ValueError:
                return construct_http_response(400, "text/html", "Bad Request")
            if amount < 1:
                return construct_http_response(400, "text/html", "Bad Request")
            name = request_json["name"]
            if name == "":
                return construct_http_response(400, "text/html", "Bad Request")
            self.bank.buyStock(name, amount)
            data = {"message": "Bought " + str(amount) + " stocks for " + str(self.bank.getStockValue(name)) + " each"}
            return construct_http_response_json(200, data)

        elif request_path == "/api/sellStock":
            if "amount" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            if "name" not in request_json:
                return construct_http_response(400, "text/html", "Bad Request")
            try:
                amount = float(request_json["amount"])
            except ValueError:
                return construct_http_response(400, "text/html", "Bad Request")
            if amount < 1:
                return construct_http_response(400, "text/html", "Bad Request")
            name = request_json["name"]
            if name == "":
                return construct_http_response(400, "text/html", "Bad Request")
            if self.bank.sellStock(name, amount):
                value = self.bank.getStockValue(name)
                data = {"message": "Sold " + str(amount) + " stocks for " + str(value) + " each"}
                return construct_http_response_json(200, data)
            else:
                data = {"message": "Not enough stocks"}
                return construct_http_response_json(400, data)
        else:
            return construct_http_response(404, "text/html", "Not Found")

    def handle_request(self, request):
        request = request.decode()
        request_lines = request.splitlines()
        request_line = request_lines[0]
        request_method = request_line.split()[0]
        request_path = request_line.split()[1]
        log.debug(f"Request: {request_method} {request_path}")
        if request_method == "GET":
            return self.handle_get_request(request_path)
        elif request_method == "POST":
            return self.handle_post_request(request_path, request_lines)
        else:
            return construct_http_response(400, "text/html", "Bad Request")
