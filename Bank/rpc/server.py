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

import grpc
from configuration import GRPC_PORT

from rpc import bank_pb2_grpc
from rpc import bank_pb2


class BankServicer(bank_pb2_grpc.BankServiceServicer):
    def __init__(self, bank):
        self.bank = bank
    def lendMoney(self, request, context):
        log.info("Received request to lend money")
        if self.bank.getLoan(request.amount):
            response = bank_pb2.Response(status="SUCCESS", reason="Money Lended")
        else:
            response = bank_pb2.Response(status="FAILED", reason="Money Not Lended")
        return response
    
    def transferMoney(self, request, context):
        log.info("Received request to transfer money")
        if self.bank.deposit(request.amount):
            response = bank_pb2.Response(status="SUCCESS", reason="Money Sent")
        else:
            response = bank_pb2.Response(status="FAILED", reason="Money Not Sent")
        return response


class GRPCServer:
    def __init__(self, bank):
        self.bank = bank

    def serve(self):
        log.debug("Setting up GRPC Server")
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        bank_pb2_grpc.add_BankServiceServicer_to_server(
            BankServicer(self.bank), server)
        server.add_insecure_port('[::]:'+str(GRPC_PORT))
        server.start()
        log.info("GRPC Server started on port: "+str(GRPC_PORT))
        server.wait_for_termination()
    