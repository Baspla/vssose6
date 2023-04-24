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
import math
import statistics
import time

import grpc
from constants import GRPC_MEASUREMENTS, INSOLVENCY_LENDING_AMOUNT, SERVER_ID
from lookup.lookup import load_bank_server

from rpc import bank_pb2
from rpc import bank_pb2_grpc

measurements = [0.0] * GRPC_MEASUREMENTS
n_measurements = 0

def lendMoney(stub,bank, amount):
    global n_measurements
    global measurements
    timestamp = time.time()
    response = stub.lendMoney(bank_pb2.Request(bank=bank,amount=amount))
    log.debug(f"Time measurement for lendMoney: {time.time()-timestamp}")
    measurements[n_measurements] = (time.time() - float(timestamp)) * 1000
    n_measurements += 1
    check_measurements()
    log.debug("Response status: %s" % response.status)
    log.debug("Response message: %s" % response.reason)
    return response

def transferMoney(stub,bank, amount):
    timestamp = time.time()
    response = stub.transferMoney(bank_pb2.Request(bank=bank,amount=amount))
    log.debug(f"Time measurement for transferMoney: {time.time()-timestamp}")
    log.debug("Response status: %s" % response.status)
    log.debug("Response message: %s" % response.reason)
    return response

def check_measurements():
    global n_measurements
    if n_measurements >= GRPC_MEASUREMENTS:
        n_measurements = 0
        log.debug("Average round trip time: {}".format(sum(measurements) / len(measurements)))
        min_rtt = min(measurements)
        max_rtt = max(measurements)
        log.debug("Min round trip time: {} ms".format(min_rtt))
        log.debug("Max round trip time: {} ms".format(max_rtt))
        log.debug("Standard deviation: {}".format(math.sqrt(sum((x - min_rtt) ** 2 for x in measurements) / len(measurements))))
        log.debug("Median: {} ms".format(statistics.median(measurements)))


def on_funds_low(bank):
    servers = load_bank_server() # Look up all available banks
    success = False
    amount = INSOLVENCY_LENDING_AMOUNT
    for serverid in servers: # Go through all banks and check if they are willing to lend money
        if serverid == SERVER_ID:
            log.debug("Skipping own bank at: "+str(servers[serverid]["ip"])+":"+str(servers[serverid]["port"])+"...")
            continue
        log.info(f"Trying to borrow money from bank: {servers[serverid]['ip']}:{str(servers[serverid]['port'])}") 
        try:
            with grpc.insecure_channel(servers[serverid]["ip"]+":"+str(servers[serverid]["port"])) as channel:
                stub = bank_pb2_grpc.BankServiceStub(channel)
                response = lendMoney(stub=stub,bank=SERVER_ID,amount=amount)
                if response.status == "SUCCESS":
                    success = True
                    bank.deposit(amount)
                    break
        except Exception as e:
            log.error(f"Error: {e}")
    if success:
        log.info("Successfully borrowed money from another bank.")
    else:
        log.info("Failed to borrow money from another bank.")
    return success

def test_transferMoney(bank):
    servers = load_bank_server() # Look up all available banks
    success = False
    amount = 10
    for serverid in servers: # Go through all banks and check if they are willing to lend money
        if serverid == SERVER_ID:
            log.debug("Skipping own bank at: "+str(servers[serverid]["ip"])+":"+str(servers[serverid]["port"])+"...")
            continue
        log.info(f"Trying to send money to: {servers[serverid]['ip']}:{str(servers[serverid]['port'])}") 
        try:
            with grpc.insecure_channel(servers[serverid]["ip"]+":"+str(servers[serverid]["port"])) as channel:
                stub = bank_pb2_grpc.BankServiceStub(channel)
                response = transferMoney(stub=stub,bank=SERVER_ID,amount=amount)
                log.debug(f"Response status: {response.status}")
                log.debug(f"Response message: {response.reason}")
                if response.status == "SUCCESS":
                    success = True
                    bank.withdraw(amount) # This will fail if the bank is insolvent but this is just for testing the gRPC
                    break
        except Exception as e:
            log.error(f"Error: {e}")
    if success:
        log.info("Successfully sent money to another bank.")
    else:
        log.info("Failed to send money to another bank.")
    return success