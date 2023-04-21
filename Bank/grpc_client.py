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
"""The Python implementation of the gRPC route guide client."""

from __future__ import print_function
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

def get_one_account(stub, account_number):
    account = stub.GetAccount(bank_pb2.AccountRequest(account_number=account_number))
    if not account:
        print("Server returned incomplete account")
        return

    print("Account %d has balance %d" % (account_number, account.balance))

def lendMoney(stub, amount):
    response = stub.lendMoney(bank_pb2.Request(bank="TEST",amount=amount))
    print("Response status: %s" % response.status)
    print("Response message: %s" % response.reason)

def transferMoney(stub, amount):
    response = stub.transferMoney(bank_pb2.Request(bank="TEST",amount=amount))
    print("Response status: %s" % response.status)
    print("Response message: %s" % response.reason)


def run():
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = bank_pb2_grpc.BankServiceStub(channel)
        print("-------------- lendMoney --------------")
        lendMoney(stub, 1000)
        print("-------------- transferMoney --------------")
        transferMoney(stub, 1000)

if __name__ == '__main__':
    log.basicConfig()
    run()