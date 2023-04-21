# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""The Python implementation of the gRPC route guide server."""

from concurrent import futures
import logging as log
import os

import grpc
import bank_pb2
import bank_pb2_grpc

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

class BankServicer(bank_pb2_grpc.BankServiceServicer):
    def __init__(self, bank):
        self.bank = bank
    def lendMoney(self, request, context):
        if self.bank.getLoan(request.amount):
            response = bank_pb2.Response(status="SUCCESS", reason="Money Lended")
        else:
            response = bank_pb2.Response(status="FAILED", reason="Money Not Lended")
        return response
    
    def transferMoney(self, request, context):
        if self.bank.withdraw(request.amount):
            response = bank_pb2.Response(status="SUCCESS", reason="Money Sent")
        else:
            response = bank_pb2.Response(status="FAILED", reason="Money Not Sent")
        return response


def serveGRPC(bank):
    log.debug("Setting up GRPC Server")
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    bank_pb2_grpc.add_BankServiceServicer_to_server(
        BankServicer(bank), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    log.info("GRPC Server started")
    server.wait_for_termination()

if __name__ == '__main__':
    from bank import Bank
    bank = Bank({},{},100000,0)
    serveGRPC(bank)